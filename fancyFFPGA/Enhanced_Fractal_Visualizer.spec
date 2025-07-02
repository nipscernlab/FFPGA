# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['fancyFractal.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets') if os.path.exists('assets') else None,
    ],
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

# Filter out None values from datas
a.datas = [item for item in a.datas if item is not None]

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
