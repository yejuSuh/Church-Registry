from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QMessageBox,
)

from constants import C
from ui_helpers import mk_btn, mk_entry, mk_combo, mk_check, vbox_field, ge


class BaptismForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("세례 기록 추가"); self.resize(600, 240); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.no_e     = add("세례 번호",           mk_entry(), 0, 0)
        self.date_e   = add("세례일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.church_e = add("세례 성당",           mk_entry(), 0, 2, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0)
        self.god_e    = add("대부/대모",            mk_entry(), 1, 1)
        self.fa_e     = add("부친",               mk_entry(), 1, 2)
        self.mo_e     = add("모친",               mk_entry(), 1, 3)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_baptism(dict(
                parishioner_no=self.pno, baptism_no=ge(self.no_e),
                baptism_date=ge(self.date_e), baptism_church=ge(self.church_e),
                officiator_nm=ge(self.off_e), godfather_nm=ge(self.god_e),
                father_nm=ge(self.fa_e), mother_nm=ge(self.mo_e),
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

        self.no_e     = add("견진 번호",           mk_entry(), 0, 0)
        self.date_e   = add("견진일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.church_e = add("견진 성당",           mk_entry(), 0, 2, 2)
        self.off_e    = add("집전자",              mk_entry(), 1, 0, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_sacrament_record(dict(
                parishioner_no=self.pno, sacrament_no=ge(self.no_e),
                sacrament_date=ge(self.date_e), sacrament_parish_church=ge(self.church_e),
                officiator_nm=ge(self.off_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class WeddingForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.name = name; self.on_save = on_save
        self.setWindowTitle("혼인 기록 추가"); self.resize(620, 260); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.no_e     = add("혼인 번호",           mk_entry(), 0, 0)
        self.date_e   = add("혼인일 (YYYY/MM/DD)", mk_entry(), 0, 1)
        self.church_e = add("성당",               mk_entry(), 0, 2, 2)
        self.role_cb  = add("역할",               mk_combo(["신랑 (m)", "신부 (w)"]), 1, 0)
        self.spouse_e = add("배우자 이름",          mk_entry(), 1, 1)
        self.off_e    = add("집전자",              mk_entry(), 1, 2, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            is_groom = ge(self.role_cb).startswith("신랑")
            spouse = ge(self.spouse_e)
            data = dict(
                wedding_no=ge(self.no_e), wedding_date=ge(self.date_e),
                parish_church=ge(self.church_e), officiator_nm=ge(self.off_e),
            )
            if is_groom:
                data["m_parishioner_no"] = self.pno
                data["m_name"]           = self.name
                data["w_name"]           = spouse
            else:
                data["w_parishioner_no"] = self.pno
                data["w_name"]           = self.name
                data["m_name"]           = spouse
            self.db.create_wedding_record(data)
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class ConfessionForm(QDialog):
    def __init__(self, parent, db, pno, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("고해 기록 추가"); self.resize(360, 170); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(8)
        outer.addWidget(body, 1)

        self.year_e    = mk_entry()
        self.spring_cb = mk_check("봄")
        self.fall_cb   = mk_check("가을")
        g.addWidget(vbox_field("연도 (YYYY)", self.year_e, C['card']), 0, 0, 1, 2)
        fw = QWidget(); fw.setObjectName("card")
        fl = QHBoxLayout(fw); fl.setContentsMargins(0, 4, 0, 0)
        fl.addWidget(self.spring_cb); fl.addWidget(self.fall_cb); fl.addStretch()
        g.addWidget(vbox_field("성사 완료", fw, C['card']), 1, 0, 1, 2)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        year = ge(self.year_e)
        if not year:
            QMessageBox.warning(self, "오류", "연도를 입력하세요."); return
        try:
            self.db.create_confession_record(dict(
                parishioner_no=self.pno, confession_year=year,
                spring="Y" if self.spring_cb.isChecked() else "N",
                fall="Y" if self.fall_cb.isChecked() else "N",
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


class DeathForm(QDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.setWindowTitle("사망 기록 추가"); self.resize(580, 210); self.setModal(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QWidget(); body.setObjectName("card")
        g = QGridLayout(body); g.setContentsMargins(16, 12, 16, 12)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)
        outer.addWidget(body, 1)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span); return w

        self.date_e  = add("사망일 (YYYY/MM/DD)",    mk_entry(), 0, 0)
        self.place_e = add("장소",                   mk_entry(), 0, 1, 2)
        self.off_e   = add("집전자",                 mk_entry(), 0, 3)
        self.sick_e  = add("병자성사일 (YYYY/MM/DD)", mk_entry(), 1, 0)
        self.viat_e  = add("노자성사일 (YYYY/MM/DD)", mk_entry(), 1, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted"); sb = mk_btn("💾  저장", "btn_accent")
        cb.clicked.connect(self.reject); sb.clicked.connect(self._save)
        bbl.addWidget(cb); bbl.addWidget(sb); outer.addWidget(bb)

    def _save(self):
        try:
            self.db.create_death_record(dict(
                parishioner_no=self.pno, death_date=ge(self.date_e),
                place=ge(self.place_e), officiator_nm=ge(self.off_e),
                sickness_date=ge(self.sick_e), viaticum_date=ge(self.viat_e),
            ))
            if self.on_save: self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
