from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QScrollArea, QFrame, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt

from constants import C, AREA_DISP, RELATIONS
from ui_helpers import fv, mk_btn, shdr, vbox_field, mk_entry, mk_combo, mk_check, ge


class ParishionerForm(QDialog):
    def __init__(self, parent, db, pno=None, on_save=None, prefill_host="", prefill_area=""):
        super().__init__(parent)
        self.db = db
        self.pno = pno
        self.on_save = on_save
        self.setWindowTitle("교적 추가" if not pno else "교적 수정")
        self.resize(860, 700)
        self.setModal(True)

        existing = db.get(pno) if pno else None
        ev = lambda k: fv(existing, k) if existing else ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("card")
        scroll.setWidget(body)
        grid = QGridLayout(body)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        outer.addWidget(scroll, 1)

        r = 0

        def add(label, widget, row, col, span=1):
            grid.addWidget(vbox_field(label, widget, C['card']), row, col, 1, span)
            return widget

        grid.addWidget(shdr("📋  기본 정보"), r, 0, 1, 4); r += 1

        if existing:
            cur_area = next((d for d in AREA_DISP if d.startswith(ev("parishioner_no")[:5])), AREA_DISP[-1])
        elif prefill_area:
            cur_area = next((d for d in AREA_DISP if d.startswith(prefill_area)), AREA_DISP[-1])
        else:
            cur_area = AREA_DISP[-1]

        self.area_cb = mk_combo(AREA_DISP, cur_area)
        self.no_le = QLineEdit(ev("parishioner_no") if existing else "")
        self.no_le.setReadOnly(True)
        self.no_le.setStyleSheet(f"background:{C['header']};color:{C['muted']};")
        grid.addWidget(vbox_field("구역 *", self.area_cb, C['card']), r, 0, 1, 2)
        grid.addWidget(vbox_field("교적번호 (자동 생성)", self.no_le, C['card']), r, 2, 1, 2); r += 1

        self.name_e  = add("이름 *",       mk_entry(ev("name")),                                         r, 0)
        self.host_e  = add("세대주 이름 *", mk_entry(ev("host_nm") if existing else prefill_host),       r, 1)
        self.rel_cb  = add("관계 *",        mk_combo(RELATIONS, ev("relation") if existing else "본인"),  r, 2)
        self.bname_e = add("세례명",        mk_entry(ev("baptism_nm")),                                   r, 3); r += 1
        self.bday_e  = add("축일 (MM/DD)",      mk_entry(ev("baptism_day")),     r, 0)
        self.pid_e   = add("생년월일",           mk_entry(ev("personal_no")),    r, 1)
        self.reg_e   = add("등록일 (YYYY/MM/DD)", mk_entry(ev("registion_date")), r, 2); r += 1

        grid.addWidget(shdr("상태 플래그"), r, 0, 1, 4); r += 1
        self.etemal_cb = mk_check("영원한 교적", ev("etemal"))
        self.duty_cb   = mk_check("교무금 납부",  ev("money_duty_flag"))
        self.lazy_cb   = mk_check("냉담자",       ev("lazy_flag"))
        self.alone_cb  = mk_check("독거",         ev("alone_flag"))
        fw = QWidget(); fw.setObjectName("card")
        fl = QHBoxLayout(fw); fl.setContentsMargins(4, 2, 4, 2)
        for cb in [self.etemal_cb, self.duty_cb, self.lazy_cb, self.alone_cb]:
            fl.addWidget(cb)
        fl.addStretch()
        grid.addWidget(fw, r, 0, 1, 4); r += 1

        grid.addWidget(shdr("📞  연락처 & 주소"), r, 0, 1, 4); r += 1
        self.telh_e  = add("집 전화",   mk_entry(ev("tel_home")),   r, 0)
        self.telm_e  = add("휴대폰",    mk_entry(ev("tel_hp")),     r, 1)
        self.telo_e  = add("직장 전화", mk_entry(ev("tel_office")), r, 2); r += 1
        self.addr_e  = add("주소",      mk_entry(ev("address")),    r, 0, 2)
        self.addrn_e = add("상세 주소", mk_entry(ev("address_no")), r, 2, 2); r += 1

        grid.addWidget(shdr("✝  세례 정보"), r, 0, 1, 4); r += 1
        self.bp_nm_e = add("세례 교구",           mk_entry(ev("baptism_parish_nm")), r, 0)
        self.bp_ch_e = add("세례 성당",           mk_entry(ev("baptism_church")),    r, 1)
        self.bp_dt_e = add("세례일 (YYYY/MM/DD)", mk_entry(ev("baptism_date")),      r, 2)
        self.bp_no_e = add("세례 번호",           mk_entry(ev("baptism_no")),        r, 3); r += 1

        grid.addWidget(shdr("🕊  견진 정보"), r, 0, 1, 4); r += 1
        self.sp_nm_e = add("견진 교구",           mk_entry(ev("sacrament_parish_nm")), r, 0)
        self.sp_ch_e = add("견진 성당",           mk_entry(ev("sacrament_church")),    r, 1)
        self.sp_dt_e = add("견진일 (YYYY/MM/DD)", mk_entry(ev("sacrament_date")),      r, 2); r += 1

        grid.addWidget(shdr("💼  직장 / 이전 소속"), r, 0, 1, 4); r += 1
        self.ofnm_e   = add("직장명",    mk_entry(ev("office_nm")),         r, 0)
        self.jknd_e   = add("직종",      mk_entry(ev("job_kind")),          r, 1)
        self.pre_nm_e = add("이전 교구", mk_entry(ev("pre_parish_nm")),     r, 2)
        self.pre_ch_e = add("이전 성당", mk_entry(ev("pre_parish_church")), r, 3); r += 1

        grid.addWidget(shdr("📝  메모"), r, 0, 1, 4); r += 1
        self.memo_te = QTextEdit()
        self.memo_te.setFixedHeight(80)
        self.memo_te.setPlainText(ev("personal_memo"))
        grid.addWidget(vbox_field("메모", self.memo_te, C['card']), r, 0, 1, 4); r += 1
        grid.setRowStretch(r, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8)
        bbl.addStretch()
        cancel_b = mk_btn("취소", "btn_muted")
        save_b   = mk_btn("💾  저장", "btn_accent")
        cancel_b.clicked.connect(self.reject)
        save_b.clicked.connect(self._save)
        bbl.addWidget(cancel_b); bbl.addWidget(save_b)
        outer.addWidget(bb)

    def _save(self):
        name = ge(self.name_e)
        host = ge(self.host_e)
        if not name:
            QMessageBox.warning(self, "오류", "이름을 입력하세요.")
            return
        if not host:
            QMessageBox.warning(self, "오류", "세대주 이름을 입력하세요.")
            return
        area_code = ge(self.area_cb).split()[0]
        pno = self.pno if self.pno else self.db.next_no(area_code)
        data = dict(
            parishioner_no=pno, name=name, host_nm=host,
            relation=ge(self.rel_cb), baptism_nm=ge(self.bname_e),
            baptism_day=ge(self.bday_e), personal_no=ge(self.pid_e),
            registion_date=ge(self.reg_e),
            etemal="Y" if self.etemal_cb.isChecked() else "N",
            money_duty_flag="Y" if self.duty_cb.isChecked() else "N",
            lazy_flag="Y" if self.lazy_cb.isChecked() else "N",
            alone_flag="Y" if self.alone_cb.isChecked() else "N",
            tel_home=ge(self.telh_e), tel_hp=ge(self.telm_e), tel_office=ge(self.telo_e),
            address=ge(self.addr_e), address_no=ge(self.addrn_e),
            baptism_parish_nm=ge(self.bp_nm_e), baptism_church=ge(self.bp_ch_e),
            baptism_date=ge(self.bp_dt_e), baptism_no=ge(self.bp_no_e),
            sacrament_parish_nm=ge(self.sp_nm_e), sacrament_church=ge(self.sp_ch_e),
            sacrament_date=ge(self.sp_dt_e),
            office_nm=ge(self.ofnm_e), job_kind=ge(self.jknd_e),
            pre_parish_nm=ge(self.pre_nm_e), pre_parish_church=ge(self.pre_ch_e),
            personal_memo=ge(self.memo_te),
        )
        try:
            if self.pno:
                del data["parishioner_no"]
                self.db.update(self.pno, data)
            else:
                self.db.create(data)
            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
