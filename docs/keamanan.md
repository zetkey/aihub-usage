# Keamanan

## API key

- API key tidak pernah ditulis ke output maupun log; yang tampil hanya nama key.
- **Header `Authorization` tidak diteruskan ke host lain.** Redirect 3xx ke
  host/skema berbeda diikuti tanpa header itu, dan redirect `https`→`http` ditolak
  sama sekali — supaya endpoint/proxy tidak bisa memancing key keluar.
- `save-key` menerima key dari `$AIHUB_API_KEY` atau `--key-file`, tidak wajib
  `--key`. Ini penting karena argumen `--key` terlihat oleh `ps` di mesin
  multiuser dan tersimpan di riwayat shell.
- Jangan commit API key. Bila ragu, gunakan `--key-file` di luar repo atau
  environment variable.

## File di disk

| File | Mode | Isi |
|---|---|---|
| `~/.config/aihub/config.json` | `0600` | API key, base URL, `local_store` |
| `~/.local/share/aihub-usage/logs.db` | `0600` (direktori `0700`) | arsip log, hanya bila diaktifkan |

`save-key`/`store` menulis config dengan `fchmod` **sebelum** menulis, jadi file
lama yang longgar tidak pernah sempat dibaca saat key baru ditulis. Arsip juga
dirapikan ke `0600` walau file-nya sudah ada dengan mode longgar.

## Arsip log

Sifat keamanannya: dibuat `0600` di direktori `0700` (dan dirapikan bila sudah ada
dengan mode longgar), **tidak** menyimpan `ip`, `username`, atau isi request, dan
baris di-scope dengan SHA-256 API key — file tidak berisi key itu sendiri. Isi
kolom dan cara pakainya ada di [arsip-lokal.md](arsip-lokal.md).

Arsip murni di sisi Anda dan bisa dihapus kapan saja:
`rm -rf ~/.local/share/aihub-usage`.

## Akses ke gateway

Script hanya **membaca** data dari gateway: tidak ada operasi tulis, tidak ada
pembuatan atau penghapusan key.

## `--json`

`--json` meneruskan payload gateway apa adanya (objek `/api/usage/token/` dan
setiap baris `/api/log/token`, termasuk field yang tidak ditampilkan di mode teks).
Kalau hasilnya dialihkan ke file, perlakukan file itu seperti data sensitif — sama
seperti contoh `aihub-usage --json > saldo.json` di README.
