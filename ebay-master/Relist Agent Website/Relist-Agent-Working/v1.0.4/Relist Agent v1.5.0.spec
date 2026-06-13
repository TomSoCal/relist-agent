# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[('ERA_Icon.png', '.'), ('ERA_Icon.ico', '.'), ('ERA_Logo.png', '.'), ('theme.py', '.'), ('update_checker.py', '.')],
    hiddenimports=['curl_cffi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Relist Agent v1.5.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[r'C:\Users\tom\agents\ebay-master\Relist Agent Website\Relist-Agent-Working\v1.0.4\ERA_Icon.ico'],
    onefile=True,
)
