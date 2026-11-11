"""Informasi aplikasi dan helper path resource (dev maupun hasil PyInstaller)."""

import os
import sys

APP_NAME = "PDF Combine"
APP_DISPLAY_NAME = "PDF Combine"
APP_DESCRIPTION = "Gabungkan PDF dan konversi gambar ke PDF"
APP_ORG = "PDFToolbox"
APP_ID = "PDFToolbox.PDFCombine"

# Data pengembang (mengikuti halaman About aplikasi Rutinitasku)
DEVELOPER_NAME = "Frendy Rikal Gerung, S.Kom."
DEVELOPER_TITLE = "Lulusan Sarjana Komputer dari Universitas Negeri Manado"
DEVELOPER_BIO = (
    "Dibuat dengan semangat untuk menyediakan alat bantu produktivitas yang "
    "personal. Menggabungkan file PDF, gambar, serta pengaturan ukuran kertas "
    "dan margin dalam satu aplikasi yang berjalan sepenuhnya offline untuk "
    "menjaga privasi data Anda."
)
DEVELOPER_LINKEDIN = "https://linkedin.com/in/frendy-rikal-gerung-bb450b38a/"
DEVELOPER_EMAIL = "frendydev1@gmail.com"
PROJECT_URL = "https://github.com/Greenson22/PDF-Combine-Python"

FALLBACK_VERSION = "0.1.0"


def resource_path(relative_path):
    """Kembalikan path absolut ke resource, mendukung mode --onefile/onedir."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def read_version():
    """Baca VERSION dari bundle/repo; fallback ke konstanta."""
    try:
        with open(resource_path("VERSION"), "r", encoding="utf-8") as handle:
            version = handle.read().strip()
            if version:
                return version
    except OSError:
        pass
    return FALLBACK_VERSION


def app_icon_path():
    return resource_path(os.path.join("assets", "icon.png"))


def profile_image_path():
    return resource_path(os.path.join("assets", "profile.jpg"))
