from __future__ import annotations

import importlib.util
import subprocess
import sys


PACKAGES = [
    ("PySide6", "PySide6"),
    ("openpyxl", "openpyxl"),
    ("python-docx", "docx"),
    ("PyMuPDF", "fitz"),
    ("pytesseract", "pytesseract"),
    ("Pillow", "PIL"),
]


def print_header(title: str) -> None:
    print()
    print(f"== {title} ==")


def command_output(command: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        return False, str(exc)
    output = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, output


def main() -> int:
    print_header("Python")
    print(f"executable: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")

    print_header("pip")
    ok, output = command_output([sys.executable, "-m", "pip", "--version"])
    print(f"available: {'yes' if ok else 'no'}")
    print(f"detail: {output}")

    print_header("Packages")
    missing = []
    for label, module_name in PACKAGES:
        found = importlib.util.find_spec(module_name) is not None
        print(f"{label}: {'OK' if found else 'MISSING'}")
        if not found:
            missing.append(label)

    print_header("PyInstaller")
    ok, output = command_output([sys.executable, "-m", "PyInstaller", "--version"])
    print(f"available: {'yes' if ok else 'no'}")
    print(f"detail: {output}")
    if not ok:
        missing.append("PyInstaller")

    print()
    if missing:
        print("Result: environment is incomplete.")
        print("Missing or unavailable:", ", ".join(missing))
        print("Run: .venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt")
        return 1

    print("Result: environment looks ready for tests and PyInstaller build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
