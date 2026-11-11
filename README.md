# PDF Combine

Aplikasi desktop (Python + PyQt6) untuk menggabungkan file PDF dan gambar
menjadi satu PDF, serta mengonversi banyak gambar sekaligus ke PDF. Tersedia
untuk **Windows** (EXE portable) dan **Ubuntu/Linux** (paket `.deb` dengan
ikon dan entri menu aplikasi).

## Fitur

- Gabung PDF + gambar (PNG/JPG/JPEG) dengan urutan yang bisa diatur.
- Konversi massal gambar ke PDF.
- Ukuran kertas A4, F4/Folio, Letter, Legal, atau ukuran asli gambar.
- Margin atas/bawah/kiri/kanan terpisah (mm) + preset margin tersimpan.
- Preview live sebelum proses.
- Drag & drop file, 100% offline.
- Dialog **Tentang** berisi daftar fitur dan profil pengembang.

## Menjalankan dari source

```bash
python3 -m venv .env
.env/bin/pip install -r requirements.txt
.env/bin/python src/main.py
```

Di Windows: `python -m venv .env`, lalu `.env\Scripts\pip install -r requirements.txt`
dan `.env\Scripts\python src\main.py`.

## Build lokal

Install PyInstaller lebih dulu:

```bash
pip install pyinstaller==6.11.1
```

### EXE portable (Windows)

```bat
pyinstaller --clean --noconfirm packaging\pdf-combine.spec
```

Hasil: `dist\PDF-Combine.exe` — single file, tidak perlu Python terpasang.

### Ubuntu / Linux

```bash
pyinstaller --clean --noconfirm packaging/pdf-combine.spec
bash packaging/build_deb.sh "$(cat VERSION)" dist/pdf-combine
```

Hasil: `dist/pdf-combine_<versi>_amd64.deb`.

Install:

```bash
sudo apt install ./dist/pdf-combine_*_amd64.deb
```

Setelah terpasang:

- Binary: `/opt/pdf-combine/pdf-combine` (symlink `/usr/bin/pdf-combine`)
- Menu aplikasi: **PDF Combine** (kategori Office/Utility)
- Ikon: `/usr/share/icons/hicolor/{256x256,512x512}/apps/pdf-combine.png`

## CI/CD (GitHub Actions)

Workflow `.github/workflows/build.yml` berjalan otomatis:

| Event | Hasil |
| --- | --- |
| Push ke `main` | Artifact `PDF-Combine-windows-x64` (EXE) dan `PDF-Combine-linux-deb` (.deb) |
| Push tag `v*` (mis. `v1.0.0`) | GitHub Release berisi EXE, DEB, dan `SHA256SUMS` |
| Pull request / manual | Build + artifact (tanpa release) |

Build `.deb` memakai runner **ubuntu-22.04** agar kompatibel dengan Ubuntu
22.04, 24.04, dan yang lebih baru.

## Ikon dan foto profil

- `assets/icon.png`, `assets/icon-256.png`, `assets/icon.ico` — ikon aplikasi.
  Ikon placeholder dapat dibuat ulang dengan:
  ```bash
  python packaging/generate_icon.py
  ```
- `assets/profile.jpg` — foto pengembang di dialog Tentang.
  Ganti file ini dengan foto Anda (disarankan rasio 1:1).

## Pengembang

**Frendy Rikal Gerung, S.Kom.** — Universitas Negeri Manado

- LinkedIn: <https://linkedin.com/in/frendy-rikal-gerung-bb450b38a/>
- Email: <frendydev1@gmail.com>
- Repo: <https://github.com/Greenson22/PDF-Combine-Python>
