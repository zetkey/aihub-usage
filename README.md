# aihub-usage

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](#persyaratan)
[![Tests](https://img.shields.io/badge/tests-88%20passed-brightgreen)](#pengembangan)
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
langsung dicocokkan dengan response gateway tanpa baris terpisah. Untuk key dengan
kuota terbatas, ketiga angka itu terisi penuh:

```console
$ aihub-usage key

API KEY INI
  nama          : kontraktor-1
  limit key     : $5.00  (2,500,000 quota)
  terpakai key  : $2.00  (1,000,000 quota)
  sisa kuota key: $3.00  (1,500,000 quota)
  kadaluarsa    : 2026-10-08 12:18
  batas model   : gpt-5.5
```

`aihub-usage tokens` menambah rincian per model:

```console
$ aihub-usage tokens

PEMAKAIAN TOKEN
  dasar hitung  : 4 log terakhir (2026-10-08 17:18 s/d 2026-10-08 18:20)
  request       : 2
  token masuk   : 2,000
  token keluar  : 440
  TOTAL TOKEN   : 2,440
  rata-rata     : 1,220 token/request
  biaya jendela : $0.0350  (Rp 630)
  biaya 1jt tok : $14.34

  PER MODEL
  model                           req        masuk       keluar        total      biaya
  gpt-5.5                           1        1,200          340        1,540    $0.0250
  deepseek-v4.1-flash               1          800          100          900    $0.0100

  kuota terpakai: 617,250 quota = $1.23
  sisa kuota    : 41,258,875 quota = $82.52
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
- **Pemakaian token** — token masuk/keluar/total, rata-rata per request, biaya per
  juta token, dan rincian per model (`tokens`).
- **Arsip log lokal (opsional, default OFF)** — mengakumulasi log antar-run agar
  perhitungan token melampaui batas 1000 log terakhir milik gateway. Aktifkan
  lewat `local_store` di config; output selalu menyebut mode yang dipakai.
- **Kuota per API key** — status unlimited, batas, kadaluarsa, batas model, plus
  nilai **quota** asli di samping setiap angka dolar.
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
| `--store` | Aktifkan arsip log lokal untuk run ini (default: ikut `local_store` di config) |
| `--no-store` | Paksa hitung hanya dari jendela log API (menang atas config/env) |
| `--anthropic` | `probe` lewat `/v1/messages` (protokol Anthropic) |

Contoh:

```bash
aihub-usage                        # ringkasan lengkap
aihub-usage balance                # cek saldo saja
aihub-usage tokens                 # pemakaian token + rincian per model
aihub-usage logs -n 20             # 20 request terakhir
aihub-usage models                 # model yang tersedia untuk key ini
aihub-usage status                 # info gateway (tidak butuh API key)
aihub-usage probe --anthropic      # tes key lewat /v1/messages
aihub-usage probe --json           # hasil probe sebagai JSON
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

### Arsip log lokal (opsional)

`/api/log/token` hanya mengembalikan **1000 baris terakhir** (nilai `MaxRecentItems`
di new-api, di-hardcode) dan tidak punya parameter paginasi. Jadi angka token dari
API saja selalu terpotong. Arsip lokal mengakumulasi log antar-run sehingga
cakupannya bertambah setiap kali CLI dijalankan.

**Default OFF** — tidak ada file yang dibuat sampai Anda mengaktifkannya:

```bash
aihub-usage store on              # aktifkan permanen (local_store=true)
aihub-usage store off             # nonaktifkan lagi
aihub-usage store                 # lihat status (aktif/nonaktif, path config & arsip)
aihub-usage tokens --store        # sekali jalan saja, tanpa mengubah config
AIHUB_STORE=1 aihub-usage tokens  # lewat environment
```

`store on`/`store off` mengubah `~/.config/aihub/config.json` dan **tidak perlu
API key** — jadi tidak perlu menempelkan `--key` hanya untuk mematikan fitur ini.
Setelah `store off`, perintah biasa langsung kembali menghitung dari API saja tanpa
`--no-store`:

```console
$ aihub-usage store
Arsip log lokal: nonaktif (default)
  config : /Users/anda/.config/aihub/config.json
  db     : /Users/anda/.local/share/aihub-usage/logs.db (belum dibuat)
  flag   : local_store tidak diset
  ubah   : aihub-usage store on  |  aihub-usage store off
```

`store off` tidak menghapus arsip yang sudah terkumpul — script memberi tahu
lokasinya supaya Anda bisa menghapusnya sendiri bila mau.

Isi `~/.config/aihub/config.json` setelah diaktifkan:

```json
{
  "api_key": "sk-...",
  "local_store":true
}
```

Setiap kali arsip dipakai, output menyebut mode-nya secara eksplisit — aktif
menghitung gabungan arsip + API, nonaktif menghitung dari jendela API saja:

```console
$ aihub-usage tokens --store

PEMAKAIAN TOKEN
  dasar hitung  : 1,204 log di arsip lokal (2026-10-01 09:12 s/d 2026-10-08 17:56)
  run ini       : 87 log baru diarsipkan
  mode          : ARSIP LOKAL AKTIF — token dihitung dari gabungan log tersimpan + log yang baru diambil dari API
  arsip         : /Users/anda/.local/share/aihub-usage/logs.db
  ...

$ aihub-usage tokens

PEMAKAIAN TOKEN
  dasar hitung  : 533 log terakhir (2026-10-08 08:38 s/d 2026-10-08 17:56)
  mode          : API SAJA — arsip lokal tidak aktif, token hanya dihitung dari jendela log yang dikirim gateway
  ...
```

Dedupe memakai `(key_hash, id)`, jadi menjalankan CLI berkali-kali tidak
menghitung ganda. Kalau antar-run ada log yang terlewat (kalah cepat dari batas
1000 log), script mencetak baris `PERINGATAN` — jalankan lebih sering, mis. lewat
cron, supaya celahnya makin kecil.

## Integrasi (script & cron)

```bash
aihub-usage --json > saldo.json          # seluruh hasil sebagai JSON
aihub-usage balance --warn-below 5       # exit 3 kalau sisa credit < $5
```

Exit code:

| Code | Arti |
|---|---|
| `0` | Normal |
| `1` | Gagal — key ditolak, error jaringan, key belum diset, atau bagian yang diminta gagal diambil (mis. `logs` ditolak gateway) |
| `2` | Argumen salah (mis. `-n -1`, `--max-tokens 0`, command tidak dikenal) |
| `3` | Sisa credit di bawah `--warn-below` |

Bagian yang gagal tidak pernah dilaporkan sebagai "tidak ada data": gateway new-api
membalas kegagalan handler dengan **HTTP 200 + `{"success":false}`**, dan script
memperlakukannya sebagai error (exit `1`), bukan sebagai hasil kosong.

Contoh pemakaian di cron — kirim notifikasi bila saldo menipis, tanpa salah
menganggap error jaringan sebagai saldo habis:

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

## Cara kerja & catatan angka

Semua data diambil dari endpoint new-api yang memang sudah ada:

| Kebutuhan | Endpoint | Auth |
|---|---|---|
| Total & sisa credit akun | `GET /v1/dashboard/billing/subscription` + `GET /v1/dashboard/billing/usage` | API key |
| Kuota & pemakaian key | `GET /api/usage/token/` | API key |
| Log request key ini | `GET /api/log/token` | API key |
| Pemakaian token (masuk/keluar, per model) | `GET /api/log/token` (dijumlahkan dari kolom `prompt_tokens`/`completion_tokens`) | API key |
| Daftar model | `GET /v1/models` | API key |
| Info gateway (kurs, satuan) | `GET /api/status` | publik |
| Probe 1 request | `POST /v1/chat/completions` atau `POST /v1/messages` | API key |

Beberapa detail yang mudah salah baca:

- **Satuan internal gateway adalah `quota`.** `500.000 quota = $1`, dan nilainya
  diambil dinamis dari `/api/status` — bukan hardcode. Setiap angka kuota key
  (`limit key`, `terpakai key`, `sisa kuota key`) ditampilkan sebagai dolar
  **beserta nilai quota aslinya dalam tanda kurung**, jadi bisa dicocokkan
  langsung dengan response `/api/usage/token` tanpa baris terpisah.
- **Angka token dari API adalah jendela log, bukan total seumur hidup key.**
  Tidak ada endpoint new-api yang memberi agregat token untuk sebuah API key, jadi
  token dijumlahkan dari `/api/log/token` — dan endpoint itu mengembalikan paling
  banyak `MaxRecentItems` baris terakhir (default **1000** di new-api, hardcode,
  tanpa paginasi). Bagian `PEMAKAIAN TOKEN` selalu menyebut **dasar hitung** dan
  **mode**-nya. Hanya baris `type=2` (pemakaian) yang dihitung: baris error/refund
  bernilai 0 token dan tidak dihitung sebagai request.
- **Arsip lokal mengatasi batas 1000 itu, tapi tidak menghapus batasnya.**
  Cakupannya hanya seluas yang sempat terarsip: log yang muncul dan hilang di
  antara dua run (lebih dari 1000 request) tetap tidak terekam. Karena itu run
  berkala lebih penting daripada run sesekali, dan `PERINGATAN` muncul saat celah
  itu terdeteksi.
- **`biaya 1jt tok` adalah biaya rata-rata per 1 juta token** pada jendela itu
  (campuran model), bukan tarif resmi satu model.
- **`total_usage` dari endpoint billing satuannya cent**, sedangkan
  `hard_limit_usd` satuannya dolar. Jadi
  `sisa = hard_limit_usd − total_usage / 100`.
- **`hard_limit_usd` bukan "batas yang boleh dipakai"**, melainkan total credit
  yang pernah diberikan (terpakai + sisa).
- **Key dengan kuota unlimited** melaporkan `total_granted`/`total_available`
  bernilai `0` dan `unlimited_quota:true`. Itu bukan berarti saldo kosong — script
  menuliskan baris `catatan` untuk menjelaskannya dan mengarahkan ke `SISA CREDIT`.
- **Statistik bisa per-key, bukan per-akun**, tergantung konfigurasi gateway.
  Bila angka billing berbeda dari `/api/usage/token/`, script menandainya dengan
  baris `catatan` — bukan diam-diam memilih salah satu.
- **Rupiah hanya nilai tampilan**, dikonversi dari `currency_rates.IDR` di
  `/api/status` (kurs referensi, bukan kurs bank). Pembukuan tetap USD.
- **Baris refund itu normal**: new-api memotong estimasi di awal request lalu
  mengembalikan selisihnya bila panggilan gagal.
- **Kolom `model` pada log bisa berisi label**, bukan nama model, untuk baris
  non-pemakaian. Nomor `type` new-api (`model/log.go`) dan labelnya:

  | `type` | Arti | Label di output |
  |---|---|---|
  | `1` | topup saldo | `isi saldo` |
  | `2` | pemakaian | nama model |
  | `3` | operasi kelola | `kelola` |
  | `4` | sistem | `sistem` |
  | `5` | error (mis. `status_code=499, context canceled`) | `error` |
  | `6` | refund | `refund` |
  | `7` | login | `login` |

  Perhatikan `5` = **error** dan `6` = **refund** — mudah tertukar, dan baris
  error memang sering muncul walau request terlihat sukses di sisi klien.
- **Kegagalan handler datang sebagai HTTP 200.** Endpoint `/api/*` new-api
  (`common.ApiError`) membalas `{"success":false,"message":...}` dengan status
  `200`. Script memeriksa envelope itu; tanpa itu, log yang ditolak terbaca
  seolah-olah "belum ada log".

## Pengembangan

```bash
python3 test_aihub_usage.py
```

Test suite menjalankan CLI terhadap `mock_gateway.py` yang meniru response asli
new-api (bentuk `/v1/dashboard/billing/*` yang memakai cent, key unlimited vs
terbatas, log semua tipe, ringkasan token + rincian per model, arsip lokal
termasuk dedupe/scope/fallback, body error 401, envelope `success:false`, sampai
isolasi config/env). **Tidak memakai credit asli dan tidak butuh API key** —
config **dan arsip** asli sengaja diabaikan lewat `AIHUB_CONFIG`/`AIHUB_DB` agar
hasilnya sama di mesin siapa pun dan arsip asli Anda tidak tersentuh.

```bash
AIHUB_CLI=/path/lain/aihub-usage python3 test_aihub_usage.py   # uji versi lain
```

Status: **88/88 passed**.

Struktur repo:

```
aihub-usage            script utama (executable, di-symlink ke ~/.local/bin)
install.sh             pemasangan symlink dan uninstall
test_aihub_usage.py    test suite (88 kasus, tanpa API key asli)
mock_gateway.py        mock new-api untuk keperluan tes
README.md              dokumen ini
```

## Keamanan

- API key tidak pernah ditulis ke output maupun log; yang tampil hanya nama key.
- `save-key` menulis `~/.config/aihub/config.json` dengan mode `0600`.
- Arsip log lokal (bila diaktifkan) dibuat dengan mode `0600` dan hanya menyimpan
  kolom yang perlu dihitung: id log, waktu, tipe, nama model, token, quota, durasi.
  **Tidak** menyimpan `ip`, `username`, atau isi request. Baris di-scope dengan
  SHA-256 API key — file tidak berisi key itu sendiri.
- Jangan commit API key. Bila ragu, gunakan `--key-file` di luar repo atau
  environment variable.
- Script hanya membaca data dari gateway; tidak ada operasi tulis, tidak ada
  pembuatan/penghapusan key. Arsip lokal murni di sisi Anda dan bisa dihapus kapan
  saja (`rm -rf ~/.local/share/aihub-usage`).

## Lisensi

[MIT](LICENSE) © 2026 zetkey

Bebas dipakai, diubah, dan didistribusikan, termasuk untuk keperluan komersial,
selama notice hak cipta dan izin di atas disertakan. Perangkat lunak diberikan
"apa adanya", tanpa jaminan dalam bentuk apa pun.
