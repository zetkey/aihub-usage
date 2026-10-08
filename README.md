# aihub-usage

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](#persyaratan)
[![Tests](https://img.shields.io/badge/tests-32%20passed-brightgreen)](#pengembangan)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](#persyaratan)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

CLI untuk melihat **sisa credit (saldo), pemakaian, dan log request** dari API key
pada gateway [Scala AI Gateway by Metranet](https://aihub.metranet.co.id).

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
  terpakai key  : $1.23
  sisa kuota key: unlimited
  kadaluarsa    : tidak ada
  batas model   : semua model
```

---

## Daftar isi

- [Fitur](#fitur)
- [Persyaratan](#persyaratan)
- [Instalasi](#instalasi)
- [Penggunaan](#penggunaan)
- [Konfigurasi](#konfigurasi)
- [Integrasi (script & cron)](#integrasi-script--cron)
- [Cara kerja & catatan angka](#cara-kerja--catatan-angka)
- [Pengembangan](#pengembangan)
- [Keamanan](#keamanan)
- [Lisensi](#lisensi)

## Fitur

- **Sisa credit akun** — total credit, terpakai, dan sisa (USD + estimasi Rupiah).
- **Kuota per API key** — status unlimited, batas, kadaluarsa, dan batas model.
- **Log request** — waktu, model, token masuk/keluar, biaya, dan durasi per panggilan.
- **Daftar model** — model yang bisa dipakai oleh key tersebut.
- **Probe** — kirim satu request kecil untuk memastikan key benar-benar jalan.
- **Mode JSON & exit code** — siap dipakai di script, cron, atau monitoring.
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

`install.sh` membuat symlink `~/.local/bin/aihub-usage` → file di repo. Karena itu
`git pull` sudah cukup untuk memakai versi terbaru; tidak perlu install ulang.

Script ini **tidak** menyentuh file konfigurasi shell Anda. Kalau `~/.local/bin`
belum ada di PATH, ia hanya menampilkan perintah yang perlu Anda tambahkan sendiri.

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
| `all` *(default)* | Status gateway + credit akun + info API key |
| `balance` | Hanya sisa credit akun |
| `key` | Hanya kuota dan pemakaian API key ini |
| `logs` | Log request terakhir lewat key ini (`-n` untuk jumlah baris) |
| `models` | Daftar model yang bisa dipakai key ini |
| `status` | Info gateway: versi, kurs, satuan quota (tanpa API key) |
| `probe` | Kirim 1 request kecil untuk menguji key |
| `save-key` | Simpan API key ke file config |

| Opsi | Keterangan |
|---|---|
| `--key sk-...` | API key untuk sekali pakai |
| `--key-file PATH` | Baca API key dari baris pertama file |
| `--base-url URL` | Override base URL (default `https://aihub.metranet.co.id`) |
| `--json` | Output JSON untuk diproses script |
| `-n, --limit N` | Jumlah log yang ditampilkan (default `10`) |
| `--warn-below USD` | Keluar dengan exit code `3` bila sisa credit di bawah nilai ini |
| `--model NAMA` | Model untuk `probe` |
| `--max-tokens N` | `max_tokens` saat `probe` (default `1`) |
| `--anthropic` | `probe` lewat `/v1/messages` (protokol Anthropic) |

Contoh:

```bash
aihub-usage                        # ringkasan lengkap
aihub-usage balance                # cek saldo saja
aihub-usage logs -n 20             # 20 request terakhir
aihub-usage models                 # model yang tersedia untuk key ini
aihub-usage status                 # info gateway (tidak butuh API key)
aihub-usage probe --anthropic      # tes key lewat /v1/messages
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
| `AIHUB_CLI` | Path script untuk test suite |

## Integrasi (script & cron)

```bash
aihub-usage --json > saldo.json          # seluruh hasil sebagai JSON
aihub-usage balance --warn-below 5       # exit 3 kalau sisa credit < $5
```

Exit code:

| Code | Arti |
|---|---|
| `0` | Normal |
| `1` | Gagal — key ditolak, error jaringan, atau key belum diset |
| `3` | Sisa credit di bawah `--warn-below` |

Contoh pemakaian di cron — kirim notifikasi bila saldo menipis:

```bash
#!/usr/bin/env bash
set -euo pipefail
if ! aihub-usage balance --warn-below 5 >/dev/null; then
  aihub-usage balance | mail -s "Saldo aihub menipis" admin@example.com
fi
```

## Cara kerja & catatan angka

Semua data diambil dari endpoint new-api yang memang sudah ada:

| Kebutuhan | Endpoint | Auth |
|---|---|---|
| Total & sisa credit akun | `GET /v1/dashboard/billing/subscription` + `GET /v1/dashboard/billing/usage` | API key |
| Kuota & pemakaian key | `GET /api/usage/token/` | API key |
| Log request key ini | `GET /api/log/token` | API key |
| Daftar model | `GET /v1/models` | API key |
| Info gateway (kurs, satuan) | `GET /api/status` | publik |
| Probe 1 request | `POST /v1/chat/completions` atau `POST /v1/messages` | API key |

Beberapa detail yang mudah salah baca:

- **Satuan internal gateway adalah `quota`.** `500.000 quota = $1`, dan nilainya
  diambil dinamis dari `/api/status` — bukan hardcode.
- **`total_usage` dari endpoint billing satuannya cent**, sedangkan
  `hard_limit_usd` satuannya dolar. Jadi
  `sisa = hard_limit_usd − total_usage / 100`.
- **`hard_limit_usd` bukan "batas yang boleh dipakai"**, melainkan total credit
  yang pernah diberikan (terpakai + sisa).
- **Key dengan kuota unlimited** melaporkan `total_granted`/`total_available`
  bernilai `0` dan `unlimited_quota:true`. Itu bukan berarti saldo kosong.
- **Statistik bisa per-key, bukan per-akun**, tergantung konfigurasi gateway.
  Bila angka billing berbeda dari `/api/usage/token/`, script menandainya dengan
  baris `catatan` — bukan diam-diam memilih salah satu.
- **Rupiah hanya nilai tampilan**, dikonversi dari `currency_rates.IDR` di
  `/api/status` (kurs referensi, bukan kurs bank). Pembukuan tetap USD.
- **Baris refund itu normal**: new-api memotong estimasi di awal request lalu
  mengembalikan selisihnya bila panggilan gagal.

## Pengembangan

```bash
python3 test_aihub_usage.py
```

Test suite menjalankan CLI terhadap `mock_gateway.py` yang meniru response asli
new-api (bentuk `/v1/dashboard/billing/*` yang memakai cent, key unlimited vs
terbatas, log, body error 401, sampai isolasi config/env). **Tidak memakai credit
asli dan tidak butuh API key** — config asli sengaja diabaikan lewat `AIHUB_CONFIG`
agar hasilnya sama di mesin siapa pun.

```bash
AIHUB_CLI=/path/lain/aihub-usage python3 test_aihub_usage.py   # uji versi lain
```

Status: **32/32 passed**.

Struktur repo:

```
aihub-usage            script utama (executable, di-symlink ke ~/.local/bin)
install.sh             pemasangan symlink dan uninstall
test_aihub_usage.py    test suite (32 kasus, tanpa API key asli)
mock_gateway.py        mock new-api untuk keperluan tes
README.md              dokumen ini
```

## Keamanan

- API key tidak pernah ditulis ke output maupun log; yang tampil hanya nama key.
- `save-key` menulis `~/.config/aihub/config.json` dengan mode `0600`.
- Jangan commit API key. Bila ragu, gunakan `--key-file` di luar repo atau
  environment variable.
- Script hanya membaca data dari gateway; tidak ada operasi tulis, tidak ada
  pembuatan/penghapusan key.

## Lisensi

[MIT](LICENSE) © 2026 zetkey

Bebas dipakai, diubah, dan didistribusikan, termasuk untuk keperluan komersial,
selama notice hak cipta dan izin di atas disertakan. Perangkat lunak diberikan
"apa adanya", tanpa jaminan dalam bentuk apa pun.
