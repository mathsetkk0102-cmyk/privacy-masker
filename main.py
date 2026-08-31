import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.main_window import MainWindow
from core.file_utils import resource_path


def load_stylesheet() -> str:
    style_path = resource_path("ui/styles.qss")
    if not style_path.exists():
        return ""
    return style_path.read_text(encoding="utf-8")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("개인정보 마스킹 도구")
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "실행 오류",
            f"프로그램을 시작하는 중 오류가 발생했습니다.\n\n원인: {exc}\n\n"
            "압축을 해제한 폴더에서 실행했는지, 필요한 파일이 함께 있는지 확인하세요.",
        )
        raise
