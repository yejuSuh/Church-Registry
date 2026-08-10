from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QMenu, QMessageBox,
)

from core.constants import C
from ui.ui_helpers import fv, mk_btn, shdr

_STATUS_STYLE = {
    "예정": "background:#b05a00;color:#fff;padding:1px 7px;border-radius:3px;font-size:11px;",
    "완료": "background:#2a7a2a;color:#fff;padding:1px 7px;border-radius:3px;font-size:11px;",
}


from forms.sacrament_forms import (
    BaptismForm, WeddingForm, DeathForm,
)
from forms.intake_forms import InfantBaptismForm, ConfirmationIntakeForm


class SacramentsTab(QWidget):
    """Scrollable tab displaying all sacrament records for a member with status badges and action buttons."""

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

    def _mark_done(self, table, pk_col, pk_val):
        self.db.update_sacrament_status(table, pk_col, pk_val, "완료")
        self._load()

    def _delete_record(self, table, pk_col, pk_val):
        if QMessageBox.question(
            self, "삭제 확인", "이 성사 기록을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_sacrament_record(table, pk_col, pk_val)
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
                ("세례일",     fv(rec, "date")),
                ("교구",       fv(rec, "diocese")),
                ("세례 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
                ("집전자 세례명", fv(rec, "officiant_name_bapt")),
                ("대부/대모",  fv(rec, "godparent_name_ko")),
                ("대부/대모 세례명", fv(rec, "godparent_name_bapt")),
            ],
            baptism_menu, status_info=("baptism", "id"))

        # 견진: one unified application form (성인/청소년 tabs inside)
        self._section(lay, "🕊  견진", self.db.get_confirmation_records(self.pno),
            lambda rec: [
                ("견진번호",   fv(rec, "confirmation_no")),
                ("견진명",     fv(rec, "confirmation_name")),
                ("견진일",     fv(rec, "date")),
                ("교구",       fv(rec, "diocese")),
                ("견진 성당",  fv(rec, "parish")),
                ("집전자",     fv(rec, "officiant_name")),
                ("집전자 세례명", fv(rec, "officiant_name_bapt")),
                ("대부/대모",  fv(rec, "godparent_name_ko")),
                ("대부/대모 세례명", fv(rec, "godparent_name_bapt")),
            ],
            lambda: open_dialog(ConfirmationIntakeForm), status_info=("confirmation", "id"))

        wedding_menu = QMenu(self)
        wedding_menu.addAction("⚡ 빠른 입력", lambda: open_dialog(WeddingForm))

        self._section(lay, "💒  혼인", self.db.get_wedding_records(self.pno),
            lambda rec: [
                ("혼인번호", fv(rec, "wedding_no")),
                ("혼인일",   fv(rec, "date")),
                ("형태",     fv(rec, "wedding_type")),
                ("형태 상세", fv(rec, "type_other")),
                ("신랑",     fv(rec, "groom_name")),
                ("신랑 세례명", fv(rec, "groom_name_bapt")),
                ("신부",     fv(rec, "bride_name")),
                ("신부 세례명", fv(rec, "bride_name_bapt")),
                ("집전자",   fv(rec, "officiant_name")),
                ("집전자 세례명", fv(rec, "officiant_name_bapt")),
            ],
            wedding_menu, status_info=("wedding", "wedding_no"))

        self._section(lay, "🍞  첫영성체", self.db.get_communion_records(self.pno),
            lambda rec: [
                ("첫영성체번호", fv(rec, "communion_no")),
                ("첫영성체일",   fv(rec, "date")),
                ("교구",         fv(rec, "diocese")),
                ("성당",         fv(rec, "parish")),
                ("집전자",       fv(rec, "officiant_name")),
            ],
            None, status_info=("communion", "communion_no"))

        death_menu = QMenu(self)
        death_menu.addAction("⚡ 빠른 입력", lambda: open_dialog(DeathForm))

        self._section(lay, "✟  사망", self.db.get_death_records(self.pno),
            lambda rec: [
                ("사망일",   fv(rec, "date_death")),
                ("장소",     fv(rec, "cemetery")),
                ("병자성사",  fv(rec, "last_rites_date")),
            ],
            death_menu)

        lay.addStretch()
        self._scroll.setWidget(body)

    def _section(self, lay, title, records, fields_fn, action, status_info=None):
        """`action` is either a QMenu (dropdown add button) or a plain callable.
        `status_info` is (table_name, pk_col) for sacraments that support 예정/완료."""
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
            vl = QVBoxLayout(card); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

            # Status badge + 완료 button (only for records with an explicit status)
            if status_info:
                table, pk_col = status_info
                pk_val  = rec[pk_col]
                status  = rec["status"]   # None for legacy rows
                if status:
                    sr = QWidget()
                    sl = QHBoxLayout(sr); sl.setContentsMargins(10, 4, 10, 2); sl.setSpacing(6)
                    badge = QLabel(status)
                    badge.setStyleSheet(_STATUS_STYLE.get(status, _STATUS_STYLE["예정"]))
                    sl.addWidget(badge); sl.addStretch()
                    if status == "예정":
                        done_btn = mk_btn("✓ 완료", "btn_success")
                        done_btn.setFixedHeight(20); done_btn.setFixedWidth(60)
                        done_btn.clicked.connect(
                            lambda _, t=table, p=pk_col, v=pk_val: self._mark_done(t, p, v)
                        )
                        sl.addWidget(done_btn)
                        del_btn = mk_btn("✕ 삭제", "btn_danger")
                        del_btn.setFixedHeight(20); del_btn.setFixedWidth(60)
                        del_btn.clicked.connect(
                            lambda _, t=table, p=pk_col, v=pk_val: self._delete_record(t, p, v)
                        )
                        sl.addWidget(del_btn)
                    vl.addWidget(sr)

            pairs_w = QWidget()
            g = QGridLayout(pairs_w); g.setContentsMargins(10, 6, 10, 6)
            g.setHorizontalSpacing(12); g.setVerticalSpacing(3)
            g.setColumnStretch(1, 2); g.setColumnStretch(3, 2)
            row, col = 0, 0
            for lbl_txt, val_txt in pairs:
                lw = QLabel(lbl_txt); lw.setObjectName("fl")
                vw = QLabel(val_txt); vw.setObjectName("fv"); vw.setWordWrap(True)
                g.addWidget(lw, row, col * 2); g.addWidget(vw, row, col * 2 + 1)
                col += 1
                if col >= 2: col = 0; row += 1
            vl.addWidget(pairs_w)
            lay.addWidget(card)
