from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout,
)

from constants import C
from ui_helpers import fv, mk_btn, shdr
from sacrament_forms import (
    BaptismForm, ConfirmationForm, WeddingForm, DeathForm,
)


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

        self._section(lay, "✝  세례", self.db.get_baptism_records(self.pno),
            lambda rec: [
                ("세례번호",   fv(rec, "baptism_no")),
                ("세례일",     fv(rec, "baptism_date")),
                ("세례 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
                ("집전자 세례명", fv(rec, "officiant_baptismal_name")),
            ],
            lambda: BaptismForm(self, self.db, self.pno, name, on_save=self.reload).exec())

        self._section(lay, "🕊  견진", self.db.get_confirmation_records(self.pno),
            lambda rec: [
                ("견진번호",   fv(rec, "confirmation_no")),
                ("견진일",     fv(rec, "confirmation_date")),
                ("견진 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
            ],
            lambda: ConfirmationForm(self, self.db, self.pno, name, on_save=self.reload).exec())

        self._section(lay, "💒  혼인", self.db.get_wedding_records(self.pno),
            lambda rec: [
                ("혼인번호", fv(rec, "wedding_no")),
                ("혼인일",   fv(rec, "wedding_date")),
                ("형태",     fv(rec, "wedding_type")),
                ("신랑",     fv(rec, "groom_name")),
                ("신랑 세례명", fv(rec, "groom_baptismal_name")),
                ("신부",     fv(rec, "bride_name")),
                ("신부 세례명", fv(rec, "bride_baptismal_name")),
                ("집전자",   fv(rec, "officiant_name")),
            ],
            lambda: WeddingForm(self, self.db, self.pno, name, on_save=self.reload).exec())

        self._section(lay, "✟  사망", self.db.get_death_records(self.pno),
            lambda rec: [
                ("사망일",   fv(rec, "death_date")),
                ("장소",     fv(rec, "cemetery")),
                ("종부성사",  fv(rec, "last_rites_date")),
                ("노자성사",  fv(rec, "viaticum")),
            ],
            lambda: DeathForm(self, self.db, self.pno, name, on_save=self.reload).exec())

        lay.addStretch()
        self._scroll.setWidget(body)

    def _section(self, lay, title, records, fields_fn, on_add):
        hdr_row = QWidget()
        hl = QHBoxLayout(hdr_row); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(6)
        hl.addWidget(shdr(title)); hl.addStretch()
        add_btn = mk_btn("+ 추가", "btn_success")
        add_btn.setFixedHeight(26); add_btn.setFixedWidth(68)
        add_btn.clicked.connect(on_add)
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
