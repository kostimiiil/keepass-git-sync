# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['keepass-sync-tray.py'],
    pathex=[],
    binaries=[],
    datas=[('sync-keepass.sh', '.'), ('sync-keepass.bat', '.'), ('keepass_icon.png', '.'), ('keepass_icon.ico', '.'), ('config.json.template', '.'), ('.gitignore.template', '.')],
    hiddenimports=['pystray', 'PIL', 'plyer', 'plyer.platforms.win', 'plyer.platforms.win.notification'],
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
    name='KeePassSyncTray',
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
    icon=['keepass_icon.ico'],
)
