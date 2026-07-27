from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QMessageBox,
)

from core.constants import C
from ui.ui_helpers import mk_btn, mk_entry, mk_combo, vbox_field, ge


class BaptismForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("세례 기록 추가"); self.resize(540, 190); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.no_e     = add("세례 번호 *",         mk_entry(), 0, 0)
        self.date_e   = add("세례일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.church_e = add("세례 성당",           mk_entry(), 0, 2, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0)
        self.off_bn_e = add("집전자 세례명",        mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.no_e):
            QMessageBox.warning(self, "오류", "세례 번호를 입력하세요.")
            return
        try:
            self.db.create_baptism(dict(
                member_id=self.pno, baptism_no=ge(self.no_e),
                date=ge(self.date_e), parish=ge(self.church_e),
                officiant_name=ge(self.off_e),
                officiant_name_bapt=ge(self.off_bn_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class ConfirmationForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("견진 기록 추가"); self.resize(520, 190); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.no_e     = add("견진 번호 *",         mk_entry(), 0, 0)
        self.date_e   = add("견진일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.church_e = add("견진 성당",           mk_entry(), 0, 2, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.no_e):
            QMessageBox.warning(self, "오류", "견진 번호를 입력하세요.")
            return
        try:
            self.db.create_confirmation_record(dict(
                member_id=self.pno, confirmation_no=ge(self.no_e),
                date=ge(self.date_e), parish=ge(self.church_e),
                officiant_name=ge(self.off_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class WeddingForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.name = name; self.on_save = on_save
        self.setWindowTitle("혼인 기록 추가"); self.resize(560, 230); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.no_e      = add("혼인 번호 *",         mk_entry(), 0, 0)
        self.date_e    = add("혼인일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.type_cb   = add("형태",               mk_combo(["성사혼", "관면혼", "단순유효화혼", "바오로특전혼", "근본유효화혼"]), 0, 2, 2)
        self.role_cb   = add("역할",               mk_combo(["신랑", "신부"]), 1, 0)
        self.spouse_e  = add("배우자 이름",          mk_entry(), 1, 1)
        self.off_e     = add("집전자",              mk_entry(), 1, 2, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        if not ge(self.no_e):
            QMessageBox.warning(self, "오류", "혼인 번호를 입력하세요.")
            return
        try:
            is_groom = ge(self.role_cb) == "신랑"
            spouse = ge(self.spouse_e)
            data = dict(
                wedding_no=ge(self.no_e), date=ge(self.date_e),
                wedding_type=ge(self.type_cb), officiant_name=ge(self.off_e),
            )
            if is_groom:
                data["groom_name"] = self.name
                data["bride_name"] = spouse
            else:
                data["bride_name"] = self.name
                data["groom_name"] = spouse
            self.db.create_wedding_record(data)
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class DeathForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("사망 기록 추가"); self.resize(540, 190); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e  = add("사망일 (YYYY/MM/DD)",  mk_entry(), 0, 0)
        self.place_e = add("장소 (묘지)",           mk_entry(), 0, 1, 2)
        self.sick_e  = add("종부성사일 (YYYY/MM/DD)", mk_entry(), 1, 0)
        self.viat_e  = add("노자성사일 (YYYY/MM/DD)", mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_death_record(dict(
                member_id=self.pno, date_death=ge(self.date_e),
                cemetery=ge(self.place_e),
                last_rites_date=ge(self.sick_e),
                viaticum=ge(self.viat_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
