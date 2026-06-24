from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent
from PyQt6.QtGui import QColor, QPainterPath, QPen

from constants import C, AREA_DISP
from ui_helpers import mk_btn
from export_dialog import ExportDialog

_CB_SZ = 15   # checkbox size in px
_CB_RD = 3    # corner radius


def _draw_checkbox(painter, rect, checked: bool):
    """Draw a rounded checkbox centered in rect. Works for both header and cell painters."""
    cx = rect.x() + (rect.width()  - _CB_SZ) // 2
    cy = rect.y() + (rect.height() - _CB_SZ) // 2
    rf = QRectF(cx, cy, _CB_SZ, _CB_SZ)

    path = QPainterPath()
    path.addRoundedRect(rf, _CB_RD, _CB_RD)

    painter.save()
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    if checked:
        painter.fillPath(path, QColor(C['accent']))
        m = 3
        painter.setPen(QPen(QColor('#FFFFFF'), 1.8,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(cx + m,            cy + _CB_SZ // 2,
                         cx + _CB_SZ // 2 - 1, cy + _CB_SZ - m - 1)
        painter.drawLine(cx + _CB_SZ // 2 - 1, cy + _CB_SZ - m - 1,
                         cx + _CB_SZ - m,   cy + m)
    else:
        painter.fillPath(path, QColor('#FFFFFF'))
        painter.setPen(QPen(QColor(C['border']), 1.2))
        painter.drawPath(path)
    painter.restore()


class _RowCheckDelegate(QStyledItemDelegate):
    """Draws a custom rounded checkbox for the selection column (col 6)."""

    @staticmethod
    def _is_checked(raw):
        # data(CheckStateRole) can return int (C++ path) or Qt.CheckState enum (Python path)
        return raw == Qt.CheckState.Checked.value or raw == Qt.CheckState.Checked

    def paint(self, painter, option, index):
        painter.save()
        if option.state & option.state.__class__.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif index.row() % 2 == 1:
            painter.fillRect(option.rect, QColor(C['row_alt']))
        else:
            painter.fillRect(option.rect, QColor(C['card']))
        painter.restore()

        raw = index.data(Qt.ItemDataRole.CheckStateRole)
        _draw_checkbox(painter, option.rect, self._is_checked(raw))

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if index.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                cur = index.data(Qt.ItemDataRole.CheckStateRole)
                # Store as int so future retrievals stay consistent
                new_val = (Qt.CheckState.Unchecked.value
                           if self._is_checked(cur)
                           else Qt.CheckState.Checked.value)
                return model.setData(index, new_val, Qt.ItemDataRole.CheckStateRole)
        return False


class _CheckHeaderView(QHeaderView):
    """Header view that draws a checkbox in one designated column and emits allToggled on click."""
    allToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._check_col = -1
        self._checked = True
        self.setSectionsClickable(True)
        self.sectionClicked.connect(self._on_section_clicked)

    def _on_section_clicked(self, logical_index):
        if logical_index == self._check_col:
            self._checked = not self._checked
            self.viewport().update()
            self.allToggled.emit(self._checked)

    def enable_check(self, col):
        self._check_col = col
        self._checked = True
        self.viewport().update()

    def disable_check(self):
        self._check_col = -1
        self.viewport().update()

    def set_all_state(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.viewport().update()

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()
        if logical_index == self._check_col:
            _draw_checkbox(painter, rect, self._checked)


class ListView(QWidget):
    row_selected = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._rows = []
        self._export_mode = False
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── toolbar ──────────────────────────────────────────────────────────
        tb = QWidget(); tb.setObjectName("toolbar"); tb.setFixedHeight(52)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(14, 8, 14, 8); tbl.setSpacing(6)
        tl = QLabel("교적 목록")
        tl.setStyleSheet(f"font-size:15px;font-weight:bold;color:{C['text']};background:transparent;")

        self.export_btn  = mk_btn("⬇  내보내기",  "btn_muted")
        self.confirm_btn = mk_btn("내보내기 실행", "btn_accent")
        self.cancel_btn  = mk_btn("취소",          "btn_muted")
        self.add_btn     = mk_btn("+ 새 교적",     "btn_accent")

        self.export_btn.clicked.connect(self._enter_export_mode)
        self.confirm_btn.clicked.connect(self._do_export)
        self.cancel_btn.clicked.connect(self._exit_export_mode)

        self.confirm_btn.setVisible(False)
        self.cancel_btn.setVisible(False)

        tbl.addWidget(tl); tbl.addStretch()
        tbl.addWidget(self.export_btn)
        tbl.addWidget(self.confirm_btn)
        tbl.addWidget(self.cancel_btn)
        tbl.addWidget(self.add_btn)
        lay.addWidget(tb)

        # ── filter bar ───────────────────────────────────────────────────────
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

        # ── table ─────────────────────────────────────────────────────────────
        self._hdr = _CheckHeaderView()
        self.table = QTableWidget()
        self.table.setHorizontalHeader(self._hdr)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["교적번호", "이름", "세례명", "구역", "세대주", "관계"])
        self._hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._hdr.setStretchLastSection(True)
        for i, w in enumerate([130, 100, 120, 130, 100, 70]):
            self.table.setColumnWidth(i, w)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"alternate-background-color:{C['row_alt']};")
        self.table.setItemDelegateForColumn(6, _RowCheckDelegate(self.table))
        lay.addWidget(self.table, 1)

        self.q_le.textChanged.connect(self.load)
        self.area_cb.currentIndexChanged.connect(self.load)
        self.table.itemSelectionChanged.connect(self._sel)
        self.table.itemChanged.connect(self._on_item_changed)
        self._hdr.allToggled.connect(self._toggle_all_checks)

    # ── data loading ──────────────────────────────────────────────────────────

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

        if self._export_mode:
            self._set_check_items()

    def _sel(self):
        row = self.table.currentRow()
        if row >= 0:
            pno = self.table.item(row, 0)
            if pno:
                self.row_selected.emit(pno.text())

    # ── export mode ───────────────────────────────────────────────────────────

    def _enter_export_mode(self):
        self._export_mode = True
        # Add checkbox column
        self._hdr.setStretchLastSection(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderItem(6, QTableWidgetItem(""))
        self._hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 44)
        self._hdr.enable_check(6)
        self._set_check_items()
        # Swap buttons
        self.export_btn.setVisible(False)
        self.confirm_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.add_btn.setEnabled(False)

    def _exit_export_mode(self):
        self._export_mode = False
        self.table.blockSignals(True)
        self.table.setColumnCount(6)
        self.table.blockSignals(False)
        self._hdr.setStretchLastSection(True)
        self._hdr.disable_check()
        self.export_btn.setVisible(True)
        self.confirm_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.add_btn.setEnabled(True)

    def _set_check_items(self):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            it = QTableWidgetItem()
            it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked)
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 6, it)
        self.table.blockSignals(False)
        self._hdr.set_all_state(True)

    def _toggle_all_checks(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            it = self.table.item(i, 6)
            if it:
                it.setCheckState(state)
        self.table.blockSignals(False)
        self.table.viewport().update()

    def _on_item_changed(self, item):
        if not self._export_mode or item.column() != 6:
            return
        total = self.table.rowCount()
        checked = sum(
            1 for i in range(total)
            if (it := self.table.item(i, 6)) and it.checkState() == Qt.CheckState.Checked
        )
        self._hdr.set_all_state(checked == total)

    def _get_checked_rows(self):
        return [
            self._rows[i]
            for i in range(min(len(self._rows), self.table.rowCount()))
            if (it := self.table.item(i, 6)) and it.checkState() == Qt.CheckState.Checked
        ]

    def _do_export(self):
        rows = self._get_checked_rows()
        if not rows:
            QMessageBox.warning(self, "선택 없음", "내보낼 교적을 한 명 이상 선택하세요.")
            return
        ExportDialog(self, rows).exec()
