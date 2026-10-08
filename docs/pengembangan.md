# Pengembangan

## Menjalankan test

```bash
python3 test_aihub_usage.py
```

Test suite menjalankan CLI terhadap `mock_gateway.py` yang meniru response asli
new-api (bentuk `/v1/dashboard/billing/*` yang memakai cent, key unlimited vs
terbatas, log semua tipe, ringkasan token + rincian per model, arsip lokal
termasuk dedupe/scope/fallback, gzip, paralelisme (puncak request bersamaan),
tidak ada endpoint diambil dua kali, body error 401, envelope `success:false`,
sampai isolasi config/env). **Tidak memakai credit asli dan tidak butuh API
key** — config **dan arsip** asli sengaja diabaikan lewat `AIHUB_CONFIG`/`AIHUB_DB`
agar hasilnya sama di mesin siapa pun dan arsip asli Anda tidak tersentuh.

```bash
AIHUB_CLI=/path/lain/aihub-usage python3 test_aihub_usage.py   # uji versi lain
```

Status: **101/101 passed**.

## Struktur repo

```
aihub-usage            script utama (executable, di-symlink ke ~/.local/bin)
install.sh             pemasangan symlink dan uninstall
test_aihub_usage.py    test suite (101 kasus, tanpa API key asli)
mock_gateway.py        mock new-api untuk keperluan tes
docs/                  dokumentasi detail
README.md              gambaran umum
```

## Mock gateway

`mock_gateway.py` bisa dijalankan dengan beberapa mode untuk menguji jalur khusus:

| Flag | Efek |
|---|---|
| `--limited` | Key dengan kuota terbatas (bukan unlimited) |
| `--anykey` | Terima bearer token apa pun (uji scope arsip per key) |
| `--gzip` | Balas dengan `Content-Encoding: gzip` |
| `--emptylogs` | `/api/log/token` sukses tapi tanpa baris |
| `--emptychoices` | `/v1/chat/completions` tanpa entri `choices` |
| `--errlog` | `/api/log/token` membalas HTTP 200 + `{"success":false}` |
| `--redirect PORT` | `/v1/models` membalas 302 ke server lain |
| `--record-auth PATH` | Catat header `Authorization` yang diterima |
| `--counts PATH` | Catat jumlah request per path (JSON) |
| `--concurrency PATH` | Catat puncak request bersamaan |
| `--delay MS` | Tahan setiap respons MS milidetik |

Mock memakai `ThreadingHTTPServer` supaya bisa melayani request bersamaan — tanpa
itu paralelisme CLI tidak akan terukur.
