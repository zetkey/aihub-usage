#!/usr/bin/env python3
"""Test suite untuk aihub-usage.

Menjalankan CLI terhadap mock gateway (mock_gateway.py) yang meniru response asli
new-api, lalu memeriksa output/exit code. Tidak memakai credit asli.

  python3 test_aihub_usage.py            # jalankan semua
  AIHUB_CLI=/path/aihub-usage python3 test_aihub_usage.py
"""
import json
import os
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


def start_mock(port, limited=False):
    args = [sys.executable, MOCK, str(port)] + (["--limited"] if limited else [])
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


def run_badkey(base, *args):
    cmd = [sys.executable, CLI, "--base-url", base, "--key", "sk-wrong"] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def case(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "   <- " + str(detail)[:200]))


def main():
    p1, p2 = free_port(), free_port()
    m1 = start_mock(p1)
    m2 = start_mock(p2, limited=True)
    b1 = "http://127.0.0.1:%d" % p1
    b2 = "http://127.0.0.1:%d" % p2
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

        # --- key terbatas --------------------------------------------------
        rc, out, err = run(b2, "key")
        case("key terbatas: limit key $5.00", "limit key     : $5.00" in out, out)
        case("key terbatas: sisa kuota key $3.00",
             "sisa kuota key: $3.00" in out, out)
        batas_line = [l.strip() for l in out.splitlines() if l.strip().startswith("batas model")]
        case("key terbatas: batas model ditampilkan",
             len(batas_line) == 1 and "gpt-5.5" in batas_line[0], out)

        # --- logs ----------------------------------------------------------
        rc, out, err = run(b1, "logs", "-n", "5")
        case("logs: baris pemakaian model tampil", "gpt-5.5" in out, out)
        case("logs: tipe error diberi label", "error" in out, out)
        case("logs: biaya per request dihitung",
             "$0.0250" in out, out)

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

        rc, out, err = run_badkey(b1, "balance")
        case("key salah: exit 1 + pesan rapi",
             rc == 1 and "401" in err, "%s / %s" % (rc, err.strip()))

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
    finally:
        m1.kill()
        m2.kill()

    failed = [r for r in results if not r[1]]
    print("\n%d/%d PASS" % (len(results) - len(failed), len(results)))
    if failed:
        print("GAGAL: " + ", ".join(r[0] for r in failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
