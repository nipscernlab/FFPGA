# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Monta a lista de datas sem None
datas_list = []
if os.path.exists('assets'):
    datas_list.append(('assets', 'assets'))

a = Analysis(
    ['fancyFractal.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'scipy.special',
        'scipy.linalg',
        'scipy.sparse',
        'numpy.random.common',
        'numpy.random.bounded_integers',
        'numpy.random.entropy',
    ],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Enhanced_Fractal_Visualizer',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
