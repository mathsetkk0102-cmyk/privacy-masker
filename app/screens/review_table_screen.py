from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import DetectionItem


class ReviewTableScreen(QWidget):
    back_requested = Signal()
    next_requested = Signal(list)

    HEADERS = ["선택", "파일명", "위치", "개인정보 유형", "원문", "마스킹 결과", "상태", "신뢰도"]
    ORIGINAL_TEXT_COLUMN = 4
    MASKED_TEXT_COLUMN = 5
    STATUS_COLUMN = 6

    def __init__(self) -> None:
        super().__init__()
        self.items: list[DetectionItem] = []
        self.row_to_item_id: dict[int, str] = {}
        self.loading = False
        self.original_text_hidden = False

        title = QLabel("탐지 결과 검토 및 수정")
        title.setObjectName("PageTitle")
        warning = QLabel("검토 화면에는 개인정보 원문이 표시됩니다. 화면 공유나 캡처에 주의하세요.")
        warning.setObjectName("WarningBanner")

        self.status_filter = QComboBox()
        self.status_filter.addItems(["전체 보기", "확인 필요만 보기"])
        self.status_filter.currentIndexChanged.connect(self.apply_filter)

        select_all_button = QPushButton("전체 선택")
        select_all_button.setObjectName("UtilityButton")
        select_all_button.clicked.connect(lambda: self.set_all_checked(True))

        select_names_button = QPushButton("이름 후보 선택")
        select_names_button.setObjectName("UtilityButton")
        select_names_button.clicked.connect(lambda: self.set_pii_type_checked("이름", True))

        self.original_text_button = QPushButton("원문 숨기기")
        self.original_text_button.setObjectName("UtilityButton")
        self.original_text_button.clicked.connect(self.toggle_original_text_visibility)

        clear_button = QPushButton("전체 해제")
        clear_button.setObjectName("UtilityButton")
        clear_button.clicked.connect(lambda: self.set_all_checked(False))

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("ReviewTable")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(0, 68)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 240)
        self.table.setColumnWidth(5, 240)
        self.table.itemChanged.connect(self.handle_item_changed)

        back_button = QPushButton("이전")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self.back_requested.emit)

        next_button = QPushButton("저장 단계로 이동")
        next_button.setObjectName("PrimaryButton")
        next_button.clicked.connect(self.emit_next)

        filter_row = QHBoxLayout()
        filter_row.addWidget(select_all_button)
        filter_row.addWidget(select_names_button)
        filter_row.addWidget(clear_button)
        filter_row.addWidget(self.original_text_button)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()

        nav_row = QHBoxLayout()
        nav_row.addWidget(back_button)
        nav_row.addStretch()
        nav_row.addWidget(next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(warning)
        layout.addLayout(filter_row)
        layout.addWidget(self.table, 1)
        layout.addLayout(nav_row)

    def load_items(self, items: list[DetectionItem]) -> None:
        self.loading = True
        self.items = items
        self.row_to_item_id = {}
        self.original_text_hidden = False
        self.original_text_button.setText("원문 숨기기")
        self.table.setRowCount(0)

        for item in self.items:
            row = self.table.rowCount()
            self.row_to_item_id[row] = item.id
            self.table.insertRow(row)

            checkbox = QCheckBox()
            checkbox.setChecked(item.selected)
            checkbox.stateChanged.connect(lambda _state, item_id=item.id: self.handle_checkbox_changed(item_id))
            self.table.setCellWidget(row, 0, checkbox)

            values = [
                item.file_name,
                item.location,
                item.pii_type,
                item.original_text,
                item.masked_text,
                item.review_status,
                item.confidence,
            ]
            for column, value in enumerate(values, start=1):
                table_item = QTableWidgetItem(value)
                if item.note:
                    table_item.setToolTip(item.note)
                if column == self.MASKED_TEXT_COLUMN:
                    table_item.setFlags(table_item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, table_item)

        self.loading = False
        self.apply_filter()

    def collect_items(self) -> list[DetectionItem]:
        self.sync_all_rows()
        return self.items

    def handle_checkbox_changed(self, item_id: str) -> None:
        if self.loading:
            return
        item = self.find_item(item_id)
        row = self.find_row(item_id)
        if item is None or row is None:
            return
        checkbox = self.table.cellWidget(row, 0)
        if isinstance(checkbox, QCheckBox):
            item.selected = checkbox.isChecked()

    def handle_item_changed(self, table_item: QTableWidgetItem) -> None:
        if self.loading or table_item.column() != self.MASKED_TEXT_COLUMN:
            return
        item_id = self.row_to_item_id.get(table_item.row())
        item = self.find_item(item_id)
        if item is not None:
            item.masked_text = table_item.text()

    def set_all_checked(self, checked: bool) -> None:
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            checkbox = self.table.cellWidget(row, 0)
            item_id = self.row_to_item_id.get(row)
            item = self.find_item(item_id)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(checked)
            if item is not None:
                item.selected = checked

    def set_pii_type_checked(self, pii_type: str, checked: bool) -> None:
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            item_id = self.row_to_item_id.get(row)
            item = self.find_item(item_id)
            if item is None or item.pii_type != pii_type:
                continue
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(checked)
            item.selected = checked

    def toggle_original_text_visibility(self) -> None:
        self.set_original_text_hidden(not self.original_text_hidden)

    def set_original_text_hidden(self, hidden: bool) -> None:
        self.original_text_hidden = hidden
        self.original_text_button.setText("원문 표시하기" if hidden else "원문 숨기기")

        for row in range(self.table.rowCount()):
            item_id = self.row_to_item_id.get(row)
            item = self.find_item(item_id)
            table_item = self.table.item(row, self.ORIGINAL_TEXT_COLUMN)
            if item is None or table_item is None:
                continue
            table_item.setText("********" if hidden else item.original_text)

    def apply_filter(self) -> None:
        needs_review_only = self.status_filter.currentText() == "확인 필요만 보기"
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, self.STATUS_COLUMN)
            hide = needs_review_only and status_item is not None and status_item.text() != "확인 필요"
            self.table.setRowHidden(row, hide)

    def emit_next(self) -> None:
        self.next_requested.emit(self.collect_items())

    def clear(self) -> None:
        self.items = []
        self.row_to_item_id = {}
        self.table.setRowCount(0)

    def sync_all_rows(self) -> None:
        for row in range(self.table.rowCount()):
            item_id = self.row_to_item_id.get(row)
            item = self.find_item(item_id)
            if item is None:
                continue
            checkbox = self.table.cellWidget(row, 0)
            masked_item = self.table.item(row, self.MASKED_TEXT_COLUMN)
            if isinstance(checkbox, QCheckBox):
                item.selected = checkbox.isChecked()
            if masked_item is not None:
                item.masked_text = masked_item.text()

    def find_item(self, item_id: str | None) -> DetectionItem | None:
        if item_id is None:
            return None
        return next((item for item in self.items if item.id == item_id), None)

    def find_row(self, item_id: str) -> int | None:
        for row, mapped_id in self.row_to_item_id.items():
            if mapped_id == item_id:
                return row
        return None
