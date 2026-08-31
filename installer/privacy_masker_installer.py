from __future__ import annotations

import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


APP_NAME = "PrivacyMasker"
PAYLOAD_NAME = "PrivacyMasker_payload.zip"


def appdata_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Programs" / APP_NAME
    return Path.home() / "AppData" / "Local" / "Programs" / APP_NAME


def resource_path(name: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / name


def message_box(title: str, message: str, error: bool = False) -> None:
    flags = 0x10 if error else 0x40
    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, flags)
    except Exception:
        print(f"{title}: {message}")


def validate_install_dir(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.anchor == str(resolved):
        raise ValueError("Install directory cannot be a drive root.")
    if len(resolved.parts) < 4:
        raise ValueError("Install directory is too broad.")
    return resolved


def remove_existing_install(install_dir: Path) -> None:
    if not install_dir.exists():
        return
    if install_dir.name.lower() != APP_NAME.lower():
        raise ValueError(f"Refusing to replace unexpected directory: {install_dir}")
    shutil.rmtree(install_dir)


def extract_payload(payload_zip: Path, install_dir: Path) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    root = install_dir.resolve()
    with zipfile.ZipFile(payload_zip) as archive:
        for member in archive.infolist():
            target = (install_dir / member.filename).resolve()
            if not str(target).lower().startswith(str(root).lower() + os.sep) and target != root:
                raise ValueError(f"Unsafe archive member: {member.filename}")
        archive.extractall(install_dir)


def powershell_quote(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def create_shortcut(shortcut_path: Path, target_path: Path, working_dir: Path) -> None:
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    script = "\n".join(
        [
            "$shell = New-Object -ComObject WScript.Shell",
            f"$shortcut = $shell.CreateShortcut({powershell_quote(shortcut_path)})",
            f"$shortcut.TargetPath = {powershell_quote(target_path)}",
            f"$shortcut.WorkingDirectory = {powershell_quote(working_dir)}",
            f"$shortcut.IconLocation = {powershell_quote(str(target_path) + ',0')}",
            "$shortcut.Save()",
        ]
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def create_uninstaller(install_dir: Path) -> None:
    desktop_shortcut = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
    start_menu_shortcut = (
        Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / f"{APP_NAME}.lnk"
    )
    uninstall_script = install_dir / f"Uninstall {APP_NAME}.cmd"
    script = f"""@echo off
echo Uninstalling {APP_NAME}...
taskkill /im {APP_NAME}.exe /f >nul 2>nul
del "{desktop_shortcut}" >nul 2>nul
del "{start_menu_shortcut}" >nul 2>nul
cd /d "%LOCALAPPDATA%\\Programs"
rmdir /s /q "{install_dir}" >nul 2>nul
echo Done.
pause
"""
    uninstall_script.write_text(script, encoding="utf-8")


def install(install_dir: Path, create_shortcuts: bool) -> Path:
    payload_zip = resource_path(PAYLOAD_NAME)
    if not payload_zip.exists():
        raise FileNotFoundError(f"Installer payload not found: {payload_zip}")

    install_dir = validate_install_dir(install_dir)
    remove_existing_install(install_dir)
    extract_payload(payload_zip, install_dir)

    app_exe = install_dir / f"{APP_NAME}.exe"
    if not app_exe.exists():
        raise FileNotFoundError(f"Installed executable not found: {app_exe}")

    create_uninstaller(install_dir)

    if create_shortcuts:
        create_shortcut(Path.home() / "Desktop" / f"{APP_NAME}.lnk", app_exe, install_dir)
        start_menu_shortcut = (
            Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / f"{APP_NAME}.lnk"
        )
        create_shortcut(start_menu_shortcut, app_exe, install_dir)

    return app_exe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} installer")
    parser.add_argument("--install-dir", type=Path, default=appdata_install_dir())
    parser.add_argument("--no-shortcuts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_zip = resource_path(PAYLOAD_NAME)
    try:
        install_dir = validate_install_dir(args.install_dir)
        if args.dry_run:
            if not payload_zip.exists():
                raise FileNotFoundError(f"Installer payload not found: {payload_zip}")
            print(f"Payload: {payload_zip}")
            print(f"Install directory: {install_dir}")
            print(f"Shortcuts: {'no' if args.no_shortcuts else 'yes'}")
            return 0

        app_exe = install(install_dir, create_shortcuts=not args.no_shortcuts)
    except Exception as exc:
        if args.quiet:
            print(f"{APP_NAME} setup failed: {exc}")
        else:
            message_box(f"{APP_NAME} Setup Failed", str(exc), error=True)
        return 1

    shortcut_message = (
        "Desktop and Start menu shortcuts have been created."
        if not args.no_shortcuts
        else "Shortcuts were not created."
    )
    if args.quiet:
        print(f"Installation complete: {app_exe}")
    else:
        message_box(
            f"{APP_NAME} Setup",
            f"Installation complete.\n\nInstalled app:\n{app_exe}\n\n{shortcut_message}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
