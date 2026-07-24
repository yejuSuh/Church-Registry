from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QInputDialog,
)
from PyQt6.QtCore import Qt

from core.constants import C, HOUSEHOLD_RELATIONS
from ui.ui_helpers import fv, mk_btn, shdr


class _MemberSearchDialog(QDialog):
    """Search for an existing registered member to add to a household."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.selected_member_id = None
        self.setWindowTitle("교인 검색")
        self.resize(460, 340)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        self.q_e = QLineEdit()
        self.q_e.setPlaceholderText("이름 또는 세례명 입력...")
        self.q_e.textChanged.connect(self._search)
        lay.addWidget(self.q_e)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["교적번호", "이름", "세례명"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.itemDoubleClicked.connect(self._select)
        lay.addWidget(self.tbl, 1)

        bb = QHBoxLayout()
        bb.addStretch()
        cancel = mk_btn("취소", "btn_muted")
        ok = mk_btn("선택", "btn_accent")
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self._select)
        bb.addWidget(cancel)
        bb.addWidget(ok)
        lay.addLayout(bb)

    def _search(self, q):
        results = self.db.search_people(q, limit=20)
        self.tbl.setRowCount(len(results))
        for i, r in enumerate(results):
            self.tbl.setItem(i, 0, QTableWidgetItem(str(r["display_id"] or "")))
            self.tbl.setItem(i, 1, QTableWidgetItem(str(r["name"] or "")))
            self.tbl.setItem(i, 2, QTableWidgetItem(str(r["baptismal_name"] or "")))
            self.tbl.item(i, 0).setData(Qt.ItemDataRole.UserRole, r["member_id"])

    def _select(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "선택", "교인을 선택하세요.")
            return
        self.selected_member_id = self.tbl.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()


class _HouseholdSearchDialog(QDialog):
    """Search for an existing household to join (by 세대주 name)."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.selected_household_id = None
        self.setWindowTitle("세대 검색")
        self.resize(460, 320)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        lay.addWidget(shdr("🔍  세대주 이름으로 검색"))

        self.q_e = QLineEdit()
        self.q_e.setPlaceholderText("세대주 이름 또는 세례명 입력...")
        self.q_e.textChanged.connect(self._search)
        lay.addWidget(self.q_e)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["교적번호", "세대주", "세례명"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.itemDoubleClicked.connect(self._select)
        lay.addWidget(self.tbl, 1)

        bb = QHBoxLayout()
        bb.addStretch()
        cancel = mk_btn("취소", "btn_muted")
        ok = mk_btn("선택", "btn_accent")
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self._select)
        bb.addWidget(cancel)
        bb.addWidget(ok)
        lay.addLayout(bb)

    def _search(self, q):
        results = self.db.search_households(q)
        self.tbl.setRowCount(len(results))
        for i, r in enumerate(results):
            self.tbl.setItem(i, 0, QTableWidgetItem(str(r["head_display_id"] or "")))
            self.tbl.setItem(i, 1, QTableWidgetItem(str(r["head_name"] or "")))
            self.tbl.setItem(i, 2, QTableWidgetItem(str(r["head_bapt"] or "")))
            self.tbl.item(i, 0).setData(Qt.ItemDataRole.UserRole, r["household_id"])

    def _select(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "선택", "세대를 선택하세요.")
            return
        self.selected_household_id = self.tbl.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()


class HouseholdDialog(QDialog):
    """Household (세대) management dialog.

    Shows the current household of a member, lists all co-members,
    and provides actions: join, leave, change head, add/remove members.
    """

    def __init__(self, parent, db, member_id, on_change=None):
        super().__init__(parent)
        self.db = db
        self.member_id = int(member_id)
        self.on_change = on_change
        self.setWindowTitle("세대 관리")
        self.resize(540, 480)
        self.setModal(True)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)

        self._build()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build(self):
        while self._lay.count():
            it = self._lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        p = self.db.get(self.member_id)
        if not p:
            self._lay.addWidget(QLabel("교인 정보를 찾을 수 없습니다."))
            return

        household_id = p["household_id"] if p else None

        hdr = QWidget(); hdr.setObjectName("detail_hdr"); hdr.setFixedHeight(50)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 8, 16, 8)
        name_lbl = QLabel(f"{fv(p, 'name')}  —  세대 관리")
        name_lbl.setStyleSheet("font-size:14px;font-weight:bold;")
        hl.addWidget(name_lbl); hl.addStretch()
        self._lay.addWidget(hdr)

        body = QWidget(); body.setObjectName("card")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(10)
        self._lay.addWidget(body, 1)

        if household_id:
            self._build_with_household(body_lay, p, household_id)
        else:
            self._build_no_household(body_lay)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(50)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        close_btn = mk_btn("닫기", "btn_muted")
        close_btn.clicked.connect(self.accept)
        bbl.addWidget(close_btn)
        self._lay.addWidget(bb)

    def _build_with_household(self, lay, p, household_id):
        head_name = fv(p, "head_of_household") or "—"
        is_head = bool(p["is_head"])

        status_lbl = QLabel(f"🏠  세대주:  {head_name}")
        status_lbl.setObjectName("fv")
        lay.addWidget(status_lbl)

        members = self.db.get_household_members(household_id)
        self.tbl = QTableWidget(len(members), 4)
        self.tbl.setHorizontalHeaderLabels(["이름", "세례명", "관계", "교적번호"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setStyleSheet(
            "QHeaderView::section{"
            f"background:transparent;color:{C['muted']};"
            "font-size:11px;font-weight:normal;"
            f"border:none;border-bottom:1px solid {C['border']};padding:2px 6px;}}"
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl_h = min(220, 34 + len(members) * 28)
        self.tbl.setFixedHeight(tbl_h)

        for i, m in enumerate(members):
            name_txt = str(m["name"] or "").strip()
            if m["is_head"]:
                name_txt += "  ★"
            self.tbl.setItem(i, 0, QTableWidgetItem(name_txt))
            self.tbl.setItem(i, 1, QTableWidgetItem(str(m["baptismal_name"] or "").strip()))
            self.tbl.setItem(i, 2, QTableWidgetItem(str(m["relation"] or "").strip()))
            self.tbl.setItem(i, 3, QTableWidgetItem(str(m["display_id"] or "").strip()))
            self.tbl.item(i, 0).setData(Qt.ItemDataRole.UserRole, m["member_id"])
            self.tbl.item(i, 0).setData(Qt.ItemDataRole.UserRole + 1, bool(m["is_head"]))
        lay.addWidget(self.tbl)

        # Per-member actions
        mab = QWidget()
        mabl = QHBoxLayout(mab); mabl.setContentsMargins(0, 0, 0, 0); mabl.setSpacing(6)
        rel_btn  = mk_btn("관계 변경", "btn_muted")
        head_btn = mk_btn("세대주로 지정", "btn_muted")
        rm_btn   = mk_btn("제거", "btn_danger")
        rel_btn.clicked.connect(lambda: self._change_relation(household_id))
        head_btn.clicked.connect(lambda: self._change_head(household_id))
        rm_btn.clicked.connect(lambda: self._remove_member(household_id))
        mabl.addWidget(rel_btn); mabl.addWidget(head_btn); mabl.addWidget(rm_btn)
        mabl.addStretch()
        lay.addWidget(mab)

        div = QWidget(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{C['border']};")
        lay.addWidget(div)

        # Household-level actions
        add_mem_btn = mk_btn("+ 기존 교인 추가", "btn_success")
        add_new_btn = mk_btn("+ 새 가족 등록", "btn_success")
        leave_btn   = mk_btn("세대 분리", "btn_danger")
        add_mem_btn.clicked.connect(lambda: self._add_existing(household_id))
        add_new_btn.clicked.connect(lambda: self._add_new(household_id))
        leave_btn.clicked.connect(self._leave_household)
        if is_head:
            leave_btn.setEnabled(False)
            leave_btn.setToolTip("세대주는 분리할 수 없습니다. 먼저 세대주를 변경하세요.")

        hb = QHBoxLayout()
        hb.addWidget(add_mem_btn); hb.addWidget(add_new_btn)
        hb.addStretch(); hb.addWidget(leave_btn)
        lay.addLayout(hb)
        lay.addStretch()

    def _build_no_household(self, lay):
        info = QLabel("이 교인은 아직 세대에 속해 있지 않습니다.")
        info.setObjectName("mu")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addStretch()
        lay.addWidget(info)
        lay.addSpacing(12)

        create_btn = mk_btn("🏠  새 세대 만들기  (본인이 세대주)", "btn_accent")
        join_btn   = mk_btn("🔍  기존 세대에 합류", "btn_success")
        create_btn.clicked.connect(self._create_household)
        join_btn.clicked.connect(self._join_existing)
        lay.addWidget(create_btn)
        lay.addWidget(join_btn)
        lay.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh(self):
        if self.on_change:
            self.on_change()
        self._build()

    def _selected_row_data(self):
        """Returns (member_id, is_head) for the currently selected table row,
        or (None, False) when nothing is selected."""
        row = self.tbl.currentRow()
        if row < 0:
            return None, False
        item = self.tbl.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole), item.data(Qt.ItemDataRole.UserRole + 1)

    def _pick_relation(self, current=""):
        idx = HOUSEHOLD_RELATIONS.index(current) if current in HOUSEHOLD_RELATIONS else 0
        rel, ok = QInputDialog.getItem(
            self, "관계 선택", "이 교인의 관계:", HOUSEHOLD_RELATIONS, idx, False
        )
        return rel if ok else None

    # ── Actions ───────────────────────────────────────────────────────────────

    def _change_relation(self, household_id):
        mid, _ = self._selected_row_data()
        if mid is None:
            QMessageBox.warning(self, "선택", "구성원을 선택하세요."); return
        members = self.db.get_household_members(household_id)
        current_rel = next((m["relation"] or "" for m in members if m["member_id"] == mid), "")
        rel = self._pick_relation(current_rel)
        if rel is None:
            return
        self.db.join_household(mid, household_id, rel)
        self._refresh()

    def _change_head(self, household_id):
        mid, is_head = self._selected_row_data()
        if mid is None:
            QMessageBox.warning(self, "선택", "구성원을 선택하세요."); return
        if is_head:
            QMessageBox.information(self, "세대주", "이미 세대주입니다."); return
        self.db.set_household_head(household_id, mid)
        self._refresh()

    def _remove_member(self, household_id):
        mid, is_head = self._selected_row_data()
        if mid is None:
            QMessageBox.warning(self, "선택", "구성원을 선택하세요."); return
        if is_head:
            QMessageBox.warning(self, "세대주", "세대주는 제거할 수 없습니다. 먼저 세대주를 변경하세요.")
            return
        if QMessageBox.question(
            self, "구성원 제거", "선택한 구성원을 세대에서 제거하시겠습니까?"
        ) != QMessageBox.StandardButton.Yes:
            return
        self.db.leave_household(mid)
        self._refresh()

    def _add_existing(self, household_id):
        dlg = _MemberSearchDialog(self, self.db)
        if dlg.exec() != QDialog.DialogCode.Accepted or dlg.selected_member_id is None:
            return
        rel = self._pick_relation("기타")
        if rel is None:
            return
        self.db.join_household(dlg.selected_member_id, household_id, rel)
        self._refresh()

    def _add_new(self, household_id):
        from forms.parishioner_form import ParishionerForm
        p = self.db.get(self.member_id)
        area = fv(p, "reg_area") if p else ""
        form = ParishionerForm(self, self.db, prefill_area=area)
        if form.exec() == QDialog.DialogCode.Accepted:
            new_mid = getattr(form, "_last_created_mid", None)
            if new_mid:
                rel = self._pick_relation("자녀")
                if rel is not None:
                    self.db.join_household(new_mid, household_id, rel)
        self._refresh()

    def _leave_household(self):
        if QMessageBox.question(
            self, "세대 분리", "이 교인을 세대에서 분리하시겠습니까?"
        ) != QMessageBox.StandardButton.Yes:
            return
        self.db.leave_household(self.member_id)
        self._refresh()

    def _create_household(self):
        self.db.create_household(self.member_id)
        self._refresh()

    def _join_existing(self):
        dlg = _HouseholdSearchDialog(self, self.db)
        if dlg.exec() != QDialog.DialogCode.Accepted or dlg.selected_household_id is None:
            return
        rel = self._pick_relation("기타")
        if rel is None:
            return
        self.db.join_household(self.member_id, dlg.selected_household_id, rel)
        self._refresh()
