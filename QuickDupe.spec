# -*- mode: python ; coding: utf-8 -*-
import os
import pydivert
import sys

# Paths
# When PyInstaller executes a spec file, __file__ may not be defined; fall back to cwd
try:
    here = os.path.dirname(__file__)
    if not here:
        here = os.path.abspath('.')
except NameError:
    here = os.path.abspath('.')
pydivert_path = os.path.dirname(pydivert.__file__)
windivert_x64 = os.path.join(here, 'windivert_sdk', 'WinDivert-2.2.2-A', 'x64')
images_dir = os.path.join(here, 'images')

# Binaries: point to canonical SDK x64 copies
binaries = []
win_dll = os.path.join(windivert_x64, 'WinDivert.dll')
win_sys64 = os.path.join(windivert_x64, 'WinDivert64.sys')
if os.path.exists(win_dll):
    binaries.append((win_dll, '.'))
if os.path.exists(win_sys64):
    binaries.append((win_sys64, '.'))

# Data files: use images from images/ directory and include icon.ico from repo root
datas = []
icon_path = os.path.join(here, 'icon.ico')
if os.path.exists(icon_path):
    datas.append((icon_path, '.'))
# include common UI images (place them at root in the bundle)
for name in ['icon.png', 'NONE.png', 'N.png', 'NE.png', 'E.png', 'SE.png', 'S.png', 'SW.png']:
    p = os.path.join(images_dir, name)
    if os.path.exists(p):
        datas.append((p, '.'))

a = Analysis(
    ['quickdupe.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [(pydivert_path, 'pydivert')],
    hiddenimports=['pynput', 'pynput.keyboard', 'pynput.mouse', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'pynput._util', 'pynput._util.win32', 'pydivert', 'keyboard'],
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
    name='QuickDupe',
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
    uac_admin=True,
    icon=['icon.ico'],
)
