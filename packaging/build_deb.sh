#!/usr/bin/env bash
#
# Rakit paket .deb dari hasil build PyInstaller (onedir).
#
# Pemakaian:
#   bash packaging/build_deb.sh <versi> <folder-hasil-pyinstaller>
# Contoh:
#   bash packaging/build_deb.sh 0.1.0 dist/pdf-combine
#
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Pemakaian: $0 <versi> <folder-hasil-pyinstaller>" >&2
    exit 1
fi

VERSION="${1#v}"
APPDIR="$2"
PKG="pdf-combine"
ARCH="amd64"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build/deb"
TREE="$BUILD_DIR/${PKG}_${VERSION}_${ARCH}"
OUT="$ROOT/dist/${PKG}_${VERSION}_${ARCH}.deb"

if [ ! -x "$APPDIR/$PKG" ]; then
    echo "Binary tidak ditemukan: $APPDIR/$PKG" >&2
    exit 1
fi

rm -rf "$TREE"
mkdir -p \
    "$TREE/DEBIAN" \
    "$TREE/opt/$PKG" \
    "$TREE/usr/bin" \
    "$TREE/usr/share/applications" \
    "$TREE/usr/share/icons/hicolor/256x256/apps" \
    "$TREE/usr/share/icons/hicolor/512x512/apps"

# Salin aplikasi utuh (onedir)
cp -a "$APPDIR/." "$TREE/opt/$PKG/"
chmod 755 "$TREE/opt/$PKG/$PKG"

# Launcher di PATH + entri menu + ikon
ln -sfn "/opt/$PKG/$PKG" "$TREE/usr/bin/$PKG"
install -m 644 "$ROOT/packaging/pdf-combine.desktop" \
    "$TREE/usr/share/applications/$PKG.desktop"
install -m 644 "$ROOT/assets/icon-256.png" \
    "$TREE/usr/share/icons/hicolor/256x256/apps/$PKG.png"
install -m 644 "$ROOT/assets/icon.png" \
    "$TREE/usr/share/icons/hicolor/512x512/apps/$PKG.png"

# Script maintainer
cat > "$TREE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF

cat > "$TREE/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF

chmod 755 "$TREE/DEBIAN/postinst" "$TREE/DEBIAN/postrm"

INSTALLED_SIZE="$(du -sk "$TREE" | cut -f1)"

cat > "$TREE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Maintainer: Frendy Rikal Gerung <frendydev1@gmail.com>
Homepage: https://github.com/Greenson22/PDF-Combine-Python
Depends: libc6, libgl1, libegl1, libxkbcommon0, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0, libxcb-xinerama0, libfontconfig1, libdbus-1-3
Description: PDF Combine - gabung PDF dan konversi gambar ke PDF
 Aplikasi desktop untuk menggabungkan file PDF dan gambar menjadi satu
 dokumen PDF, serta mengonversi banyak gambar sekaligus ke PDF.
 Dilengkapi pengaturan ukuran kertas, margin per sisi, dan preview live.
EOF

mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$TREE" "$OUT"

echo "Paket dibuat: $OUT"
