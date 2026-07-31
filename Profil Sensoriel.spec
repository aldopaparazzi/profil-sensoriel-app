# -*- mode: python ; coding: utf-8 -*-  # noqa: UP009

a = Analysis(  # noqa: F821 # type: ignore
    ["ui.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("data/reference", "data/reference"),
        ("favicon_io/icon.ico", "favicon_io"),
        ("config/runtime.json", "config"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # type: ignore # noqa: F821

exe = EXE(  # noqa: F821 # type: ignore
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Dunn2",
    icon="favicon_io/icon.ico",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(  # noqa: F821 # type: ignore
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Profil Sensoriel",
)
