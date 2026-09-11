from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QMessageBox,
)

from core.constants import C
from ui.ui_helpers import mk_btn, mk_entry, mk_combo, vbox_field, ge


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

        self.date_e   = add("세례일 (YYYY/MM/DD)", mk_entry(), 0, 0)
        self.church_e = add("세례 성당",           mk_entry(), 0, 1, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0)
        self.off_bn_e = add("집전자 세례명",        mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_baptism(dict(
                member_id=self.pno,
                date=ge(self.date_e), parish=ge(self.church_e),
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

        self.date_e   = add("견진일 (YYYY/MM/DD)", mk_entry(), 0, 0)
        self.church_e = add("견진 성당",           mk_entry(), 0, 1, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0)
        self.cname_e  = add("견진명",              mk_entry(), 1, 1, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_confirmation_record(dict(
                member_id=self.pno,
                date=ge(self.date_e), parish=ge(self.church_e),
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

        self.date_e   = add("첫영성체일 (YYYY/MM/DD)", mk_entry(), 0, 0)
        self.church_e = add("성당",                    mk_entry(), 0, 1, 2)
        self.dioc_e   = add("교구",                    mk_entry(), 1, 0)
        self.off_e    = add("집전자",                  mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_communion_record(dict(
                member_id=self.pno,
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
    """Quick-entry dialog for a wedding record; supports '기타' type with free-text entry."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.name = name; self.on_save = on_save
        self.setWindowTitle("혼인 기록 추가"); self.setMinimumWidth(560); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e    = add("혼인일 (YYYY/MM/DD)", mk_entry(), 0, 0)
        self.type_cb   = add("형태",               mk_combo(["성사혼", "관면혼", "단순유효화혼", "바오로특전혼", "근본유효화혼", "기타"]), 0, 1, 2)
        self.role_cb   = add("역할",               mk_combo(["신랑", "신부"]), 1, 0)
        self.spouse_e  = add("배우자 이름",          mk_entry(), 1, 1)
        self.off_e     = add("집전자",              mk_entry(), 1, 2, 2)

        self._type_other_row = QWidget(); self._type_other_row.setObjectName("card")
        tol = QHBoxLayout(self._type_other_row); tol.setContentsMargins(16, 0, 16, 8)
        self.type_other_e = mk_entry(); self.type_other_e.setPlaceholderText("혼인 형태를 직접 입력하세요")
        tol.addWidget(vbox_field("형태 직접입력", self.type_other_e, C['card']))
        self._type_other_row.setVisible(False)
        def _on_type_change(t):
            self._type_other_row.setVisible(t == "기타")
            self.adjustSize()
        self.type_cb.currentTextChanged.connect(_on_type_change)
        outer.addWidget(self._type_other_row)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            is_groom = ge(self.role_cb) == "신랑"
            spouse = ge(self.spouse_e)
            wtype = ge(self.type_cb)
            data = dict(
                date=ge(self.date_e),
                wedding_type=wtype, officiant_name=ge(self.off_e),
            )
            if wtype == "기타":
                data["type_other"] = ge(self.type_other_e) or None
            if is_groom:
                data["groom_id"] = self.pno
                data["groom_name"] = self.name
                data["bride_name"] = spouse
            else:
                data["bride_id"] = self.pno
                data["bride_name"] = self.name
                data["groom_name"] = spouse
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
        self.birth_e   = add("생년월일", mk_entry(fv_("birth_date")),     r, 2); r += 1
        self.cur_addr_e = add("현 주소", mk_entry(fv_("address")),        r, 0, 4); r += 1

        # ── 사망 정보 ────────────────────────────────────────────────────────
        g.addWidget(shdr("📋  사망 정보"), r, 0, 1, 4); r += 1
        self.date_e   = add("사망일 (YYYY/MM/DD)",    mk_entry(), r, 0)
        self.family_e = add("유족 (연락 가족)",         mk_entry(), r, 1, 2); r += 1
        self.cemetery_e = add("묘지 주소",             mk_entry(), r, 0, 4); r += 1
        self.rites_e  = add("병자성사일 (YYYY/MM/DD)", mk_entry(), r, 0, 2); r += 1

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

        self.date_e    = add("전입일 (YYYY/MM/DD)", mk_entry(), 0, 0)
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

        self.date_e    = add("전출일 (YYYY/MM/DD)", mk_entry(), 0, 0)
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
