from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.validation_service import file_status


class FileSelectScreen(QWidget):
    next_requested = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.selected_files: list[str] = []

        title = QLabel("파일 선택")
        title.setObjectName("PageTitle")
        subtitle = QLabel("PDF, XLSX, DOCX, HWPX 파일을 여러 개 선택할 수 있습니다. HWP는 이번 MVP에서 안내만 제공합니다.")
        subtitle.setObjectName("MutedText")

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("FileList")
        self.list_widget.setAcceptDrops(False)

        add_button = QPushButton("파일 추가")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.pick_files)

        remove_button = QPushButton("선택 파일 제거")
        remove_button.setObjectName("SecondaryButton")
        remove_button.clicked.connect(self.remove_selected)

        next_button = QPushButton("다음")
        next_button.setObjectName("PrimaryButton")
        next_button.clicked.connect(self.emit_next)

        button_row = QHBoxLayout()
        button_row.addWidget(add_button)
        button_row.addWidget(remove_button)
        button_row.addStretch()
        button_row.addWidget(next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(button_row)

    def pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "처리할 파일 선택",
            "",
            "문서 파일 (*.pdf *.xlsx *.docx *.hwpx *.hwp);;모든 파일 (*.*)",
        )
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
        self.refresh_list()

    def remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.list_widget.selectedIndexes()}, reverse=True)
        for row in rows:
            del self.selected_files[row]
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for file in self.selected_files:
            path = Path(file)
            status = file_status(path)
            item = QListWidgetItem(f"{path.name}  |  {path.suffix.upper().lstrip('.')}  |  {status}")
            if status != "처리 가능":
                item.setForeground(Qt.GlobalColor.darkYellow)
            self.list_widget.addItem(item)

    def emit_next(self) -> None:
        self.next_requested.emit(self.selected_files)

    def reset(self) -> None:
        self.selected_files = []
        self.refresh_list()
