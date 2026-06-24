from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from constants import C, AREA_DISP
from ui_helpers import mk_btn
from export_dialog import ExportDialog


class ListView(QWidget):
    row_selected = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._rows = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        tb = QWidget(); tb.setObjectName("toolbar"); tb.setFixedHeight(52)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(14, 8, 14, 8)
        tl = QLabel("교적 목록")
        tl.setStyleSheet(f"font-size:15px;font-weight:bold;color:{C['text']};background:transparent;")
        self.export_btn = mk_btn("⬇  내보내기", "btn_muted")
        self.add_btn    = mk_btn("+ 새 교적",   "btn_accent")
        self.export_btn.clicked.connect(lambda: ExportDialog(self, self._rows).exec())
        tbl.addWidget(tl); tbl.addStretch()
        tbl.addWidget(self.export_btn); tbl.addWidget(self.add_btn)
        lay.addWidget(tb)

        fb = QWidget(); fb.setObjectName("filterbar"); fb.setFixedHeight(48)
        fbl = QHBoxLayout(fb); fbl.setContentsMargins(10, 6, 10, 6); fbl.setSpacing(8)
        self.q_le = QLineEdit()
        self.q_le.setPlaceholderText("🔍  이름 / 세례명 / 교적번호 / 세대주")
        self.q_le.setFixedWidth(280)
        self.area_cb = QComboBox()
        self.area_cb.addItem("전체 구역")
        self.area_cb.addItems(AREA_DISP)
        self.area_cb.setFixedWidth(180)
        self.cnt_lbl = QLabel(""); self.cnt_lbl.setObjectName("mu")
        fbl.addWidget(self.q_le); fbl.addWidget(self.area_cb)
        fbl.addStretch(); fbl.addWidget(self.cnt_lbl)
        lay.addWidget(fb)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["교적번호", "이름", "세례명", "구역", "세대주", "관계"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        for i, w in enumerate([130, 100, 120, 130, 100, 70]):
            self.table.setColumnWidth(i, w)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"alternate-background-color:{C['row_alt']};")
        lay.addWidget(self.table, 1)

        self.q_le.textChanged.connect(self.load)
        self.area_cb.currentIndexChanged.connect(self.load)
        self.table.itemSelectionChanged.connect(self._sel)

    def load(self):
        q = self.q_le.text()
        area_text = self.area_cb.currentText()
        if area_text and area_text != "전체 구역":
            parts = area_text.split(None, 1)
            district = parts[1].strip() if len(parts) > 1 else ""
        else:
            district = ""
        rows = self.db.search(q, district)
        self._rows = rows
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [
                r["member_id"],
                r["name"] or "",
                r["baptismal_name"] or "",
                r["district"] or "",
                r["head_of_household"] or "",
                r["relation"] or "",
            ]
            is_inactive = r["is_inactive"]
            for j, val in enumerate(vals):
                it = QTableWidgetItem(val)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if is_inactive:
                    it.setForeground(QColor(C["orange"]))
                self.table.setItem(i, j, it)
        self.cnt_lbl.setText(f"총 {len(rows)}명")

    def _sel(self):
        row = self.table.currentRow()
        if row >= 0:
            pno = self.table.item(row, 0)
            if pno:
                self.row_selected.emit(pno.text())
