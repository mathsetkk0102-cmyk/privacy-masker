# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


block_cipher = None
project_root = Path(SPECPATH)

datas = [
    (str(project_root / "ui" / "styles.qss"), "ui"),
    (str(project_root / "README.md"), "."),
    (str(project_root / "README_RELEASE.md"), "."),
]

icon_path = project_root / "assets" / "app.ico"
app_icon = str(icon_path) if icon_path.exists() else None

hiddenimports = []
for package_name in ("openpyxl", "docx", "fitz", "pytesseract", "PIL"):
    hiddenimports.extend(collect_submodules(package_name))

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tests",
        "sample_files",
        "__pycache__",
        ".pytest_cache",
    ],
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
    name="PrivacyMasker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PrivacyMasker",
)
