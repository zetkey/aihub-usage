#!/usr/bin/env python3
"""Test suite untuk aihub-usage.

Menjalankan CLI terhadap mock gateway (mock_gateway.py) yang meniru response asli
new-api, lalu memeriksa output/exit code. Tidak memakai credit asli.

  python3 test_aihub_usage.py            # jalankan semua
  AIHUB_CLI=/path/aihub-usage python3 test_aihub_usage.py
"""
import json
import os
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MOCK = os.path.join(HERE, "mock_gateway.py")


def _default_cli():
    """Pakai script di repo ini kalau ada, supaya tes bisa jalan sebelum install."""
    local = os.path.join(HERE, "aihub-usage")
    if os.path.isfile(local):
        return local
    return os.path.expanduser("~/.local/bin/aihub-usage")


CLI = os.environ.get("AIHUB_CLI", _default_cli())
KEY = "sk-testkey123"
# config yang tidak pernah dibuat -> tes tidak terpengaruh ~/.config/aihub/config.json asli
ISOLATED_CONFIG = os.path.join(HERE, ".test_no_config.json")


def clean_env(**overrides):
    env = {k: v for k, v in os.environ.items()
           if k not in ("AIHUB_API_KEY", "AIHUB_BASE_URL", "AIHUB_CONFIG")}
    env["AIHUB_CONFIG"] = ISOLATED_CONFIG
    env.update(overrides)
    return env

results = []


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_mock(port, limited=False, errlog=False, empty_choices=False,
               empty_logs=False):
    args = [sys.executable, MOCK, str(port)]
    if limited:
        args.append("--limited")
    if errlog:
        args.append("--errlog")
    if empty_choices:
        args.append("--emptychoices")
    if empty_logs:
        args.append("--emptylogs")
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/api/status" % port, timeout=1).read()
            return proc
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("mock gagal start di port %d" % port)


def run(base, *args):
    cmd = [sys.executable, CLI, "--base-url", base, "--key", KEY] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr

def run_env(base, env, *args):
    """Jalankan CLI dengan env khusus (mis. tanpa key sama sekali)."""
    cmd = [sys.executable, CLI, "--base-url", base] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    return p.returncode, p.stdout, p.stderr


def run_badkey(base, *args):
    cmd = [sys.executable, CLI, "--base-url", base, "--key", "sk-wrong"] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def case(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "   <- " + str(detail)[:200]))


def main():
    p1, p2, p3, p4, p5 = (free_port(), free_port(), free_port(), free_port(),
                          free_port())
    m1 = start_mock(p1)
    m2 = start_mock(p2, limited=True)
    m3 = start_mock(p3, errlog=True)
    m4 = start_mock(p4, empty_choices=True)
    m5 = start_mock(p5, empty_logs=True)
    b1 = "http://127.0.0.1:%d" % p1
    b2 = "http://127.0.0.1:%d" % p2
    b3 = "http://127.0.0.1:%d" % p3
    b4 = "http://127.0.0.1:%d" % p4
    b5 = "http://127.0.0.1:%d" % p5
    try:
        # --- status (endpoint publik) -------------------------------------
        rc, out, err = run(b1, "status")
        case("status: quota_per_unit tampil bulat 500,000",
             rc == 0 and "500,000 quota = $1" in out, out[-200:])
        case("status: nama gateway terbaca", "metranet AI" in out, out[-200:])
        case("status: kurs IDR terbaca", "IDR=18000" in out, out[-200:])

        # --- all: balance + key -------------------------------------------
        rc, out, err = run(b1, "all")
        case("all: exit 0", rc == 0, rc)
        case("all: sisa credit = total - terpakai (11.11)",
             "SISA CREDIT   : $11.11" in out, out)
        case("all: konversi rupiah gaya Indonesia",
             "Rp 200.000" in out, out)
        case("all: total credit $12.35", "total credit  : $12.35" in out, out)
        case("all: terpakai $1.23 (cent dibagi 100)",
             "terpakai      : $1.23" in out, out)
        case("all: nama key terbaca", "prod-hermes" in out, out)
        case("all: key unlimited dikenali",
             "limit key     : unlimited (ikut saldo akun)" in out, out)
        case("all: masa aktif tidak dibatasi",
             "masa aktif    : tidak dibatasi" in out, out)
        case("all: terpakai key + nilai quota mentah",
             "terpakai key  : $1.23  (617,250 quota)" in out, out)
        case("all: key unlimited dijelaskan (0 bukan saldo kosong)",
             "key unlimited" in out and "SISA CREDIT" in out, out)

        # --- key terbatas --------------------------------------------------
        rc, out, err = run(b2, "key")
        case("key terbatas: limit key $5.00", "limit key     : $5.00" in out, out)
        case("key terbatas: sisa kuota key $3.00",
             "sisa kuota key: $3.00" in out, out)
        batas_line = [l.strip() for l in out.splitlines() if l.strip().startswith("batas model")]
        case("key terbatas: batas model ditampilkan",
             len(batas_line) == 1 and "gpt-5.5" in batas_line[0], out)
        case("key terbatas: kuota mentah sebagai konteks dolar",
             "limit key     : $5.00  (2,500,000 quota)" in out
             and "terpakai key  : $2.00  (1,000,000 quota)" in out
             and "sisa kuota key: $3.00  (1,500,000 quota)" in out, out)
        case("key terbatas: tanpa dump kolom mentah",
             "total_granted" not in out and "raw /api" not in out, out)

        # --- logs ----------------------------------------------------------
        rc, out, err = run(b1, "logs", "-n", "5")
        case("logs: baris pemakaian model tampil", "gpt-5.5" in out, out)
        # mock mengirim type=5 (error) lebih dulu lalu type=6 (refund) terakhir;
        # label harus ikut barisnya, bukan tertukar.
        rows = [l for l in out.splitlines() if l.strip()[:1].isdigit()]
        case("logs: tipe 5 = error, tipe 6 = refund (tidak tertukar)",
             len(rows) == 4 and "error" in rows[0] and "refund" in rows[-1], out)
        case("logs: header pakai satuan token",
             "token_in" in out and "token_out" in out, out)
        case("logs: biaya per request dihitung",
             "$0.0250" in out and "$0.0100" in out, out)

        # --- ringkasan token ------------------------------------------------
        rc, out, err = run(b1, "all")
        case("all: ada bagian PEMAKAIAN TOKEN", "PEMAKAIAN TOKEN" in out, out)
        case("all: total token = masuk + keluar (2,440)",
             "TOTAL TOKEN   : 2,440" in out, out)
        case("all: token masuk 2,000 / keluar 440",
             "token masuk   : 2,000" in out and "token keluar  : 440" in out, out)
        case("all: baris error/refund tidak dihitung sebagai request",
             "request       : 2" in out, out)
        case("all: hanya tabel log yang tidak ikut (bagian LOG absen)",
             "LOG TERAKHIR" not in out, out)

        rc, out, err = run(b1, "tokens")
        case("tokens: ringkasan + rincian per model",
             rc == 0 and "PER MODEL" in out and "gpt-5.5" in out
             and "deepseek-v4.1-flash" in out, out)
        case("tokens: biaya per model dari quota",
             "$0.0250" in out and "$0.0100" in out, out)
        case("tokens: rata-rata token per request",
             "1,220 token/request" in out, out)
        case("tokens: kuota terpakai ditampilkan informatif",
             "kuota terpakai: 617,250 quota = $1.23" in out, out)
        case("tokens: blok API KEY INI tidak diulang",
             "API KEY INI" not in out and "raw /api" not in out, out)

        rc, out, err = run(b1, "tokens", "--json")
        try:
            d = json.loads(out)
            t = d["tokens"]
            ok = (rc == 0 and t["requests"] == 2 and t["total_tokens"] == 2440
                  and t["prompt_tokens"] == 2000 and t["completion_tokens"] == 440
                  and abs(t["cost_usd"] - 0.035) < 1e-9
                  and [m["model"] for m in t["by_model"]] == ["gpt-5.5",
                                                              "deepseek-v4.1-flash"]
                  and d["token"]["total_used"] == 617250
                  and "logs" not in d)
        except Exception as e:
            ok, d = False, str(e)
        case("tokens --json: struktur token + by_model urut biaya", ok,
             d if not ok else "")

        rc, out, err = run(b5, "tokens")
        case("tokens tanpa log pemakaian: pesan jelas, exit 0",
             rc == 0 and "belum ada log pemakaian" in out, out)

        rc, out, err = run(b3, "tokens")
        case("tokens gagal (success:false): exit 1 + pesan gateway",
             rc == 1 and "gagal" in err and "Traceback" not in err,
             "%s / %s" % (rc, err.strip()[-200:]))

        rc, out, err = run(b1, "logs", "-n", "0")
        case("logs: -n 0 tidak mencetak baris log, ringkasan tetap ada",
             rc == 0 and "gpt-5.5" not in out and "TOTAL TOKEN" in out, out)
        rc, out, err = run(b1, "logs", "-n", "-1")
        case("logs: -n negatif ditolak argparse (exit 2)",
             rc == 2 and "negatif" in err, "%s / %s" % (rc, err.strip()))

        # --- stdout ditutup lebih awal (mis. `aihub-usage tokens | head`) ----
        pipe = " ".join(shlex.quote(x) for x in
                        [sys.executable, CLI, "--base-url", b1, "--key", KEY,
                         "tokens"]) + " | head -3"
        p = subprocess.run(pipe, shell=True, capture_output=True, text=True,
                           timeout=60)
        case("output dipotong `head`: bersih, tanpa traceback BrokenPipe",
             "Traceback" not in p.stderr and "BrokenPipe" not in p.stderr,
             p.stderr.strip()[-200:])

        # --- models --------------------------------------------------------
        rc, out, err = run(b1, "models")
        case("models: jumlah model benar (2, id kosong difilter)",
             "2 model" in out, out)
        case("models: id kosong tidak muncul",
             "gpt-5.5, deepseek-v4.1-flash" in out, out)

        # --- probe ---------------------------------------------------------
        rc, out, err = run(b1, "probe", "--model", "gpt-5.5")
        case("probe openai: exit 0 + token usage",
             rc == 0 and "prompt : 3 token" in out and "output : 1 token" in out, out)
        rc, out, err = run(b1, "probe", "--model", "gpt-5.5", "--anthropic")
        case("probe anthropic: lewat /v1/messages",
             rc == 0 and "input  : 3 token" in out, out)

        rc, out, err = run(b1, "probe", "--model", "gpt-5.5", "--json")
        try:
            d = json.loads(out)
            ok = (rc == 0 and d["endpoint"] == "/v1/chat/completions"
                  and d["prompt_tokens"] == 3 and d["content"] == "hi")
        except Exception as e:
            ok, d = False, str(e)
        case("probe --json: JSON valid, bukan teks", ok, d if not ok else "")

        rc, out, err = run(b4, "probe", "--model", "gpt-5.5")
        case("probe tanpa choices: tidak crash (exit 0)",
             rc == 0 and "jawab" in out, "%s / %s" % (rc, err.strip()[-200:]))

        rc, out, err = run(b1, "probe", "--max-tokens", "0")
        case("probe --max-tokens 0 ditolak argparse (exit 2)",
             rc == 2 and "harus >= 1" in err, "%s / %s" % (rc, err.strip()))

        # --- json ----------------------------------------------------------
        rc, out, err = run(b1, "--json")
        try:
            d = json.loads(out)
            ok = (rc == 0
                  and abs(d["balance"]["remaining_usd"] - 11.1111) < 0.001
                  and d["status"]["quota_per_unit"] == 500000
                  and d["token"]["name"] == "prod-hermes")
        except Exception as e:
            ok, d = False, str(e)
        case("json: struktur + angka balance akurat", ok, d if not ok else "")

        # --- exit codes ----------------------------------------------------
        rc, out, err = run(b1, "balance", "--warn-below", "20")
        case("warn-below: sisa < batas -> exit 3 + pesan",
             rc == 3 and "DI BAWAH BATAS" in err, "%s / %s" % (rc, err.strip()))
        rc, out, err = run(b1, "balance", "--warn-below", "5")
        case("warn-below: sisa aman -> exit 0", rc == 0, rc)

        rc, out, err = run(b1, "key", "--warn-below", "20")
        case("warn-below pada `key`: tetap exit 3, tanpa traceback",
             rc == 3 and "Traceback" not in err and "DI BAWAH BATAS" in err,
             "%s / %s" % (rc, err.strip()))
        rc, out, err = run(b1, "logs", "--warn-below", "5")
        case("warn-below pada `logs`: saldo aman -> exit 0, tanpa traceback",
             rc == 0 and "Traceback" not in err, "%s / %s" % (rc, err.strip()))

        # --- error envelope HTTP 200 + success:false ------------------------
        rc, out, err = run(b3, "logs")
        case("log gagal (success:false): exit 1 + pesan gateway",
             rc == 1 and "gagal" in err and "Traceback" not in err,
             "%s / %s" % (rc, err.strip()[-200:]))
        rc, out, err = run(b3, "logs", "--json")
        try:
            d = json.loads(out)
            ok = rc == 1 and "logs_error" in d and "Traceback" not in err
        except Exception as e:
            ok, d = False, str(e)
        case("logs gagal + --json: JSON tetap valid, exit 1", ok, d if not ok else "")

        rc, out, err = run(b1, "usage")
        case("command `usage` tidak lagi diterima (exit 2)",
             rc == 2, rc)

        rc, out, err = run_badkey(b1, "balance")
        case("key salah: exit 1 + pesan rapi",
             rc == 1 and "401" in err, "%s / %s" % (rc, err.strip()))

        p = subprocess.run([sys.executable, CLI, "--base-url", "bukan-url", "status"],
                           capture_output=True, text=True, timeout=60,
                           env=clean_env())
        case("base URL tanpa skema: pesan rapi, tanpa traceback",
             p.returncode == 1 and "tidak valid" in p.stderr
             and "Traceback" not in p.stderr, p.stderr.strip()[-200:])

        # --- config / key resolution ---------------------------------------
        rc, out, err = subprocess.run(
            [sys.executable, CLI, "status", "--key", "sk-x",
             "--base-url", b1], capture_output=True, text=True).returncode, "", ""
        case("--key + --base-url diterima", rc == 0, rc)

        env = clean_env(AIHUB_API_KEY=KEY, AIHUB_BASE_URL=b1)
        p = subprocess.run([sys.executable, CLI, "balance"],
                           capture_output=True, text=True, env=env, timeout=60)
        case("env AIHUB_API_KEY / AIHUB_BASE_URL dipakai",
             p.returncode == 0 and "SISA CREDIT" in p.stdout, p.stdout[-200:])

        p = subprocess.run([sys.executable, CLI, "balance"], capture_output=True,
                           text=True, timeout=60,
                           env=clean_env())
        case("tanpa key: error jelas + exit 1",
             p.returncode == 1 and "API key belum ada" in p.stderr, p.stderr[:200])

        # --- status publik & --key-file ------------------------------------
        p = subprocess.run([sys.executable, CLI, "--base-url", b1, "status"],
                           capture_output=True, text=True, timeout=60,
                           env=clean_env())
        case("status tanpa key: tetap jalan (endpoint publik)",
             p.returncode == 0 and "quota = $1" in p.stdout, p.stdout[-150:])

        kf = os.path.join(HERE, ".test_key_file")
        with open(kf, "w") as f:
            f.write("# komentar diabaikan\n" + KEY + "\n")
        try:
            p = subprocess.run([sys.executable, CLI, "--key-file", kf,
                                "--base-url", b1, "balance"],
                               capture_output=True, text=True, timeout=60)
            case("--key-file: baris pertama (komentar dilewati) dipakai",
                 p.returncode == 0 and "SISA CREDIT" in p.stdout, p.stdout[-150:])
        finally:
            os.remove(kf)

        # --- save-key -> config dipakai lagi tanpa --key --------------------
        cfg = os.path.join(HERE, ".test_config.json")
        if os.path.exists(cfg):
            os.remove(cfg)
        try:
            p = subprocess.run([sys.executable, CLI, "--key", KEY,
                                "--base-url", b1, "save-key"],
                               capture_output=True, text=True, timeout=60,
                               env=clean_env(AIHUB_CONFIG=cfg))
            saved = p.returncode == 0 and os.path.exists(cfg)
            mode = oct(stat.S_IMODE(os.stat(cfg).st_mode)) if saved else "?"
            case("save-key: file config dibuat mode 0600",
                 saved and mode == "0o600", "%s / %s" % (p.stdout.strip(), mode))

            p = subprocess.run([sys.executable, CLI, "balance"],
                               capture_output=True, text=True, timeout=60,
                               env=clean_env(AIHUB_CONFIG=cfg))
            case("config tersimpan: dipakai otomatis tanpa --key",
                 p.returncode == 0 and "SISA CREDIT" in p.stdout, p.stdout[-150:])
        finally:
            if os.path.exists(cfg):
                os.remove(cfg)

        # --- save-key ke direktori yang belum ada ---------------------------
        nested = os.path.join(HERE, ".test_nested", "deep", "config.json")
        try:
            p = subprocess.run([sys.executable, CLI, "--key", KEY,
                                "--base-url", b1, "save-key"],
                               capture_output=True, text=True, timeout=60,
                               env=clean_env(AIHUB_CONFIG=nested))
            mode = (oct(stat.S_IMODE(os.stat(nested).st_mode))
                    if os.path.exists(nested) else "?")
            case("save-key: direktori induk dibuat otomatis, mode 0600",
                 p.returncode == 0 and mode == "0o600",
                 "%s / %s" % (p.stderr.strip()[-150:], mode))
        finally:
            shutil.rmtree(os.path.join(HERE, ".test_nested"), ignore_errors=True)
    finally:
        for m in (m1, m2, m3, m4, m5):
            m.kill()

    failed = [r for r in results if not r[1]]
    print("\n%d/%d PASS" % (len(results) - len(failed), len(results)))
    if failed:
        print("GAGAL: " + ", ".join(r[0] for r in failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
