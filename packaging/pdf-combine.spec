# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller untuk PDF Combine.

Windows : onefile portable -> dist/PDF-Combine.exe
Linux   : onedir          -> dist/pdf-combine/ (dipakai build_deb.sh)
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
IS_WINDOWS = sys.platform == "win32"

NAME = "PDF-Combine" if IS_WINDOWS else "pdf-combine"
ICON = ROOT / "assets" / ("icon.ico" if IS_WINDOWS else "icon.png")

datas = [
    (str(ROOT / "assets" / "icon.png"), "assets"),
    (str(ROOT / "assets" / "profile.jpg"), "assets"),
    (str(ROOT / "VERSION"), "."),
]

excludes = [
    "tkinter",
    "unittest",
    "pydoc",
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtQml",
    "PyQt6.QtQuick",
    "PyQt6.QtQuickWidgets",
    "PyQt6.QtMultimedia",
    "PyQt6.QtMultimediaWidgets",
    "PyQt6.QtBluetooth",
    "PyQt6.QtNfc",
    "PyQt6.QtPositioning",
    "PyQt6.QtSql",
    "PyQt6.QtTest",
    "PyQt6.QtDesigner",
    "PyQt6.QtHelp",
    "PyQt6.Qt3DCore",
    "PyQt6.Qt3DRender",
]

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if IS_WINDOWS:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(ICON),
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(ICON),
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=NAME,
    )
