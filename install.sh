#!/usr/bin/env bash
# install.sh — pasang `aihub-usage` ke PATH dengan cara symlink.
#
#   ./install.sh              # symlink ke ~/.local/bin/aihub-usage
#   ./install.sh --uninstall  # hapus symlink
#   BIN_DIR=~/bin ./install.sh
#
# Tidak menyentuh file konfigurasi shell sama sekali. Kalau ~/.local/bin belum
# ada di PATH, script cuma memberi tahu perintah yang perlu Anda tambahkan sendiri.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
TARGET="$BIN_DIR/aihub-usage"
SOURCE="$REPO_DIR/aihub-usage"

die() { printf 'error: %s\n' "$1" >&2; exit 1; }
info() { printf '%s\n' "$1"; }

# --- uninstall --------------------------------------------------------------
if [ "${1:-}" = "--uninstall" ] || [ "${1:-}" = "-u" ]; then
  if [ -L "$TARGET" ]; then
    rm -f "$TARGET"
    info "dihapus: $TARGET"
  elif [ -e "$TARGET" ]; then
    die "$TARGET bukan symlink (file biasa) — tidak saya hapus. Hapus manual kalau memang mau."
  else
    info "tidak ada yang perlu dihapus ($TARGET tidak ada)."
  fi
  exit 0
fi

# --- cek prasyarat ----------------------------------------------------------
[ -f "$SOURCE" ] || die "$SOURCE tidak ada. Jalankan install.sh dari dalam repo."
command -v python3 >/dev/null 2>&1 || die "python3 tidak ditemukan di PATH."
python3 - <<'PY' || die "butuh Python 3.8+ (pakai python3 di PATH)."
import sys
sys.exit(0 if sys.version_info >= (3, 8) else 1)
PY

chmod +x "$SOURCE"

mkdir -p "$BIN_DIR"

# --- pasang symlink ---------------------------------------------------------
if [ -L "$TARGET" ]; then
  CURRENT="$(readlink "$TARGET")"
  if [ "$CURRENT" = "$SOURCE" ]; then
    info "symlink sudah benar: $TARGET -> $SOURCE"
  else
    ln -sfn "$SOURCE" "$TARGET"
    info "symlink diperbarui: $TARGET -> $SOURCE (sebelumnya $CURRENT)"
  fi
elif [ -e "$TARGET" ]; then
  # file biasa (mis. hasil copy manual versi lama) -> simpan sebagai .bak
  BACKUP="$TARGET.bak.$(date +%Y%m%d%H%M%S)"
  mv "$TARGET" "$BACKUP"
  ln -sfn "$SOURCE" "$TARGET"
  info "file lama dipindah ke: $BACKUP"
  info "symlink dibuat      : $TARGET -> $SOURCE"
else
  ln -sfn "$SOURCE" "$TARGET"
  info "symlink dibuat: $TARGET -> $SOURCE"
fi

# --- verifikasi -------------------------------------------------------------
# offline saja: cukup membuktikan shebang + interpreter + argparse jalan.
# (memanggil `status` akan menembak jaringan dan gagal palsu saat offline)
if ! "$TARGET" --help >/dev/null 2>&1; then
  info "peringatan: '$TARGET --help' gagal jalan. Cek manual: $TARGET --help"
fi

# --- cek PATH ---------------------------------------------------------------
case ":$PATH:" in
  *":$BIN_DIR:"*)
    info ""
    info "Siap. Coba: aihub-usage status"
    ;;
  *)
    info ""
    info "$BIN_DIR BELUM ada di PATH sesi ini. Tambahkan sendiri (script ini tidak"
    info "mengubah file konfigurasi shell Anda):"
    case "${SHELL:-}" in
      *fish)  info "  fish : fish_add_path $BIN_DIR" ;;
      *zsh)   info "  zsh  : echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc" ;;
      *)      info "  bash : echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc" ;;
    esac
    info "Atau langsung pakai path lengkap: $TARGET status"
    ;;
esac

# --- langkah berikutnya -----------------------------------------------------
if [ ! -f "$HOME/.config/aihub/config.json" ] && [ -z "${AIHUB_API_KEY:-}" ]; then
  info ""
  info "Belum ada API key tersimpan. Simpan dengan:"
  info "  $TARGET --key sk-xxxxxxxx save-key"
fi
