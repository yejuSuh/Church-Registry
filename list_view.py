from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox,
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
        self.del_cb  = QCheckBox("삭제된 교적 포함")
        self.cnt_lbl = QLabel(""); self.cnt_lbl.setObjectName("mu")
        fbl.addWidget(self.q_le); fbl.addWidget(self.area_cb); fbl.addWidget(self.del_cb)
        fbl.addStretch(); fbl.addWidget(self.cnt_lbl)
        lay.addWidget(fb)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["교적번호", "이름", "세례명", "관계", "세대주", "전화번호"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        for i, w in enumerate([130, 100, 120, 70, 100, 120]):
            self.table.setColumnWidth(i, w)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"alternate-background-color:{C['row_alt']};")
        lay.addWidget(self.table, 1)

        self.q_le.textChanged.connect(self.load)
        self.area_cb.currentIndexChanged.connect(self.load)
        self.del_cb.stateChanged.connect(self.load)
        self.table.itemSelectionChanged.connect(self._sel)

    def load(self):
        q    = self.q_le.text()
        area = self.area_cb.currentText()
        area = area.split()[0] if area and area != "전체 구역" else ""
        rows = self.db.search(q, area, self.del_cb.isChecked())
        self._rows = rows
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r["parishioner_no"], r["name"] or "", r["baptism_nm"] or "",
                    r["relation"] or "", r["host_nm"] or "", r["tel_home"] or ""]
            is_del = str(r["delete_flag"]).strip() == "Y"
            is_lap = str(r["lazy_flag"]).strip() == "Y"
            for j, val in enumerate(vals):
                it = QTableWidgetItem(val)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if is_del:
                    it.setForeground(QColor("#AAAAAA"))
                elif is_lap:
                    it.setForeground(QColor(C["orange"]))
                self.table.setItem(i, j, it)
        self.cnt_lbl.setText(f"총 {len(rows)}명")

    def _sel(self):
        row = self.table.currentRow()
        if row >= 0:
            pno = self.table.item(row, 0)
            if pno:
                self.row_selected.emit(pno.text())
