# Cara kerja & catatan angka

Dokumen ini menjelaskan dari mana setiap angka diambil, kenapa CLI-nya cepat, dan
detail yang mudah salah baca.

## Endpoint yang dipakai

Semua data diambil dari endpoint new-api yang memang sudah ada — tidak ada
scraping HTML.

| Kebutuhan | Endpoint | Auth |
|---|---|---|
| Total & sisa credit akun | `GET /v1/dashboard/billing/subscription` + `GET /v1/dashboard/billing/usage` | API key |
| Kuota & pemakaian key | `GET /api/usage/token/` | API key |
| Log request key ini | `GET /api/log/token` | API key |
| Pemakaian token (masuk/keluar, per model) | `GET /api/log/token` (dijumlahkan dari kolom `prompt_tokens`/`completion_tokens`) | API key |
| Daftar model | `GET /v1/models` | API key |
| Info gateway (kurs, satuan) | `GET /api/status` | publik |
| Probe 1 request | `POST /v1/chat/completions` atau `POST /v1/messages` | API key |

## Kenapa cepat

Dua hal yang membuat CLI ini selesai dalam ~0,3 s, bukan ~0,8 s:

- **Request paralel.** Semua endpoint di atas saling independen, jadi dijalankan
  bersamaan lewat `ThreadPoolExecutor`. Sebelumnya tiap endpoint membuka koneksi
  TLS sendiri secara berurutan, jadi biayanya dijumlahkan (6 × ~140 ms). Sekarang
  totalnya ditentukan endpoint terlama (`/api/log/token`), bukan jumlah endpoint.
- **gzip.** Request mengirim `Accept-Encoding: gzip, deflate`. `/api/log/token`
  bisa >500 KB mentah dan turun ke ~30 KB, jadi endpoint yang paling berat itu
  selesai jauh lebih cepat. Kalau gateway tidak mendukung kompresi, tidak ada
  yang berubah — respons dibaca apa adanya.

`/api/status` dan `/v1/models` tidak dikompresi gateway (masing-masing ~90 KB dan
~19 KB), jadi keduanya memang tetap menjadi bagian biaya terbesar pada perintah
yang memakainya.

## Catatan angka

### Quota

Satuan internal gateway adalah `quota`. `500.000 quota = $1`, dan nilainya diambil
dinamis dari `/api/status` — bukan hardcode. Setiap angka kuota key (`limit key`,
`terpakai key`, `sisa kuota key`) ditampilkan sebagai dolar **beserta nilai quota
aslinya dalam tanda kurung**, jadi bisa dicocokkan langsung dengan response
`/api/usage/token` tanpa baris terpisah.

### Credit akun

- **`total_usage` dari endpoint billing satuannya cent**, sedangkan
  `hard_limit_usd` satuannya dolar. Jadi `sisa = hard_limit_usd − total_usage / 100`.
- **`hard_limit_usd` bukan "batas yang boleh dipakai"**, melainkan total credit
  yang pernah diberikan (terpakai + sisa).
- **Key dengan kuota unlimited** melaporkan `total_granted`/`total_available`
  bernilai `0` dan `unlimited_quota:true`. Itu bukan berarti saldo kosong — script
  menuliskan baris `catatan` untuk menjelaskannya dan mengarahkan ke `SISA CREDIT`.
- **Statistik bisa per-key, bukan per-akun**, tergantung konfigurasi gateway. Bila
  angka billing berbeda dari `/api/usage/token/`, script menandainya dengan baris
  `catatan` — bukan diam-diam memilih salah satu.
- **Rupiah hanya nilai tampilan**, dikonversi dari `currency_rates.IDR` di
  `/api/status` (kurs referensi, bukan kurs bank). Pembukuan tetap USD.

### Token

- **Angka token dari API adalah jendela log, bukan total seumur hidup key.** Tidak
  ada endpoint new-api yang memberi agregat token untuk sebuah API key, jadi token
  dijumlahkan dari `/api/log/token` — dan endpoint itu mengembalikan paling banyak
  `MaxRecentItems` baris terakhir (default **1000** di new-api, hardcode, tanpa
  paginasi). Bagian `PEMAKAIAN TOKEN` selalu menyebut **dasar hitung** dan
  **mode**-nya. Hanya baris `type=2` (pemakaian) yang dihitung: baris error/refund
  bernilai 0 token dan tidak dihitung sebagai request.
- **Arsip lokal mengatasi batas 1000 itu, tapi tidak menghapus batasnya.**
  Cakupannya hanya seluas yang sempat terarsip, dan `PERINGATAN` muncul saat ada
  log yang terlewat antar-run. Detailnya di [arsip-lokal.md](arsip-lokal.md).
- **`biaya 1jt tok` adalah biaya rata-rata per 1 juta token** pada jendela itu
  (campuran model), bukan tarif resmi satu model.

### Log

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
- **Baris refund itu normal**: new-api memotong estimasi di awal request lalu
  mengembalikan selisihnya bila panggilan gagal.
- **Kegagalan handler datang sebagai HTTP 200.** Endpoint `/api/*` new-api
  (`common.ApiError`) membalas `{"success":false,"message":...}` dengan status
  `200`. Script memeriksa envelope itu; tanpa itu, log yang ditolak terbaca
  seolah-olah "belum ada log".
