# aihub-usage

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](#persyaratan)
[![Tests](https://img.shields.io/badge/tests-101%20passed-brightgreen)](docs/pengembangan.md)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](#persyaratan)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

CLI untuk melihat **sisa credit (saldo), pemakaian token, dan log request** dari
API key pada gateway [Scala AI Gateway by Metranet](https://aihub.metranet.co.id).

Gateway tersebut dibangun di atas [new-api](https://github.com/QuantumNous/new-api),
sehingga seluruh data diambil dari endpoint resminya — **tanpa scraping HTML** dan
tanpa menyimpan password akun. Satu file Python, tanpa dependensi eksternal.

```console
$ aihub-usage

Scala AI Gateway — metranet AI
  base URL      : https://aihub.metranet.co.id
  versi gateway : 2576fe9
  satuan        : 500,000 quota = $1
  kurs          : CNY=7, IDR=18000, USD=1

CREDIT AKUN
  total credit  : $12.35
  terpakai      : $1.23
  SISA CREDIT   : $11.11  (Rp 200.000)
  masa aktif    : tidak dibatasi

API KEY INI
  nama          : prod-hermes
  limit key     : unlimited (ikut saldo akun)
  terpakai key  : $1.23  (617,250 quota)
  sisa kuota key: unlimited
  kadaluarsa    : tidak ada
  batas model   : semua model
  catatan       : key unlimited — gateway melaporkan total_granted & total_available = 0; patokan saldo ada di baris SISA CREDIT.

PEMAKAIAN TOKEN
  dasar hitung  : 4 log terakhir (2026-10-08 17:18 s/d 2026-10-08 18:20)
  mode          : API SAJA — arsip lokal tidak aktif, token hanya dihitung dari jendela log yang dikirim gateway
  request       : 2
  token masuk   : 2,000
  token keluar  : 440
  TOTAL TOKEN   : 2,440
  rata-rata     : 1,220 token/request
  biaya jendela : $0.0350  (Rp 630)
  biaya 1jt tok : $14.34
  catatan       : hanya log yang dikirim gateway (new-api membatasi daftar log per key), bukan total seumur hidup key.
```

Angka dolar selalu disertai nilai **quota** aslinya dalam tanda kurung, jadi bisa
langsung dicocokkan dengan response gateway. `aihub-usage tokens` menambah rincian
per model:

```console
$ aihub-usage tokens

PEMAKAIAN TOKEN
  ...
  PER MODEL
  model                           req        masuk       keluar        total      biaya
  gpt-5.5                           1        1,200          340        1,540    $0.0250
  deepseek-v4.1-flash               1          800          100          900    $0.0100
```

## Fitur

- **Sisa credit akun** — total credit, terpakai, dan sisa (USD + estimasi Rupiah).
- **Kuota per API key** — status unlimited, batas, kadaluarsa, batas model, plus
  nilai **quota** asli di samping setiap angka dolar.
- **Pemakaian token** — token masuk/keluar/total, rata-rata per request, biaya per
  juta token, dan rincian per model (`tokens`).
- **Log request** — waktu, model, token masuk/keluar, biaya, dan durasi.
- **Daftar model** — model yang bisa dipakai oleh key tersebut.
- **Probe** — kirim satu request kecil untuk memastikan key benar-benar jalan.
- **Mode JSON & exit code** — siap dipakai di script, cron, atau monitoring.
- **Arsip log lokal (opsional, default OFF)** — mengakumulasi log antar-run agar
  perhitungan token melampaui batas 1000 log terakhir milik gateway.
- **Cepat** — semua endpoint diambil paralel dan respons diterima dalam gzip.
- **Tanpa dependensi** — hanya stdlib Python 3.8+.
- **Key tidak pernah bocor** — key hanya tampil sebagai nama, tidak pernah di-print.

## Persyaratan

- Python **3.8+** (`python3` sudah ada di macOS, Linux, dan Windows modern).
- Satu API key `sk-...` dari gateway.

Tidak ada `pip install`, tidak ada virtualenv, tidak ada library pihak ketiga.

## Instalasi

```bash
git clone https://github.com/zetkey/aihub-usage.git
cd aihub-usage
./install.sh
```

`install.sh` membuat symlink `~/.local/bin/aihub-usage` → file di repo, jadi
`git pull` sudah cukup untuk memakai versi terbaru. Script ini **tidak** menyentuh
file konfigurasi shell Anda; kalau `~/.local/bin` belum ada di PATH, ia hanya
menampilkan perintah yang perlu Anda tambahkan sendiri.

```bash
BIN_DIR=~/bin ./install.sh    # pasang symlink di folder lain
./install.sh --uninstall      # hapus symlink
```

Simpan API key, lalu jalankan:

```bash
aihub-usage --key sk-xxxxxxxx save-key
aihub-usage
```

## Penggunaan

```
aihub-usage [command] [options]
```

| Command | Keterangan |
|---|---|
| `all` *(default)* | Status gateway + credit akun + info API key + ringkasan token |
| `balance` | Hanya sisa credit akun |
| `key` | Hanya kuota dan pemakaian API key ini |
| `logs` | Log request terakhir lewat key ini (`-n` untuk jumlah baris) |
| `tokens` | Pemakaian dalam satuan token + rincian per model |
| `models` | Daftar model yang bisa dipakai key ini |
| `status` | Info gateway: versi, kurs, satuan quota (tanpa API key) |
| `probe` | Kirim 1 request kecil untuk menguji key |
| `save-key` | Simpan API key ke file config |
| `store [on\|off\|status]` | Aktifkan/nonaktifkan arsip log lokal (tanpa perlu API key) |

| Opsi | Keterangan |
|---|---|
| `--key sk-...` | API key untuk sekali pakai |
| `--key-file PATH` | Baca API key dari baris pertama file |
| `--base-url URL` | Override base URL (default `https://aihub.metranet.co.id`) |
| `--json` | Output JSON untuk diproses script |
| `-n, --limit N` | Jumlah log yang ditampilkan (default `10`; `0` = tanpa baris) |
| `--warn-below USD` | Keluar dengan exit code `3` bila sisa credit di bawah nilai ini (saldo akun ikut diambil walau command-nya bukan `balance`) |
| `--model NAMA` | Model untuk `probe` |
| `--max-tokens N` | `max_tokens` saat `probe` (default `1`, minimal `1`) |
| `--store` / `--no-store` | Paksa arsip lokal aktif / nonaktif untuk run ini |
| `--anthropic` | `probe` lewat `/v1/messages` (protokol Anthropic) |

Contoh:

```bash
aihub-usage                        # ringkasan lengkap
aihub-usage balance                # cek saldo saja
aihub-usage tokens                 # pemakaian token + rincian per model
aihub-usage logs -n 20             # 20 request terakhir
aihub-usage status                 # info gateway (tidak butuh API key)
aihub-usage probe --anthropic      # tes key lewat /v1/messages
aihub-usage key --warn-below 5     # cek kuota key + peringatan saldo
```

> [!TIP]
> `probe` benar-benar memanggil model dan **memakai credit**. `--max-tokens`
> default `1` supaya biayanya sekecil mungkin.

## Konfigurasi

API key dicari berurutan, berhenti di yang pertama ditemukan:

1. `--key sk-...`
2. `--key-file PATH`
3. Environment variable `AIHUB_API_KEY`
4. File config `~/.config/aihub/config.json` (dibuat oleh `save-key`, mode `0600`)

```bash
aihub-usage --key sk-xxxxxxxx save-key        # simpan ke file config
export AIHUB_API_KEY=sk-xxxxxxxx              # atau lewat environment
aihub-usage --key-file ~/.config/aihub/key balance
```

Base URL default `https://aihub.metranet.co.id`, bisa dioverride dengan
`--base-url` atau `$AIHUB_BASE_URL`. Jadi script ini tidak terpaku pada Metranet —
arahkan saja ke host new-api lain.

| Variabel | Fungsi |
|---|---|
| `AIHUB_API_KEY` | API key |
| `AIHUB_BASE_URL` | Base URL gateway |
| `AIHUB_CONFIG` | Lokasi file config (default `~/.config/aihub/config.json`) |
| `AIHUB_STORE` | `1`/`true` untuk mengaktifkan arsip log lokal |
| `AIHUB_DB` | Lokasi arsip log lokal (default `~/.local/share/aihub-usage/logs.db`) |
| `AIHUB_CLI` | Path script untuk test suite |

## Integrasi (script & cron)

```bash
aihub-usage --json > saldo.json          # seluruh hasil sebagai JSON
aihub-usage balance --warn-below 5       # exit 3 kalau sisa credit < $5
```

| Exit code | Arti |
|---|---|
| `0` | Normal |
| `1` | Gagal — key ditolak, error jaringan, key belum diset, atau bagian yang diminta gagal diambil |
| `2` | Argumen salah (mis. `-n -1`, `--max-tokens 0`, command tidak dikenal) |
| `3` | Sisa credit di bawah `--warn-below` |

Bagian yang gagal tidak pernah dilaporkan sebagai "tidak ada data": gateway
new-api membalas kegagalan handler dengan HTTP 200 + `{"success":false}`, dan
script memperlakukannya sebagai error.

```bash
#!/usr/bin/env bash
set -uo pipefail
aihub-usage balance --warn-below 5 >/dev/null
rc=$?
case $rc in
  3) aihub-usage balance | mail -s "Saldo aihub menipis" admin@example.com ;;
  0) : ;;
  *) echo "aihub-usage gagal (exit $rc)" >&2 ;;
esac
```

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [Cara kerja & catatan angka](docs/cara-kerja.md) | Endpoint yang dipakai, kenapa cepat, arti tiap angka, tipe log |
| [Arsip log lokal](docs/arsip-lokal.md) | Cara mengaktifkan, mode, dedupe, dan batasnya |
| [Keamanan](docs/keamanan.md) | Penanganan API key, izin file, isi arsip |
| [Pengembangan](docs/pengembangan.md) | Test suite, struktur repo, mode mock gateway |

## Lisensi

[MIT](LICENSE) © 2026 zetkey

Bebas dipakai, diubah, dan didistribusikan, termasuk untuk keperluan komersial,
selama notice hak cipta dan izin di atas disertakan. Perangkat lunak diberikan
"apa adanya", tanpa jaminan dalam bentuk apa pun.
