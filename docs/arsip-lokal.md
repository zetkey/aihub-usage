# Arsip log lokal (opsional)

`/api/log/token` hanya mengembalikan **1000 baris terakhir** (nilai `MaxRecentItems`
di new-api, di-hardcode) dan tidak punya parameter paginasi. Jadi angka token dari
API saja selalu terpotong. Arsip lokal mengakumulasi log antar-run sehingga
cakupannya bertambah setiap kali CLI dijalankan.

**Default OFF** — tidak ada file yang dibuat sampai Anda mengaktifkannya.

## Mengaktifkan

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
`--no-store`.

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

## Mode di output

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

## Dedupe dan celah log

Identitas log = `request_id` dari gateway (stabil antar-run). `id` yang juga
dikirim gateway bukan identitas: itu nomor urut jendela (1 = terbaru) yang
berubah tiap fetch, jadi tidak dipakai untuk dedupe. Dengan begitu menjalankan
CLI berkali-kali tidak menghitung ganda. Kalau antar-run ada log yang terlewat
(kalah cepat dari batas 1000 log), script mencetak baris `PERINGATAN` — jalankan
lebih sering, mis. lewat cron, supaya celahnya makin kecil.

Arsip lama (dedupe pakai `id`, bisa beku di 1000 baris pertama) dimigrasi
otomatis saat dibuka; baris lamanya disimpan sebagai `legacy:<id>` dan
digantikan baris asli begitu window baru memuat log yang sama.

**Batas yang jujur:** arsip tidak menghapus batas 1000 log, hanya menambah cakupan
seluas yang sempat terarsip. Log yang muncul dan hilang di antara dua run (lebih
dari 1000 request) tetap tidak terekam.

## Urutan prioritas

`--no-store` > `--store` > `$AIHUB_STORE` > `local_store` di config > off.

## Isi file

Arsip dibuat dengan mode `0600` di dalam direktori `0700`, dan hanya menyimpan
kolom yang perlu dihitung: id log, waktu, tipe, nama model, token, quota, durasi.
**Tidak** menyimpan `ip`, `username`, atau isi request. Baris di-scope dengan
SHA-256 API key — file tidak berisi key itu sendiri.

Lokasi default `~/.local/share/aihub-usage/logs.db`, bisa dioverride dengan
`$AIHUB_DB`. Menghapus arsip: `rm -rf ~/.local/share/aihub-usage`.
