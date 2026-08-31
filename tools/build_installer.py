from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIST_DIR = PROJECT_ROOT / "dist" / "PrivacyMasker"
APP_EXE = APP_DIST_DIR / "PrivacyMasker.exe"
PAYLOAD_DIR = PROJECT_ROOT / "build" / "installer_payload"
PAYLOAD_ZIP = PAYLOAD_DIR / "PrivacyMasker_payload.zip"
INSTALLER_SPEC = PROJECT_ROOT / "installer" / "privacy_masker_installer.spec"
INSTALLER_EXE = PROJECT_ROOT / "dist" / "PrivacyMaskerSetup.exe"


def require_app_dist() -> None:
    if not APP_EXE.exists():
        raise FileNotFoundError(
            "dist\\PrivacyMasker\\PrivacyMasker.exe was not found. "
            "Run build_windows.bat first."
        )
    if not (APP_DIST_DIR / "_internal").exists():
        raise FileNotFoundError(
            "dist\\PrivacyMasker\\_internal was not found. "
            "The installer must package the full onedir distribution."
        )


def create_payload_zip() -> None:
    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(PAYLOAD_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in APP_DIST_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(APP_DIST_DIR))


def run_pyinstaller() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(INSTALLER_SPEC),
        "--clean",
        "-y",
        "--distpath",
        str(PROJECT_ROOT / "dist"),
        "--workpath",
        str(PROJECT_ROOT / "build" / "installer"),
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> int:
    print("[1/4] Checking app distribution...")
    require_app_dist()

    print("[2/4] Creating installer payload zip...")
    create_payload_zip()
    print(f"Payload: {PAYLOAD_ZIP}")

    print("[3/4] Building setup executable...")
    run_pyinstaller()

    print("[4/4] Checking setup executable...")
    if not INSTALLER_EXE.exists():
        raise FileNotFoundError(f"Installer was not created: {INSTALLER_EXE}")

    print()
    print("[SUCCESS] Installer build completed.")
    print(f"Installer: {INSTALLER_EXE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
