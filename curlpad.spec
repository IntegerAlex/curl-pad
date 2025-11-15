# -*- mode: python ; coding: utf-8 -*-
# Security-hardened PyInstaller spec for curlpad

from PyInstaller.utils.hooks import collect_submodules

# Collect all curlpad submodules
curlpad_submodules = collect_submodules('curlpad')

a = Analysis(
    ['src/curlpad/__main__.py'],  # Use package __main__.py to avoid naming conflict
    pathex=['src'],  # Add src/ to path so PyInstaller can find curlpad package
    binaries=[],
    datas=[],
    # Hidden imports: Ensure critical modules are bundled
    hiddenimports=[
        'subprocess', 'shlex', 'tempfile', 'signal', 'stat', 'platform',
        # Include curlpad package and all its submodules
        'curlpad',
    ] + curlpad_submodules,  # Add all collected submodules
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
    name='curlpad',
    debug=False,
    bootloader_ignore_signals=False,
    # Security: Strip symbols to reduce attack surface
    strip=True,
    # Security: Disable UPX compression (can be modified without detection)
    upx=False,
    upx_exclude=[],
    # Security: Use dedicated runtime temp directory
    runtime_tmpdir='_MEI',
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    # Security: Code signing identity (set via environment or manually)
    # Windows: Set via CODESIGN_IDENTITY env var or signtool post-build
    # macOS: Set via CODESIGN_IDENTITY env var
    codesign_identity=None,  # TODO: Configure code signing for production
    entitlements_file=None,  # macOS: Add entitlements.plist if needed
)
