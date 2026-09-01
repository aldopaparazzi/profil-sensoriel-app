# -*- mode: python ; coding: utf-8 -*-  # noqa: UP009

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
)

# ---------------------------------------------------------------------------
# NumPy
# ---------------------------------------------------------------------------

numpy_hiddenimports = collect_submodules("numpy")
numpy_datas = collect_data_files("numpy")

# ---------------------------------------------------------------------------
# Matplotlib
# ---------------------------------------------------------------------------

matplotlib_hiddenimports = collect_submodules("matplotlib")
matplotlib_datas = collect_data_files("matplotlib")

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(  # noqa: F821  # type: ignore
    ["ui.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Données de l'application
        ("data/reference", "data/reference"),
        ("favicon_io/icon.ico", "favicon_io"),
        ("config/runtime.json", "config"),
        # Données nécessaires à NumPy / Matplotlib
        *numpy_datas,
        *matplotlib_datas,
    ],
    hiddenimports=[
        # NumPy
        *numpy_hiddenimports,
        # Matplotlib
        *matplotlib_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# ---------------------------------------------------------------------------
# PYZ
# ---------------------------------------------------------------------------

pyz = PYZ(a.pure)  # type: ignore # noqa: F821

# ---------------------------------------------------------------------------
# EXE
# ---------------------------------------------------------------------------

exe = EXE(  # noqa: F821  # type: ignore
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Profil Sensoriel",
    icon="favicon_io/icon.ico",
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
)

# ---------------------------------------------------------------------------
# COLLECT
# ---------------------------------------------------------------------------

coll = COLLECT(  # noqa: F821  # type: ignore
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Profil Sensoriel",
)
