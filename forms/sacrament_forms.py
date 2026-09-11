from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
)
from PyQt6.QtCore import Qt

from core.constants import C
from ui.ui_helpers import fv, mk_btn, mk_entry, mk_date, mk_combo, vbox_field, ge


class _SpousePicker(QWidget):
    """Typeahead member search for the spouse field in WeddingForm.

    Selecting a member links their member_id and locks the name field.
    '연결 해제' unlinks and lets the clerk type a free-text name instead.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.member_id = None

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)

        search_row = QHBoxLayout(); search_row.setContentsMargins(0, 0, 0, 0); search_row.setSpacing(6)
        self.search_e = mk_entry()
        self.search_e.setPlaceholderText("배우자 검색 (이름/세례명) — 없으면 이름 직접 입력")
        self.unlink_btn = mk_btn("연결 해제", "btn_muted")
        self.unlink_btn.setFixedWidth(76); self.unlink_btn.setVisible(False)
        search_row.addWidget(self.search_e, 1); search_row.addWidget(self.unlink_btn)
        lay.addLayout(search_row)

        self.results = QListWidget(); self.results.setFixedHeight(72)
        self.results.setVisible(False)
        lay.addWidget(self.results)

        self.linked_lbl = QLabel()
        self.linked_lbl.setStyleSheet(f"color:{C['success']};font-weight:bold;background:transparent;")
        self.linked_lbl.setVisible(False)
        lay.addWidget(self.linked_lbl)

        self.name_e = mk_entry()
        self.name_e.setPlaceholderText("배우자 이름 *")
        lay.addWidget(self.name_e)

        self.search_e.textChanged.connect(self._on_search)
        self.results.itemClicked.connect(self._on_select)
        self.unlink_btn.clicked.connect(self._unlink)

    def _on_search(self, text):
        if not text.strip():
            self.results.setVisible(False); return
        rows = self.db.search_people(text.strip(), limit=8)
        self.results.clear()
        if rows:
            for r in rows:
                label = f"{fv(r,'name')}  {fv(r,'baptismal_name')}  [{fv(r,'display_id')}]"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, (r["member_id"], fv(r, "name")))
                self.results.addItem(item)
            self.results.setVisible(True)
        else:
            self.results.setVisible(False)

    def _on_select(self, item):
        mid, name = item.data(Qt.ItemDataRole.UserRole)
        self.member_id = mid
        self.linked_lbl.setText(f"✓  {name}  [ID {mid}]")
        self.linked_lbl.setVisible(True)
        self.results.setVisible(False); self.search_e.clear()
        self.unlink_btn.setVisible(True)
        self.name_e.setText(name); self.name_e.setEnabled(False)

    def _unlink(self):
        self.member_id = None
        self.linked_lbl.setVisible(False)
        self.unlink_btn.setVisible(False)
        self.name_e.setEnabled(True)

    def get_name(self):
        return self.name_e.text().strip()


class BaptismForm(QDialog):
    """Quick-entry dialog for a single baptism record."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("세례 기록 추가"); self.resize(460, 160); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        member = db.get(pno)
        fv_ = lambda k: str(member[k]).strip() if member and member[k] else ""

        self.date_e   = add("세례일(MM/DD/YYYY)",      mk_date(), 0, 0)
        self.dioc_e   = add("교구",        mk_entry(), 0, 1)
        self.church_e = add("세례 성당",   mk_entry(), 0, 2)
        self.bname_e  = add("세례명",      mk_entry(fv_("baptismal_name")), 1, 0)
        self.off_e    = add("집전자",      mk_entry(), 1, 1)
        self.off_bn_e = add("집전자 세례명", mk_entry(), 1, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            bname = ge(self.bname_e) or None
            if bname:
                self.db.update(self.pno, {"baptismal_name": bname})
            self.db.create_baptism(dict(
                member_id=self.pno,
                is_adp=0,
                date=ge(self.date_e),
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e),
                officiant_name=ge(self.off_e),
                officiant_name_bapt=ge(self.off_bn_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class ConfirmationForm(QDialog):
    """Quick-entry dialog for a single confirmation record."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("견진 기록 추가"); self.resize(460, 160); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e   = add("견진일(MM/DD/YYYY)",      mk_date(), 0, 0)
        self.dioc_e   = add("교구",        mk_entry(), 0, 1)
        self.church_e = add("견진 성당",   mk_entry(), 0, 2)
        self.off_e    = add("집전자",      mk_entry(), 1, 0)
        self.cname_e  = add("견진명",      mk_entry(), 1, 1, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_confirmation_record(dict(
                member_id=self.pno,
                is_adp=0,
                date=ge(self.date_e),
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e),
                officiant_name=ge(self.off_e),
                confirmation_name=ge(self.cname_e) or None,
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class CommunionForm(QDialog):
    """Quick-entry dialog for a first-communion record."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("첫영성체 기록 추가"); self.resize(460, 160); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e   = add("첫영성체일(MM/DD/YYYY)", mk_date(), 0, 0)
        self.church_e = add("성당",      mk_entry(), 0, 1, 2)
        self.dioc_e   = add("교구",      mk_entry(), 1, 0)
        self.off_e    = add("집전자",    mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_communion_record(dict(
                member_id=self.pno,
                is_adp=0,
                date=ge(self.date_e) or None,
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e) or None,
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class WeddingForm(QDialog):
    """Wedding record dialog; spouse can be searched from existing members or entered as free text."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.name = name; self.on_save = on_save
        self.setWindowTitle("혼인 기록 추가"); self.setMinimumWidth(560); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        bl = QVBoxLayout(body); bl.setContentsMargins(16, 12, 16, 12); bl.setSpacing(10)
        outer.addWidget(body, 1)

        g = QGridLayout(); g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e  = add("혼인일(MM/DD/YYYY)", mk_date(), 0, 0)
        self.type_cb = add("형태", mk_combo(["성사혼", "관면혼", "단순유효화혼", "바오로특전혼", "근본유효화혼", "기타"]), 0, 1, 2)
        self.role_cb = add("역할", mk_combo(["신랑", "신부"]), 1, 0)
        self.off_e   = add("집전자", mk_entry(), 1, 1, 3)
        bl.addLayout(g)

        # '기타' type free-text row
        self._type_other_row = QWidget(); self._type_other_row.setObjectName("card")
        tol = QHBoxLayout(self._type_other_row); tol.setContentsMargins(0, 0, 0, 0)
        self.type_other_e = mk_entry(); self.type_other_e.setPlaceholderText("혼인 형태를 직접 입력하세요")
        tol.addWidget(vbox_field("형태 직접입력", self.type_other_e, C['card']))
        self._type_other_row.setVisible(False)
        self.type_cb.currentTextChanged.connect(
            lambda t: (self._type_other_row.setVisible(t == "기타"), self.adjustSize()))
        bl.addWidget(self._type_other_row)

        # Spouse picker (search existing member or free-text)
        self.spouse = _SpousePicker(db)
        bl.addWidget(self.spouse)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not self.spouse.get_name():
            QMessageBox.warning(self, "오류", "배우자 이름을 입력하세요.")
            return
        try:
            is_groom = ge(self.role_cb) == "신랑"
            wtype = ge(self.type_cb)
            data = dict(
                date=ge(self.date_e) or None,
                wedding_type=wtype,
                officiant_name=ge(self.off_e) or None,
            )
            if wtype == "기타":
                data["type_other"] = ge(self.type_other_e) or None
            if is_groom:
                data["groom_id"]   = self.pno
                data["groom_name"] = self.name
                data["bride_id"]   = self.spouse.member_id
                data["bride_name"] = self.spouse.get_name()
            else:
                data["bride_id"]   = self.pno
                data["bride_name"] = self.name
                data["groom_id"]   = self.spouse.member_id
                data["groom_name"] = self.spouse.get_name()
            self.db.create_wedding_record(data)
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class DeathForm(QDialog):
    """Death record intake: shows member info (read-only), then collects death date,
    cemetery address, last-rites date, a family contact name, and current address."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("사망 기록 추가"); self.resize(600, 360); self.setModal(True)

        from PyQt6.QtWidgets import QScrollArea, QFrame
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(); body.setObjectName("card")
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        from ui.ui_helpers import shdr
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        member = db.get(pno)
        fv_ = lambda k: str(member[k]).strip() if member and member[k] else ""

        # ── 고인 정보 (pre-filled from member record; editable) ───────────────
        r = 0
        g.addWidget(shdr("✟  고인 정보"), r, 0, 1, 4); r += 1
        self.name_e    = add("이름",    mk_entry(fv_("name")),            r, 0)
        self.bname_e   = add("세례명",  mk_entry(fv_("baptismal_name")),  r, 1)
        self.birth_e   = add("생년월일(MM/DD/YYYY)", mk_entry(fv_("birth_date")),     r, 2); r += 1
        self.cur_addr_e = add("현 주소", mk_entry(fv_("address")),        r, 0, 4); r += 1

        # ── 사망 정보 ────────────────────────────────────────────────────────
        g.addWidget(shdr("📋  사망 정보"), r, 0, 1, 4); r += 1
        self.date_e   = add("사망일(MM/DD/YYYY)",       mk_date(), r, 0)
        self.family_e = add("유족 (연락 가족)", mk_entry(), r, 1, 2); r += 1
        self.cemetery_e = add("묘지 주소",  mk_entry(), r, 0, 4); r += 1
        self.rites_e  = add("병자성사일(MM/DD/YYYY)",   mk_date(), r, 0, 2); r += 1

        g.setRowStretch(r, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.date_e):
            QMessageBox.warning(self, "오류", "사망일을 입력하세요.")
            return
        try:
            # Write back any edits to the member record
            self.db.update(self.pno, dict(
                name=ge(self.name_e),
                baptismal_name=ge(self.bname_e) or None,
                birth_date=ge(self.birth_e) or None,
                address=ge(self.cur_addr_e) or None,
            ))
            self.db.create_death_record(dict(
                member_id=self.pno,
                date_death=ge(self.date_e) or None,
                cemetery=ge(self.cemetery_e) or None,
                last_rites_date=ge(self.rites_e) or None,
                family_name=ge(self.family_e) or None,
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class MoveInForm(QDialog):
    """Dialog for recording a move-in event (former diocese and parish)."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("전입 기록 추가"); self.resize(480, 220); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e    = add("전입일(MM/DD/YYYY)", mk_date(), 0, 0)
        self.diocese_e = add("이전 교구",           mk_entry(), 0, 1)
        self.parish_e  = add("이전 성당",           mk_entry(), 0, 2)
        self.addr_e    = add("이전 성당 주소",       mk_entry(), 1, 0, 3)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.date_e):
            QMessageBox.warning(self, "오류", "전입일을 입력하세요.")
            return
        try:
            self.db.create_movein_record(dict(
                member_id=self.pno,
                date=ge(self.date_e),
                former_diocese=ge(self.diocese_e),
                former_parish=ge(self.parish_e),
                former_address=ge(self.addr_e) or None,
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class MoveOutForm(QDialog):
    """Dialog for recording a move-out event (destination diocese and parish)."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("전출 기록 추가"); self.resize(480, 220); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e    = add("전출일(MM/DD/YYYY)", mk_date(), 0, 0)
        self.diocese_e = add("새 교구",             mk_entry(), 0, 1)
        self.parish_e  = add("새 성당",             mk_entry(), 0, 2)
        self.addr_e    = add("새 성당 주소",         mk_entry(), 1, 0, 3)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.date_e):
            QMessageBox.warning(self, "오류", "전출일을 입력하세요.")
            return
        try:
            self.db.create_moveout_record(dict(
                member_id=self.pno,
                date=ge(self.date_e),
                dest_diocese=ge(self.diocese_e),
                dest_parish=ge(self.parish_e),
                dest_address=ge(self.addr_e) or None,
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
