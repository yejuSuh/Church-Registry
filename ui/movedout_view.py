from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.constants import C, AREA_DISP
from ui.ui_helpers import fv, mk_btn


class MovedOutView(QWidget):
    """List of members who have been marked as moved out (전출).
    Data is fully preserved; members can be reactivated from here."""

    reactivated = pyqtSignal()   # triggers a reload of the main member list

    _COLS = ["교적번호", "이름", "세례명", "구역"]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._rows = []

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────────────
        bar = QWidget(); bar.setObjectName("detail_hdr"); bar.setFixedHeight(52)
        bl = QHBoxLayout(bar); bl.setContentsMargins(16, 8, 16, 8); bl.setSpacing(10)
        title = QLabel("📤  전출 교적")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:white;background:transparent;")
        bl.addWidget(title)
        bl.addSpacing(16)
        self._q = QLineEdit(); self._q.setPlaceholderText("이름 / 세례명 검색")
        self._q.setFixedWidth(200)
        bl.addWidget(self._q)
        bl.addStretch()
        self._reactivate_btn = mk_btn("재등록", "btn_success")
        self._reactivate_btn.setEnabled(False)
        bl.addWidget(self._reactivate_btn)
        lay.addWidget(bar)

        # ── Table ─────────────────────────────────────────────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(len(self._COLS))
        self._tbl.setHorizontalHeaderLabels(self._COLS)
        self._tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.verticalHeader().setVisible(False)
        lay.addWidget(self._tbl, 1)

        self._q.textChanged.connect(self._load)
        self._tbl.itemSelectionChanged.connect(self._on_select)
        self._reactivate_btn.clicked.connect(self._reactivate)

    def showEvent(self, event):
        super().showEvent(event)
        self._load()

    def _load(self):
        q = self._q.text().strip()
        self._rows = self.db.search_movedout(q)
        self._tbl.setRowCount(len(self._rows))
        for r, p in enumerate(self._rows):
            district = fv(p, "district") or fv(p, "reg_area")
            for c, val in enumerate([
                fv(p, "display_id"),
                fv(p, "name"),
                fv(p, "baptismal_name"),
                district,
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._tbl.setItem(r, c, item)
        self._reactivate_btn.setEnabled(False)

        if not self._rows:
            self._tbl.setRowCount(1)
            placeholder = QTableWidgetItem("전출 처리된 교인이 없습니다")
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._tbl.setSpan(0, 0, 1, len(self._COLS))
            self._tbl.setItem(0, 0, placeholder)

    def _on_select(self):
        self._reactivate_btn.setEnabled(bool(self._tbl.selectedItems()))

    def _reactivate(self):
        row = self._tbl.currentRow()
        if row < 0 or row >= len(self._rows):
            return
        p = self._rows[row]
        name = fv(p, "name")
        if QMessageBox.question(
            self, "재등록 확인",
            f"'{name}' 교인을 활성 교적으로 재등록하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.reactivate_member(p["member_id"])
            self.reactivated.emit()
            self._load()
