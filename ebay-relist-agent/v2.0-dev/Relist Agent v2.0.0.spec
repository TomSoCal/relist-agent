# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:\Users\tom\agents\ebay-relist-agent\v2.0-dev\config.json', '.'),
        
        ('ERA_Logo.png', '.'),
        ('ERA_Icon.ico', '.'),
        ('INFO_ICON.png', '.'),
        ('theme.py', '.'),
        ('config.json', '.'),
    ],
    hiddenimports=['tkinter', 'PIL', 'update_checker'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Relist Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='ERA_Icon.ico',
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

