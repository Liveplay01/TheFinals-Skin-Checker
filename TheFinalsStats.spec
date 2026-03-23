# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for TheFinalsStats
# Build: pyinstaller TheFinalsStats.spec

import os

block_cipher = None

# Bundle Tesseract if prepare_vendor.py was run first
_tess_vendor = os.path.join(os.path.abspath('.'), 'vendor', 'tesseract')
_tess_datas = [('vendor/tesseract', 'tesseract')] if os.path.isdir(_tess_vendor) else []

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('skin_db.json', '.'),
        *_tess_datas,
    ],
    hiddenimports=[
        'mss',
        'mss.windows',
        'pytesseract',
        'cv2',
        'PIL',
        'PIL.Image',
        'numpy',
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'rapidfuzz',
        'rapidfuzz.fuzz',
        'rapidfuzz.process',
        'win32api',
        'win32con',
        'win32gui',
        'requests',
        'bs4',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'core.capture',
        'core.ocr_engine',
        'core.matcher',
        'core.scanner',
        'data.database',
        'data.storage',
        'data.exporter',
        'data.scraper',
        'ui.main_window',
        'ui.overlay',
        'ui.area_selector',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython'],
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
    name='TheFinalsStats',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # uncomment if you add an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TheFinalsStats',
)
