# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None
project_root = Path(SPECPATH).parent
payload_zip = project_root / "build" / "installer_payload" / "PrivacyMasker_payload.zip"
icon_path = project_root / "assets" / "app.ico"
app_icon = str(icon_path) if icon_path.exists() else None

a = Analysis(
    [str(project_root / "installer" / "privacy_masker_installer.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(payload_zip), ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tests", "sample_files", "__pycache__", ".pytest_cache"],
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
    name="PrivacyMaskerSetup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
