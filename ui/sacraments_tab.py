from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QMenu,
)

from core.constants import C
from ui.ui_helpers import fv, mk_btn, shdr


def _married_disp(rec):
    # fv() treats 0 as "no value" (falsy), which would hide an explicit
    # "아니오" (not married in church) -- read the raw column instead.
    try:
        v = rec["parents_married_in_church"]
    except Exception:
        v = None
    return "예" if v == 1 else ("아니오" if v == 0 else "")
from forms.sacrament_forms import (
    BaptismForm, WeddingForm, DeathForm,
)
from forms.intake_forms import InfantBaptismForm, ConfirmationIntakeForm


class SacramentsTab(QWidget):
    def __init__(self, db, pno):
        super().__init__()
        self.db = db; self.pno = pno
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self._scroll, 1)
        self._load()

    def reload(self):
        self._load()

    def _load(self):
        body = QWidget(); body.setObjectName("card")
        lay = QVBoxLayout(body); lay.setContentsMargins(12, 8, 12, 16); lay.setSpacing(10)

        p = self.db.get(self.pno)
        name = fv(p, "name") if p else ""

        def open_dialog(cls):
            cls(self, self.db, self.pno, name, on_save=self.reload).exec()

        # 세례: full infant-baptism/first-communion intake form, or a quick
        # manual entry for simple/legacy records.
        baptism_menu = QMenu(self)
        baptism_menu.addAction("📋 유아세례 및 첫영성체 신청서", lambda: open_dialog(InfantBaptismForm))
        baptism_menu.addAction("⚡ 빠른 입력 (간단 기록)", lambda: open_dialog(BaptismForm))

        self._section(lay, "✝  세례", self.db.get_baptism_records(self.pno),
            lambda rec: [
                ("세례번호",   fv(rec, "baptism_no")),
                ("세례일",     fv(rec, "baptism_date")),
                ("교구",       fv(rec, "diocese")),
                ("세례 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
                ("집전자 세례명", fv(rec, "officiant_baptismal_name")),
                ("대부/대모",  fv(rec, "godparent_name_korean")),
                ("대부/대모 세례명", fv(rec, "godparent_baptismal_name")),
                ("아버지",     fv(rec, "father_name_korean")),
                ("아버지 전화", fv(rec, "father_phone")),
                ("어머니",     fv(rec, "mother_name_korean")),
                ("어머니 전화", fv(rec, "mother_phone")),
                ("부모 혼인성사", _married_disp(rec)),
            ],
            baptism_menu)

        # 견진: one unified application form (성인/청소년 tabs inside)
        self._section(lay, "🕊  견진", self.db.get_confirmation_records(self.pno),
            lambda rec: [
                ("견진번호",   fv(rec, "confirmation_no")),
                ("견진일",     fv(rec, "confirmation_date")),
                ("교구",       fv(rec, "diocese")),
                ("견진 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
                ("대부/대모",  fv(rec, "sponsor_name_korean")),
                ("대부/대모 세례명", fv(rec, "sponsor_baptismal_name")),
                ("아버지",     fv(rec, "father_name_korean")),
                ("아버지 전화", fv(rec, "father_phone")),
                ("어머니",     fv(rec, "mother_name_korean")),
                ("어머니 전화", fv(rec, "mother_phone")),
                ("부모 혼인성사", _married_disp(rec)),
                ("혼인기록 연결", fv(rec, "wedding_no")),
            ],
            lambda: open_dialog(ConfirmationIntakeForm))

        wedding_menu = QMenu(self)
        wedding_menu.addAction("⚡ 빠른 입력", lambda: open_dialog(WeddingForm))

        self._section(lay, "💒  혼인", self.db.get_wedding_records(self.pno),
            lambda rec: [
                ("혼인번호", fv(rec, "wedding_no")),
                ("혼인일",   fv(rec, "wedding_date")),
                ("형태",     fv(rec, "wedding_type")),
                ("장소",     fv(rec, "marriage_place")),
                ("신랑",     fv(rec, "groom_name")),
                ("신랑 세례명", fv(rec, "groom_baptismal_name")),
                ("신부",     fv(rec, "bride_name")),
                ("신부 세례명", fv(rec, "bride_baptismal_name")),
                ("집전자",   fv(rec, "officiant_name")),
            ],
            wedding_menu)

        self._section(lay, "🍞  첫영성체", self.db.get_communion_records(self.pno),
            lambda rec: [
                ("첫영성체번호", fv(rec, "communion_no")),
                ("첫영성체일",   fv(rec, "communion_date")),
                ("교구",         fv(rec, "diocese")),
                ("성당",         fv(rec, "parish")),
            ],
            None)

        death_menu = QMenu(self)
        death_menu.addAction("⚡ 빠른 입력", lambda: open_dialog(DeathForm))

        self._section(lay, "✟  사망", self.db.get_death_records(self.pno),
            lambda rec: [
                ("사망일",   fv(rec, "death_date")),
                ("장소",     fv(rec, "cemetery")),
                ("종부성사",  fv(rec, "last_rites_date")),
                ("노자성사",  fv(rec, "viaticum")),
            ],
            death_menu)

        lay.addStretch()
        self._scroll.setWidget(body)

    def _section(self, lay, title, records, fields_fn, action):
        """`action` is either a QMenu (dropdown add button) or a plain
        callable (direct add button)."""
        hdr_row = QWidget()
        hl = QHBoxLayout(hdr_row); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(6)
        hl.addWidget(shdr(title)); hl.addStretch()
        if action is not None:
            if isinstance(action, QMenu):
                add_btn = mk_btn("+ 추가 ▾", "btn_success")
                add_btn.setMenu(action)
            else:
                add_btn = mk_btn("+ 추가", "btn_success")
                add_btn.clicked.connect(action)
            add_btn.setFixedHeight(26); add_btn.setFixedWidth(78)
            hl.addWidget(add_btn)
        lay.addWidget(hdr_row)

        if not records:
            lbl = QLabel("  기록 없음"); lbl.setObjectName("mu")
            lay.addWidget(lbl)
            return

        for rec in records:
            pairs = [(l, v) for l, v in fields_fn(rec) if v and v not in ("—", "")]
            if not pairs:
                continue
            card = QWidget()
            card.setStyleSheet(f"background:{C['header']};border-radius:4px;")
            g = QGridLayout(card); g.setContentsMargins(10, 6, 10, 6)
            g.setHorizontalSpacing(12); g.setVerticalSpacing(3)
            g.setColumnStretch(1, 2); g.setColumnStretch(3, 2)
            row, col = 0, 0
            for lbl_txt, val_txt in pairs:
                lw = QLabel(lbl_txt); lw.setObjectName("fl")
                vw = QLabel(val_txt); vw.setObjectName("fv"); vw.setWordWrap(True)
                g.addWidget(lw, row, col * 2); g.addWidget(vw, row, col * 2 + 1)
                col += 1
                if col >= 2: col = 0; row += 1
            lay.addWidget(card)
