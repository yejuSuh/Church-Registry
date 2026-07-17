from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QScrollArea, QFrame, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt

from constants import C
from ui_helpers import fv, mk_btn, mk_entry, mk_combo, mk_check, vbox_field, shdr, ge
from person_picker import PersonPicker, WeddingMatchDialog


# ── Shared building blocks ───────────────────────────────────────────────────

class ApplicantFields(QWidget):
    """The applicant's own info (name/DOB/place of birth/sex/address, plus
    contact+occupation+marital-status for the two adult forms). Pre-filled
    from the member the dialog was opened for; editable so gaps on file can
    be filled in from the paper form."""

    def __init__(self, member, show_contact=True):
        super().__init__()
        ev = lambda k: fv(member, k) if member else ""
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        lay.addWidget(shdr("👤  신청자 정보"))

        body = QWidget()
        g = QGridLayout(body); g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4):
            g.setColumnStretch(col, 1)
        lay.addWidget(body)

        def add(lbl, w, r, c, span=1):
            g.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span)
            return w

        r = 0
        self.kr_e = add("이름 (한글) *", mk_entry(ev("name")), r, 0)
        self.en_e = add("이름 (영문)", mk_entry(ev("name_english")), r, 1)
        self.bn_e = add("세례명", mk_entry(ev("baptismal_name")), r, 2)
        sex_disp = {'M': '남', 'F': '여'}.get(ev("sex"), '')
        self.sex_cb = add("성별", mk_combo(['', '남', '여'], sex_disp), r, 3); r += 1

        self.birth_e = add("생년월일 (YYYY/MM/DD)", mk_entry(ev("birth_date")), r, 0)
        self.pob_e = add("출생지", mk_entry(ev("place_of_birth")), r, 1)
        self.addr_e = add("주소", mk_entry(ev("address")), r, 2, 2); r += 1

        self.phone_e = self.email_e = self.occ_e = self.marital_cb = None
        if show_contact:
            self.phone_e = add("전화", mk_entry(ev("phone_cell")), r, 0)
            self.email_e = add("이메일", mk_entry(ev("email")), r, 1)
            self.occ_e = add("직업", mk_entry(ev("occupation")), r, 2)
            self.marital_cb = add(
                "혼인상태", mk_combo(['미혼', '초혼', '재혼', '이혼', '사별'], ev("marital_status")),
                r, 3,
            ); r += 1

    def data(self):
        sex_db = {'남': 'M', '여': 'F'}.get(ge(self.sex_cb)) or None
        d = dict(
            name_korean=ge(self.kr_e) or None,
            name_english=ge(self.en_e) or None,
            baptismal_name=ge(self.bn_e) or None,
            sex=sex_db,
            birth_date=ge(self.birth_e) or None,
            place_of_birth=ge(self.pob_e) or None,
            address=ge(self.addr_e) or None,
        )
        if self.marital_cb:
            d.update(
                phone_cell=ge(self.phone_e) or None,
                email=ge(self.email_e) or None,
                occupation=ge(self.occ_e) or None,
                marital_status=ge(self.marital_cb) or None,
            )
        return d


class ParentBlock(QWidget):
    """Father/mother field group: a PersonPicker (name + phone) plus that
    parent's own baptism info (date/diocese/parish) -- same column shape on
    both `baptism` and `confirmation`."""

    def __init__(self, db, title):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.picker = PersonPicker(db, title, show_english=True, show_phone=True)
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
        lay.addWidget(shdr("✝  이전 세례 정보"))
        if has_existing:
            note = QLabel("이미 세례 기록이 있어 새로 만들지 않습니다 (세례 기록 탭 참고).")
            note.setObjectName("mu")
            lay.addWidget(note)

        row = QWidget()
        rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(10)
        self.no_e = mk_entry(); rl.addWidget(vbox_field("세례 번호", self.no_e, C['card']), 1)
        self.date_e = mk_entry(); rl.addWidget(vbox_field("세례일", self.date_e, C['card']), 1)
        self.dioc_e = mk_entry(); rl.addWidget(vbox_field("교구", self.dioc_e, C['card']), 1)
        self.par_e = mk_entry(); rl.addWidget(vbox_field("성당", self.par_e, C['card']), 1)
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

    def _link_parents(self, father: ParentBlock, mother: ParentBlock, applicant: ApplicantFields):
        # Decision: when a father/mother match is found, automatically link the
        # child into that household (family.head_of_household/relation) rather
        # than leaving it as a manual follow-up -- see item 4 in the intake
        # forms task. This overwrites the applicant's existing family row.
        father_mid = father.member_id()
        mother_mid = mother.member_id()
        if not (father_mid or mother_mid):
            return
        sex = ge(applicant.sex_cb)
        relation = {'남': '자', '여': '녀'}.get(sex, '자녀')
        head = father.name_korean() if father_mid else mother.name_korean()
        if head:
            self.db.link_child_to_parent(self.pno, head, relation)


class _AdultApplicantDialog(_IntakeDialog):
    """Shared scaffold for the two adult forms (confirmation + RCIA): full
    applicant fields, marital status, and a conditional spouse/marriage
    block that's shown only when marital status is 초혼/재혼."""

    def __init__(self, parent, db, pno, name, title, size, on_save=None):
        super().__init__(parent, db, pno, name, title, size, on_save)
        r = 0
        self.applicant = ApplicantFields(self.member, show_contact=True)
        self.grid.addWidget(self.applicant, r, 0, 1, 4); r += 1

        self.spouse_group = QWidget()
        sl = QVBoxLayout(self.spouse_group); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(6)
        self.spouse = PersonPicker(db, "💍  배우자", show_english=False, show_phone=False)
        sl.addWidget(self.spouse)

        wrow = QWidget()
        wl = QHBoxLayout(wrow); wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(10)
        self.wtype_cb = mk_combo(["(관면)혼배성사", "사회혼"])
        wl.addWidget(vbox_field("혼인 형태", self.wtype_cb, C['card']), 1)
        self.wplace_e = mk_entry()
        wl.addWidget(vbox_field("혼인 장소", self.wplace_e, C['card']), 1)
        self.wdate_e = mk_entry()
        wl.addWidget(vbox_field("혼인일", self.wdate_e, C['card']), 1)
        self.woff_e = mk_entry()
        wl.addWidget(vbox_field("혼인 집전자", self.woff_e, C['card']), 1)
        sl.addWidget(wrow)

        wrow2 = QWidget()
        wl2 = QHBoxLayout(wrow2); wl2.setContentsMargins(0, 0, 0, 0); wl2.setSpacing(10)
        self.wno_e = mk_entry()
        wl2.addWidget(vbox_field("혼인 번호 (신규 생성 시 필요)", self.wno_e, C['card']), 1)
        find_btn = mk_btn("🔍 기존 혼인기록 찾기", "btn_muted")
        find_btn.clicked.connect(self._find_wedding)
        wl2.addWidget(find_btn, 1)
        sl.addWidget(wrow2)

        self.grid.addWidget(self.spouse_group, r, 0, 1, 4); r += 1
        self._matched_wedding_no = None

        self.applicant.marital_cb.currentTextChanged.connect(lambda _: self._on_marital_change())
        self._on_marital_change()

        self._r_after_applicant = r

    def _on_marital_change(self):
        show = ge(self.applicant.marital_cb) in ("초혼", "재혼")
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
        or if married but no wedding_no was given for a new record (spouse
        English name isn't captured here -- `wedding` has no column for it,
        see the note in intake_forms.py's module docstring / task summary)."""
        if marital_status not in ("초혼", "재혼"):
            return None
        if self._matched_wedding_no:
            return self._matched_wedding_no
        spouse_name = self.spouse.kr_e.text().strip()
        wno = ge(self.wno_e)
        if not spouse_name or not wno:
            return None
        sex = ge(self.applicant.sex_cb)
        is_groom = sex == '남'
        wdata = dict(
            wedding_no=wno,
            wedding_date=ge(self.wdate_e) or None,
            wedding_type=ge(self.wtype_cb) or None,
            marriage_place=ge(self.wplace_e) or None,
            officiant_name=ge(self.woff_e) or None,
        )
        applicant_kr = self.applicant.kr_e.text().strip() or None
        applicant_bn = self.applicant.bn_e.text().strip() or None
        spouse_bn = self.spouse.bn_e.text().strip() or None
        if is_groom:
            wdata.update(
                groom_member_id=self.pno, groom_name=applicant_kr, groom_baptismal_name=applicant_bn,
                bride_member_id=self.spouse.member_id, bride_name=spouse_name, bride_baptismal_name=spouse_bn,
            )
        else:
            wdata.update(
                bride_member_id=self.pno, bride_name=applicant_kr, bride_baptismal_name=applicant_bn,
                groom_member_id=self.spouse.member_id, groom_name=spouse_name, groom_baptismal_name=spouse_bn,
            )
        self.db.create_wedding_record(wdata)
        return wno


# ── Form 1: 성인 견진성사 신청서 — Adult Confirmation ────────────────────────

class AdultConfirmationForm(_AdultApplicantDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "성인 견진성사 신청서", (720, 780), on_save)
        r = self._r_after_applicant

        self.prior_baptism = PriorBaptismBlock(has_existing=bool(db.get_baptism_records(pno)))
        self.grid.addWidget(self.prior_baptism, r, 0, 1, 4); r += 1

        self.hdr("🕊  견진 정보", r); r += 1
        self.no_e = self.add("견진 번호 *", mk_entry(), r, 0)
        self.date_e = self.add("견진일 (예정/실시, YYYY/MM/DD)", mk_entry(), r, 1)
        self.dioc_e = self.add("견진 교구", mk_entry(), r, 2)
        self.church_e = self.add("견진 성당", mk_entry(), r, 3); r += 1
        self.off_e = self.add("집전자", mk_entry(), r, 0)
        self.off_bn_e = self.add("집전자 세례명", mk_entry(), r, 1); r += 1

        self.sponsor = PersonPicker(db, "🕊  견진 대부/대모", show_english=True, show_phone=False)
        self.grid.addWidget(self.sponsor, r, 0, 1, 4); r += 1

        self.grid.setRowStretch(r, 1)

    def _save(self):
        try:
            no = ge(self.no_e)
            if not no:
                QMessageBox.warning(self, "오류", "견진 번호를 입력하세요.")
                return

            app_data = self.applicant.data()
            self.db.update_member_fields(self.pno, app_data)
            self.prior_baptism.maybe_create(self.db, self.pno)
            wedding_no = self._resolve_wedding(app_data.get("marital_status"))

            data = dict(
                confirmation_no=no, member_id=self.pno,
                confirmation_date=ge(self.date_e) or None,
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e) or None,
                officiant_baptismal_name=ge(self.off_bn_e) or None,
                wedding_no=wedding_no,
            )
            data.update(self.sponsor.data("sponsor"))
            self.db.create_confirmation_record(data)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 2: 성인 입문성사 신청서 — Adult Initiation (RCIA) ───────────────────

class AdultInitiationForm(_AdultApplicantDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "성인 입문성사 신청서 (RCIA)", (720, 780), on_save)
        r = self._r_after_applicant

        self.fc_cb = mk_check("첫영성체 대상자 (첫영성체가 필요한 경우 체크)")
        self.grid.addWidget(self.fc_cb, r, 0, 1, 4); r += 1

        self.fc_group = QWidget()
        fl = QVBoxLayout(self.fc_group); fl.setContentsMargins(0, 0, 0, 0); fl.setSpacing(10)
        self.prior_baptism = PriorBaptismBlock(has_existing=bool(db.get_baptism_records(pno)))
        self.godparent = PersonPicker(db, "🕊  대부/대모 (첫영성체)", show_english=True, show_phone=False)
        fl.addWidget(self.prior_baptism); fl.addWidget(self.godparent)
        self.fc_cb.toggled.connect(self.fc_group.setVisible)
        self.fc_group.setVisible(False)
        self.grid.addWidget(self.fc_group, r, 0, 1, 4); r += 1

        self.hdr("✝  입문성사 정보", r); r += 1
        self.no_e = self.add("견진 번호 *", mk_entry(), r, 0)
        self.date_e = self.add("예식일 (예정/실시, YYYY/MM/DD)", mk_entry(), r, 1)
        self.dioc_e = self.add("교구", mk_entry(), r, 2)
        self.church_e = self.add("성당", mk_entry(), r, 3); r += 1
        self.off_e = self.add("집전자", mk_entry(), r, 0, 3); r += 1

        self.grid.setRowStretch(r, 1)

    def _save(self):
        try:
            no = ge(self.no_e)
            if not no:
                QMessageBox.warning(self, "오류", "견진 번호를 입력하세요.")
                return

            app_data = self.applicant.data()
            self.db.update_member_fields(self.pno, app_data)
            wedding_no = self._resolve_wedding(app_data.get("marital_status"))

            data = dict(
                confirmation_no=no, member_id=self.pno,
                confirmation_date=ge(self.date_e) or None,
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e) or None,
                wedding_no=wedding_no,
            )
            if self.fc_cb.isChecked():
                self.prior_baptism.maybe_create(self.db, self.pno)
                data.update(self.godparent.data("sponsor"))
            self.db.create_confirmation_record(data)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 3: 유아세례 및 첫영성체 신청서 — Infant Baptism & First Communion ───

class InfantBaptismForm(_IntakeDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "유아세례 및 첫영성체 신청서", (720, 820), on_save)
        r = 0
        self.applicant = ApplicantFields(self.member, show_contact=False)
        self.grid.addWidget(self.applicant, r, 0, 1, 4); r += 1

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

            self.db.update_member_fields(self.pno, self.applicant.data())

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

            self._link_parents(self.father, self.mother, self.applicant)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 4: 청소년 견진성사 신청서 — Youth Confirmation ──────────────────────

class YouthConfirmationForm(_IntakeDialog):
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "청소년 견진성사 신청서", (720, 820), on_save)
        r = 0
        self.applicant = ApplicantFields(self.member, show_contact=False)
        self.grid.addWidget(self.applicant, r, 0, 1, 4); r += 1

        self.prior_baptism = PriorBaptismBlock(has_existing=bool(db.get_baptism_records(pno)))
        self.grid.addWidget(self.prior_baptism, r, 0, 1, 4); r += 1

        self.father = ParentBlock(db, "👨  아버지")
        self.grid.addWidget(self.father, r, 0, 1, 4); r += 1
        self.mother = ParentBlock(db, "👩  어머니")
        self.grid.addWidget(self.mother, r, 0, 1, 4); r += 1

        self.married_cb = mk_check("부모가 혼인성사(성당)로 결혼함")
        self.grid.addWidget(self.married_cb, r, 0, 1, 4); r += 1

        self.sponsor = PersonPicker(db, "🕊  견진 대부/대모", show_english=True, show_phone=False)
        self.grid.addWidget(self.sponsor, r, 0, 1, 4); r += 1

        self.hdr("🕊  견진 정보", r); r += 1
        self.no_e = self.add("견진 번호 *", mk_entry(), r, 0)
        self.date_e = self.add("견진일 (예정/실시, YYYY/MM/DD)", mk_entry(), r, 1)
        self.dioc_e = self.add("견진 교구", mk_entry(), r, 2)
        self.church_e = self.add("견진 성당", mk_entry(), r, 3); r += 1
        self.off_e = self.add("집전자 (주교)", mk_entry(), r, 0, 3); r += 1

        self.grid.setRowStretch(r, 1)

    def _save(self):
        try:
            no = ge(self.no_e)
            if not no:
                QMessageBox.warning(self, "오류", "견진 번호를 입력하세요.")
                return

            self.db.update_member_fields(self.pno, self.applicant.data())
            self.prior_baptism.maybe_create(self.db, self.pno)

            data = dict(
                confirmation_no=no, member_id=self.pno,
                confirmation_date=ge(self.date_e) or None,
                diocese=ge(self.dioc_e) or None,
                parish=ge(self.church_e) or None,
                officiant_name=ge(self.off_e) or None,
                parents_married_in_church=1 if self.married_cb.isChecked() else 0,
            )
            data.update(self.father.data("father"))
            data.update(self.mother.data("mother"))
            data.update(self.sponsor.data("sponsor"))
            self.db.create_confirmation_record(data)

            self._link_parents(self.father, self.mother, self.applicant)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
