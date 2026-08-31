from pathlib import Path
import sys

from core.file_utils import resource_path


def test_resource_path_finds_stylesheet_in_development() -> None:
    path = resource_path("ui/styles.qss")

    assert path.exists()
    assert path.name == "styles.qss"


def test_resource_path_uses_pyinstaller_meipass(monkeypatch, tmp_path: Path) -> None:
    bundled_style = tmp_path / "ui" / "styles.qss"
    bundled_style.parent.mkdir()
    bundled_style.write_text("/* bundled */", encoding="utf-8")

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert resource_path("ui/styles.qss") == bundled_style
