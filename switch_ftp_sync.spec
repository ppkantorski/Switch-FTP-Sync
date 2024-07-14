# switch_ftp_sync.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['switch_ftp_sync.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.ini', '.'),
        ('icon.png', '.'),
        ('icon.icns', '.'),
        ('icon.ico', '.'),
        ('dark_taskbar.png', '.'),
        ('light_taskbar.png', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='switch_ftp_sync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False to hide the console window
    icon='icon.ico',  # Path to your icon file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='switch_ftp_sync',
)

app = BUNDLE(
    coll,
    name='Switch FTP Sync.app',
    icon='icon.icns',  # Path to your icon file
    bundle_identifier='com.ppkantorski.switch_ftp_sync',
    info_plist={
        'CFBundleName': 'switch_ftp_sync',
        'CFBundleDisplayName': 'FTP Screenshots',
        'CFBundleIdentifier': 'com.ppkantorski.switch_ftp_sync',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'LSUIElement': True,
    }
)
