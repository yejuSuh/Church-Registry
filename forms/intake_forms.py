from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QScrollArea, QFrame, QLabel, QMessageBox, QTabWidget,
)
from PyQt6.QtCore import Qt

from core.constants import C
from ui.ui_helpers import fv, mk_btn, mk_entry, mk_combo, mk_check, vbox_field, shdr, ge
from forms.person_picker import PersonPicker, WeddingMatchDialog


# ── Shared building blocks ───────────────────────────────────────────────────

def member_summary(member):
    """Read-only one-liner identifying the member a sacrament is being added
    to. The member's own data (names, birth date, address, ...) already lives
    on the registration record, so intake forms don't ask for it again."""
    w = QWidget()
    lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)
    lay.addWidget(shdr("👤  신청자"))
    parts = [fv(member, "display_id"), fv(member, "name")]
    bn = fv(member, "baptismal_name")
    if bn:
        parts[-1] += f" ({bn})"
    sex = {'M': '남', 'F': '여'}.get(fv(member, "sex"), "")
    for extra in (sex, fv(member, "birth_date")):
        if extra:
            parts.append(extra)
    lbl = QLabel("  ·  ".join(p for p in parts if p))
    lbl.setObjectName("fv")
    lay.addWidget(lbl)
    return w


class ParentBlock(QWidget):
    """Father/mother field group: a PersonPicker (name + phone) plus that
    parent's own baptism info (date/diocese/parish) -- same column shape on
    both `baptism` and `confirmation`."""

    def __init__(self, db, title, required=()):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.picker = PersonPicker(db, title, show_english=True, show_phone=True,
                                   required=required)
        lay.addWidget(self.picker)

        row = QWidget()
        rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(10)
        self.bdate_e = mk_entry(); rl.addWidget(vbox_field("세례일", self.bdate_e, C['card']), 1)
        self.dioc_e = mk_entry(); rl.addWidget(vbox_field("세례 교구", self.dioc_e, C['card']), 1)
        self.par_e = mk_entry(); rl.addWidget(vbox_field("세례 성당", self.par_e, C['card']), 1)
        lay.addWidget(row)

    def data(self, prefix):
        d = self.picker.data(prefix)
        d[f"{prefix}_baptism_date"] = self.bdate_e.text().strip() or None
        d[f"{prefix}_baptism_diocese"] = self.dioc_e.text().strip() or None
        d[f"{prefix}_baptism_parish"] = self.par_e.text().strip() or None
        return d

    def name_korean(self):
        return self.picker.kr_e.text().strip()

    def member_id(self):
        return self.picker.member_id


class PriorBaptismBlock(QWidget):
    """Date/diocese/parish of a baptism that already happened (elsewhere or
    previously), entered on the confirmation/RCIA forms so it can be recorded
    into `baptism` if the applicant has no baptism record on file yet.
    Requires a manually-entered baptism_no (this app doesn't auto-number
    sacrament records -- see sacrament_counter in DB_SCHEMA_GUIDE.md) so it's
    skipped entirely if left blank."""

    def __init__(self, has_existing):
        super().__init__()
        self.has_existing = has_existing
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        lay.addWidget(shdr("✝  세례성사"))
        if has_existing:
            note = QLabel("이미 세례 기록이 있어 새로 만들지 않습니다 (세례 기록 탭 참고).")
            note.setObjectName("mu")
            lay.addWidget(note)

        # required unless an existing baptism record makes this block moot
        star = "" if has_existing else " *"
        row = QWidget()
        rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(10)
        self.no_e = mk_entry(); rl.addWidget(vbox_field(f"세례 번호{star}", self.no_e, C['card']), 1)
        self.date_e = mk_entry(); rl.addWidget(vbox_field(f"세례일자{star}", self.date_e, C['card']), 1)
        self.dioc_e = mk_entry(); rl.addWidget(vbox_field(f"세례교구{star}", self.dioc_e, C['card']), 1)
        self.par_e = mk_entry(); rl.addWidget(vbox_field(f"세례본당{star}", self.par_e, C['card']), 1)
        lay.addWidget(row)

        if has_existing:
            for w in (self.no_e, self.date_e, self.dioc_e, self.par_e):
                w.setEnabled(False)

    def maybe_create(self, db, member_id):
        if self.has_existing:
            return
        no = self.no_e.text().strip()
        if not no:
            return
        db.create_baptism(dict(
            baptism_no=no, member_id=member_id,
            baptism_date=self.date_e.text().strip() or None,
            diocese=self.dioc_e.text().strip() or None,
            parish=self.par_e.text().strip() or None,
        ))


# ── Dialog scaffolding ───────────────────────────────────────────────────────

class _IntakeDialog(QDialog):
    def __init__(self, parent, db, pno, name, title, size, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.member = db.get(pno)
        self.setWindowTitle(title)
        self.resize(*size)
        self.setModal(True)

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(); body.setObjectName("card")
        scroll.setWidget(body)
        self.grid = QGridLayout(body)
        self.grid.setContentsMargins(16, 12, 16, 12)
        self.grid.setHorizontalSpacing(16); self.grid.setVerticalSpacing(10)
        for col in range(4):
            self.grid.setColumnStretch(col, 1)
        outer.addWidget(scroll, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cbtn = mk_btn("취소", "btn_muted"); sbtn = mk_btn("💾  저장", "btn_accent")
        cbtn.clicked.connect(self.reject); sbtn.clicked.connect(self._save)
        bbl.addWidget(cbtn); bbl.addWidget(sbtn)
        outer.addWidget(bb)

    def add(self, lbl, w, r, c, span=1):
        self.grid.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span)
        return w

    def hdr(self, text, r):
        self.grid.addWidget(shdr(text), r, 0, 1, 4)

    def _link_parents(self, father: ParentBlock, mother: ParentBlock):
        # Decision: when a father/mother match is found, automatically link the
        # child into that household (family.head_of_household/relation) rather
        # than leaving it as a manual follow-up -- see item 4 in the intake
        # forms task. This overwrites the applicant's existing family row.
        father_mid = father.member_id()
        mother_mid = mother.member_id()
        if not (father_mid or mother_mid):
            return
        relation = {'M': '자', 'F': '녀'}.get(fv(self.member, "sex"), '자녀')
        head = father.name_korean() if father_mid else mother.name_korean()
        if head:
            self.db.link_child_to_parent(self.pno, head, relation)


class ConfirmationIntakeForm(_IntakeDialog):
    """Unified 견진성사 신청서: common required blocks (applicant, baptism
    info, sponsor, rite info) plus a 성인/청소년 tab for the type-specific
    fields. Replaces the separate adult/RCIA/youth forms."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "견진성사 신청서", (720, 800), on_save)
        r = 0
        self.grid.addWidget(member_summary(self.member), r, 0, 1, 4); r += 1

        self.prior_baptism = PriorBaptismBlock(has_existing=bool(db.get_baptism_records(pno)))
        self.grid.addWidget(self.prior_baptism, r, 0, 1, 4); r += 1

        self.sponsor = PersonPicker(db, "🕊  대부모", show_english=True, show_phone=False,
                                    required=("kr", "en", "bn"))
        self.grid.addWidget(self.sponsor, r, 0, 1, 4); r += 1

        self.hdr("🕊  견진 정보", r); r += 1
        self.no_e = self.add("견진 번호 *", mk_entry(), r, 0)
        self.date_e = self.add("성사 예정일 (YYYY/MM/DD) *", mk_entry(), r, 1)
        self.off_e = self.add("집전사제/(대)주교 *", mk_entry(), r, 2, 2); r += 1
        self.dioc_e = self.add("교구", mk_entry(), r, 0)
        self.church_e = self.add("성당", mk_entry(), r, 1); r += 1

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_adult_tab(), "성인")
        self.tabs.addTab(self._build_youth_tab(), "청소년")
        self.grid.addWidget(self.tabs, r, 0, 1, 4); r += 1
        self.grid.setRowStretch(r, 1)

    # ── Tab builders ─────────────────────────────────────────────────────────

    def _build_adult_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 10, 8, 10); lay.setSpacing(10)

        mrow = QWidget()
        ml = QHBoxLayout(mrow); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(10)
        self.marital_cb = mk_combo(
            ['미혼', '초혼', '재혼', '이혼', '사별'], fv(self.member, "marital_status")
        )
        ml.addWidget(vbox_field("혼인상태 *", self.marital_cb, C['card']), 1)
        ml.addStretch(3)
        lay.addWidget(mrow)

        self.spouse_group = QWidget()
        sl = QVBoxLayout(self.spouse_group); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(6)
        self.spouse = PersonPicker(self.db, "💍  배우자", show_english=True, show_phone=False,
                                   required=("kr", "en", "bn"))
        sl.addWidget(self.spouse)

        wrow = QWidget()
        wl = QHBoxLayout(wrow); wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(10)
        self.wtype_cb = mk_combo(["(관면)혼배성사", "사회혼"])
        wl.addWidget(vbox_field("혼인 형태 *", self.wtype_cb, C['card']), 1)
        self.wplace_e = mk_entry()
        wl.addWidget(vbox_field("혼인장소 *", self.wplace_e, C['card']), 1)
        self.wdate_e = mk_entry()
        wl.addWidget(vbox_field("혼인날짜 *", self.wdate_e, C['card']), 1)
        self.woff_e = mk_entry()
        wl.addWidget(vbox_field("예식 집전자 *", self.woff_e, C['card']), 1)
        sl.addWidget(wrow)

        wrow2 = QWidget()
        wl2 = QHBoxLayout(wrow2); wl2.setContentsMargins(0, 0, 0, 0); wl2.setSpacing(10)
        self.wno_e = mk_entry()
        wl2.addWidget(vbox_field("혼인 번호 (신규 생성 시 필요)", self.wno_e, C['card']), 1)
        find_btn = mk_btn("🔍 기존 혼인기록 찾기", "btn_muted")
        find_btn.clicked.connect(self._find_wedding)
        wl2.addWidget(find_btn, 1)
        sl.addWidget(wrow2)

        lay.addWidget(self.spouse_group)
        lay.addStretch()
        self._matched_wedding_no = None

        self.marital_cb.currentTextChanged.connect(lambda _: self._on_marital_change())
        self._on_marital_change()
        return w

    def _build_youth_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 10, 8, 10); lay.setSpacing(10)
        self.father = ParentBlock(self.db, "👨  아버지", required=("kr", "en", "phone"))
        self.mother = ParentBlock(self.db, "👩  어머니", required=("kr", "en", "phone"))
        self.married_cb = mk_check("부모가 혼인성사(성당)로 결혼함")
        lay.addWidget(self.father)
        lay.addWidget(self.mother)
        lay.addWidget(self.married_cb)
        lay.addStretch()
        return w

    # ── Adult tab helpers ────────────────────────────────────────────────────

    def _on_marital_change(self):
        show = ge(self.marital_cb) in ("초혼", "재혼")
        self.spouse_group.setVisible(show)

    def _find_wedding(self):
        spouse_name = self.spouse.kr_e.text().strip()
        dlg = WeddingMatchDialog(self, self.db, spouse_name, member_id=self.pno)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.chosen:
            r = dlg.chosen
            self._matched_wedding_no = r["wedding_no"]
            self.wno_e.setText(fv(r, "wedding_no")); self.wno_e.setReadOnly(True)
            self.wdate_e.setText(fv(r, "wedding_date"))
            idx = self.wtype_cb.findText(fv(r, "wedding_type"), Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.wtype_cb.setCurrentIndex(idx)
            self.wplace_e.setText(fv(r, "marriage_place"))
            self.woff_e.setText(fv(r, "officiant_name"))

    def _resolve_wedding(self, marital_status):
        """Returns the wedding_no to link on confirmation.wedding_no, creating
        a new `wedding` row if needed. Returns None if not currently married,
        or if married but no wedding_no was given for a new record."""
        if marital_status not in ("초혼", "재혼"):
            return None
        if self._matched_wedding_no:
            return self._matched_wedding_no
        spouse_name = self.spouse.kr_e.text().strip()
        wno = ge(self.wno_e)
        if not spouse_name or not wno:
            return None
        is_groom = fv(self.member, "sex") == 'M'
        wdata = dict(
            wedding_no=wno,
            wedding_date=ge(self.wdate_e) or None,
            wedding_type=ge(self.wtype_cb) or None,
            marriage_place=ge(self.wplace_e) or None,
            officiant_name=ge(self.woff_e) or None,
        )
        applicant_kr = fv(self.member, "name") or None
        applicant_en = fv(self.member, "name_english") or None
        applicant_bn = fv(self.member, "baptismal_name") or None
        spouse_en = self.spouse.en_e.text().strip() or None
        spouse_bn = self.spouse.bn_e.text().strip() or None
        if is_groom:
            wdata.update(
                groom_member_id=self.pno, groom_name=applicant_kr,
                groom_name_english=applicant_en, groom_baptismal_name=applicant_bn,
                bride_member_id=self.spouse.member_id, bride_name=spouse_name,
                bride_name_english=spouse_en, bride_baptismal_name=spouse_bn,
            )
        else:
            wdata.update(
                bride_member_id=self.pno, bride_name=applicant_kr,
                bride_name_english=applicant_en, bride_baptismal_name=applicant_bn,
                groom_member_id=self.spouse.member_id, groom_name=spouse_name,
                groom_name_english=spouse_en, groom_baptismal_name=spouse_bn,
            )
        self.db.create_wedding_record(wdata)
        return wno

    # ── Save ─────────────────────────────────────────────────────────────────

    def _save(self):
        try:
            is_adult = self.tabs.currentIndex() == 0

            checks = [
                (self.no_e,        "견진 번호를 입력하세요."),
                (self.date_e,      "성사 예정일을 입력하세요."),
                (self.off_e,       "집전사제/(대)주교를 입력하세요."),
                (self.sponsor.kr_e, "대부모 한글 이름을 입력하세요."),
                (self.sponsor.en_e, "대부모 영문 이름을 입력하세요."),
                (self.sponsor.bn_e, "대부모 세례명을 입력하세요."),
            ]
            if not self.prior_baptism.has_existing:
                checks += [
                    (self.prior_baptism.no_e,   "세례 번호를 입력하세요."),
                    (self.prior_baptism.date_e, "세례일자를 입력하세요."),
                    (self.prior_baptism.dioc_e, "세례교구를 입력하세요."),
                    (self.prior_baptism.par_e,  "세례본당을 입력하세요."),
                ]
            if is_adult:
                if ge(self.marital_cb) in ("초혼", "재혼"):
                    checks += [
                        (self.spouse.kr_e, "배우자 한글 이름을 입력하세요."),
                        (self.spouse.en_e, "배우자 영문 이름을 입력하세요."),
                        (self.spouse.bn_e, "배우자 세례명을 입력하세요."),
                        (self.wplace_e,    "혼인장소를 입력하세요."),
                        (self.wdate_e,     "혼인날짜를 입력하세요."),
                        (self.woff_e,      "예식 집전자를 입력하세요."),
                    ]
            else:
                checks += [
                    (self.father.picker.kr_e,    "아버지 한글 이름을 입력하세요."),
                    (self.father.picker.en_e,    "아버지 영문 이름을 입력하세요."),
                    (self.father.picker.phone_e, "아버지 전화번호를 입력하세요."),
                    (self.mother.picker.kr_e,    "어머니 한글 이름을 입력하세요."),
                    (self.mother.picker.en_e,    "어머니 영문 이름을 입력하세요."),
                    (self.mother.picker.phone_e, "어머니 전화번호를 입력하세요."),
                ]
            for widget, msg in checks:
                if not widget.text().strip():
                    QMessageBox.warning(self, "오류", msg)
                    widget.setFocus()
                    return

            if is_adult and ge(self.marital_cb):
                self.db.update_member_fields(
                    self.pno, dict(marital_status=ge(self.marital_cb)))
            self.prior_baptism.maybe_create(self.db, self.pno)

            data = dict(
                confirmation_no=ge(self.no_e), member_id=self.pno,
                confirmation_date=ge(self.date_e),
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e),
            )
            data.update(self.sponsor.data("sponsor"))

            if is_adult:
                data["wedding_no"] = self._resolve_wedding(ge(self.marital_cb))
            else:
                data.update(self.father.data("father"))
                data.update(self.mother.data("mother"))
                data["parents_married_in_church"] = 1 if self.married_cb.isChecked() else 0

            self.db.create_confirmation_record(data)

            if not is_adult:
                self._link_parents(self.father, self.mother)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 3: 유아세례 및 첫영성체 신청서 — Infant Baptism & First Communion ───

class InfantBaptismForm(_IntakeDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "유아세례 및 첫영성체 신청서", (720, 780), on_save)
        r = 0
        self.grid.addWidget(member_summary(self.member), r, 0, 1, 4); r += 1

        self.hdr("✝  세례 정보", r); r += 1
        self.no_e = self.add("세례 번호 *", mk_entry(), r, 0)
        self.date_e = self.add("세례일 (예정/실시, YYYY/MM/DD)", mk_entry(), r, 1)
        self.dioc_e = self.add("교구", mk_entry(), r, 2)
        self.church_e = self.add("성당", mk_entry(), r, 3); r += 1
        self.off_e = self.add("집전자/부제", mk_entry(), r, 0)
        self.off_bn_e = self.add("집전자 세례명", mk_entry(), r, 1); r += 1

        self.father = ParentBlock(db, "👨  아버지")
        self.grid.addWidget(self.father, r, 0, 1, 4); r += 1
        self.mother = ParentBlock(db, "👩  어머니")
        self.grid.addWidget(self.mother, r, 0, 1, 4); r += 1

        self.married_cb = mk_check("부모가 혼인성사(성당)로 결혼함")
        self.grid.addWidget(self.married_cb, r, 0, 1, 4); r += 1

        self.godparent = PersonPicker(db, "🕊  대부/대모", show_english=True, show_phone=False)
        self.grid.addWidget(self.godparent, r, 0, 1, 4); r += 1

        self.comm_cb = mk_check("첫영성체 신청")
        self.grid.addWidget(self.comm_cb, r, 0, 1, 4); r += 1

        self.comm_group = QWidget()
        cl = QHBoxLayout(self.comm_group); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(10)
        self.comm_no_e = mk_entry()
        cl.addWidget(vbox_field("첫영성체 번호 *", self.comm_no_e, C['card']), 1)
        self.comm_date_e = mk_entry()
        cl.addWidget(vbox_field("첫영성체일 (예정/실시)", self.comm_date_e, C['card']), 1)
        self.comm_cb.toggled.connect(self.comm_group.setVisible)
        self.comm_group.setVisible(False)
        self.grid.addWidget(self.comm_group, r, 0, 1, 4); r += 1

        self.grid.setRowStretch(r, 1)

    def _save(self):
        try:
            no = ge(self.no_e)
            if not no:
                QMessageBox.warning(self, "오류", "세례 번호를 입력하세요.")
                return

            data = dict(
                baptism_no=no, member_id=self.pno,
                baptism_date=ge(self.date_e) or None,
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e) or None,
                officiant_baptismal_name=ge(self.off_bn_e) or None,
                parents_married_in_church=1 if self.married_cb.isChecked() else 0,
            )
            data.update(self.father.data("father"))
            data.update(self.mother.data("mother"))
            data.update(self.godparent.data("godparent"))
            self.db.create_baptism(data)

            if self.comm_cb.isChecked():
                cno = ge(self.comm_no_e)
                if cno:
                    self.db.create_communion_record(dict(
                        communion_no=cno, member_id=self.pno,
                        communion_date=ge(self.comm_date_e) or None,
                        diocese=ge(self.dioc_e) or None,
                        parish=ge(self.church_e) or None,
                    ))

            self._link_parents(self.father, self.mother)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
