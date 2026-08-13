from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QTabWidget,
    QGridLayout,
)
from PyQt6.QtCore import Qt

from core.constants import C
from ui.ui_helpers import fv, mk_btn, mk_entry, mk_combo, vbox_field, ge


class _MemberSearch(QWidget):
    """Optional member search: links to a registered member or falls back to free-text name.

    Either path is valid on save. member_id is None for non-member records;
    get_name() always returns a usable display name.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.member_id = None

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)

        # search row: type to find existing member
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(6)
        self.search_e = mk_entry()
        self.search_e.setPlaceholderText("등록 신자 검색 (이름/세례명) — 없으면 아래에 직접 입력")
        self.unlink_btn = mk_btn("연결 해제", "btn_muted")
        self.unlink_btn.setFixedWidth(76); self.unlink_btn.setVisible(False)
        row.addWidget(self.search_e, 1); row.addWidget(self.unlink_btn)
        lay.addLayout(row)

        self.results = QListWidget(); self.results.setFixedHeight(80)
        self.results.setVisible(False)
        lay.addWidget(self.results)

        # linked-member badge (shown after selection)
        self.linked_lbl = QLabel(); self.linked_lbl.setObjectName("mu")
        self.linked_lbl.setStyleSheet(f"color:{C['success']};font-weight:bold;background:transparent;")
        self.linked_lbl.setVisible(False)
        lay.addWidget(self.linked_lbl)

        # free-text name field (always visible; locked when a member is linked)
        self.name_e = mk_entry()
        self.name_e.setPlaceholderText("이름 *")
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

    def reset(self):
        self.member_id = None
        self.search_e.clear()
        self.results.setVisible(False)
        self.linked_lbl.setVisible(False)
        self.unlink_btn.setVisible(False)
        self.name_e.clear(); self.name_e.setEnabled(True)

    def get_name(self):
        return self.name_e.text().strip()


def _tab_shell(content_fn):
    """Wrap a content-building function in a scroll area."""
    outer = QWidget()
    scroll = QScrollArea(); scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    body = QWidget(); body.setObjectName("card")
    scroll.setWidget(body)
    lay = QVBoxLayout(body); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
    vl = QVBoxLayout(outer); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)
    vl.addWidget(scroll)
    content_fn(lay)
    lay.addStretch()
    return outer


def _field_grid(parent_lay, rows):
    """Add a QGridLayout of vbox_field widgets; rows is list of (label, widget, col, span)."""
    g = QGridLayout(); g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
    for col in range(4): g.setColumnStretch(col, 1)
    r = 0; col = 0
    for label, widget, span in rows:
        g.addWidget(vbox_field(label, widget, C["card"]), r, col, 1, span)
        col += span
        if col >= 4: col = 0; r += 1
    parent_lay.addLayout(g)


class SacramentEntryView(QWidget):
    """Independent sacrament creation page; each tab creates one type of record."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        hdr = QWidget(); hdr.setObjectName("toolbar"); hdr.setFixedHeight(48)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("성사 기록 추가"); title.setStyleSheet("font-size:15px;font-weight:bold;")
        hl.addWidget(title); hl.addStretch()
        outer.addWidget(hdr)

        tabs = QTabWidget()
        tabs.addTab(self._baptism_tab(),      "✝  세례")
        tabs.addTab(self._confirmation_tab(), "🕊  견진")
        tabs.addTab(self._wedding_tab(),      "💒  혼인")
        tabs.addTab(self._communion_tab(),    "🍞  첫영성체")
        tabs.addTab(self._movein_tab(),       "📥  전입")
        tabs.addTab(self._moveout_tab(),      "📤  전출")
        tabs.addTab(self._death_tab(),        "✟  사망")
        outer.addWidget(tabs, 1)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _save_btn(self, lay, callback):
        bb = QWidget(); bl = QHBoxLayout(bb); bl.setContentsMargins(0, 8, 0, 0)
        bl.addStretch()
        btn = mk_btn("💾  저장", "btn_accent"); btn.setFixedWidth(100)
        btn.clicked.connect(callback); bl.addWidget(btn)
        lay.addWidget(bb)

    def _check_name(self, picker, parent):
        """Return True if a name is available (member linked or free-text entered)."""
        if not picker.get_name():
            QMessageBox.warning(parent, "이름 필요", "신자를 선택하거나 이름을 직접 입력하세요.")
            return False
        return True

    def _check_member(self, picker, parent):
        """Return True only when a registered member is linked (required for move/death)."""
        if not picker.member_id:
            QMessageBox.warning(parent, "신자 미선택", "신자를 검색해서 선택하세요.")
            return False
        return True

    def _ok(self, picker, *entries):
        """Clear picker + entry fields after a successful save."""
        picker.reset()
        for e in entries:
            if hasattr(e, "clear"): e.clear()
            elif hasattr(e, "setCurrentIndex"): e.setCurrentIndex(0)

    # ── 세례 ─────────────────────────────────────────────────────────────────

    def _baptism_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e  = mk_entry(); dioc_e  = mk_entry()
            par_e   = mk_entry(); off_e   = mk_entry()
            _field_grid(lay, [
                ("세례일 (YYYY/MM/DD)", date_e, 1),
                ("교구",                dioc_e, 1),
                ("세례 성당",           par_e,  1),
                ("집전자",              off_e,  1),
            ])
            def save():
                if not self._check_name(ms, self): return
                data = dict(
                    member_id=ms.member_id,
                    date=ge(date_e) or None,
                    diocese=ge(dioc_e) or None,
                    parish=ge(par_e) or None,
                    officiant_name=ge(off_e) or None,
                )
                if not ms.member_id:
                    data["person_name"] = ms.get_name()
                self.db.create_baptism(data)
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 세례 기록이 저장되었습니다.")
                self._ok(ms, date_e, dioc_e, par_e, off_e)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 견진 ─────────────────────────────────────────────────────────────────

    def _confirmation_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e  = mk_entry(); cname_e = mk_entry()
            dioc_e  = mk_entry(); par_e   = mk_entry(); off_e = mk_entry()
            _field_grid(lay, [
                ("견진일 (YYYY/MM/DD)", date_e,  1),
                ("견진명",              cname_e, 1),
                ("교구",                dioc_e,  1),
                ("견진 성당",           par_e,   1),
                ("집전자",              off_e,   2),
            ])
            def save():
                if not self._check_name(ms, self): return
                data = dict(
                    member_id=ms.member_id,
                    date=ge(date_e) or None,
                    confirmation_name=ge(cname_e) or None,
                    diocese=ge(dioc_e) or None,
                    parish=ge(par_e) or None,
                    officiant_name=ge(off_e) or None,
                )
                if not ms.member_id:
                    data["person_name"] = ms.get_name()
                self.db.create_confirmation_record(data)
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 견진 기록이 저장되었습니다.")
                self._ok(ms, date_e, cname_e, dioc_e, par_e, off_e)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 혼인 ─────────────────────────────────────────────────────────────────

    def _wedding_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            role_cb  = mk_combo(["신랑", "신부"])
            spouse_e = mk_entry()
            date_e   = mk_entry()
            type_cb  = mk_combo(["성사혼", "관면혼", "단순유효화혼", "바오로특전혼", "근본유효화혼", "기타"])
            off_e    = mk_entry()

            # '기타' type → show free-text field
            other_row = QWidget(); orl = QHBoxLayout(other_row)
            orl.setContentsMargins(0, 0, 0, 0)
            type_other_e = mk_entry(); type_other_e.setPlaceholderText("혼인 형태 직접 입력")
            orl.addWidget(vbox_field("형태 직접입력", type_other_e, C["card"]))
            other_row.setVisible(False)
            type_cb.currentTextChanged.connect(lambda t: other_row.setVisible(t == "기타"))

            _field_grid(lay, [
                ("역할",               role_cb,  1),
                ("배우자 이름",         spouse_e, 1),
                ("혼인일 (YYYY/MM/DD)", date_e,   1),
                ("혼인 형태",           type_cb,  1),
                ("집전자",              off_e,    2),
            ])
            lay.addWidget(other_row)

            def save():
                if not self._check_name(ms, self): return
                is_groom = ge(role_cb) == "신랑"
                wtype = ge(type_cb)
                name = ms.get_name()
                data = dict(
                    date=ge(date_e) or None,
                    wedding_type=wtype,
                    officiant_name=ge(off_e) or None,
                )
                if wtype == "기타":
                    data["type_other"] = ge(type_other_e) or None
                if is_groom:
                    data["groom_id"] = ms.member_id; data["groom_name"] = name
                    data["bride_name"] = ge(spouse_e)
                else:
                    data["bride_id"] = ms.member_id; data["bride_name"] = name
                    data["groom_name"] = ge(spouse_e)
                self.db.create_wedding_record(data)
                QMessageBox.information(self, "저장 완료", f"{name} 혼인 기록이 저장되었습니다.")
                self._ok(ms, date_e, spouse_e, off_e, type_other_e)
                type_cb.setCurrentIndex(0); role_cb.setCurrentIndex(0)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 첫영성체 ─────────────────────────────────────────────────────────────

    def _communion_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e = mk_entry(); dioc_e = mk_entry()
            par_e  = mk_entry(); off_e  = mk_entry()
            _field_grid(lay, [
                ("첫영성체일 (YYYY/MM/DD)", date_e, 1),
                ("교구",                    dioc_e, 1),
                ("성당",                    par_e,  1),
                ("집전자",                  off_e,  1),
            ])
            def save():
                if not self._check_name(ms, self): return
                data = dict(
                    member_id=ms.member_id,
                    date=ge(date_e) or None,
                    diocese=ge(dioc_e) or None,
                    parish=ge(par_e) or None,
                    officiant_name=ge(off_e) or None,
                )
                if not ms.member_id:
                    data["person_name"] = ms.get_name()
                self.db.create_communion_record(data)
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 첫영성체 기록이 저장되었습니다.")
                self._ok(ms, date_e, dioc_e, par_e, off_e)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 전입 ─────────────────────────────────────────────────────────────────

    def _movein_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e = mk_entry(); dioc_e = mk_entry(); par_e = mk_entry(); addr_e = mk_entry()
            _field_grid(lay, [
                ("전입일 (YYYY/MM/DD)", date_e, 1),
                ("이전 교구",           dioc_e, 1),
                ("이전 성당",           par_e,  1),
                ("이전 성당 주소",       addr_e, 4),
            ])
            def save():
                if not self._check_member(ms, self): return
                self.db.create_movein_record(dict(
                    member_id=ms.member_id,
                    date=ge(date_e) or None,
                    former_diocese=ge(dioc_e) or None,
                    former_parish=ge(par_e) or None,
                    former_address=ge(addr_e) or None,
                ))
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 전입 기록이 저장되었습니다.")
                self._ok(ms, date_e, dioc_e, par_e, addr_e)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 전출 ─────────────────────────────────────────────────────────────────

    def _moveout_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e = mk_entry(); dioc_e = mk_entry(); par_e = mk_entry(); addr_e = mk_entry()
            _field_grid(lay, [
                ("전출일 (YYYY/MM/DD)", date_e, 1),
                ("새 교구",             dioc_e, 1),
                ("새 성당",             par_e,  1),
                ("새 성당 주소",         addr_e, 4),
            ])
            def save():
                if not self._check_member(ms, self): return
                self.db.create_moveout_record(dict(
                    member_id=ms.member_id,
                    date=ge(date_e) or None,
                    dest_diocese=ge(dioc_e) or None,
                    dest_parish=ge(par_e) or None,
                    dest_address=ge(addr_e) or None,
                ))
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 전출 기록이 저장되었습니다.")
                self._ok(ms, date_e, dioc_e, par_e, addr_e)
            self._save_btn(lay, save)
        return _tab_shell(build)

    # ── 사망 ─────────────────────────────────────────────────────────────────

    def _death_tab(self):
        def build(lay):
            ms = _MemberSearch(self.db); lay.addWidget(ms)
            date_e  = mk_entry(); place_e = mk_entry(); rites_e = mk_entry()
            _field_grid(lay, [
                ("사망일 (YYYY/MM/DD)",   date_e,  1),
                ("장소 (묘지)",           place_e, 2),
                ("종부성사일 (YYYY/MM/DD)", rites_e, 2),
            ])
            def save():
                if not self._check_member(ms, self): return
                self.db.create_death_record(dict(
                    member_id=ms.member_id,
                    date_death=ge(date_e) or None,
                    cemetery=ge(place_e) or None,
                    last_rites_date=ge(rites_e) or None,
                ))
                QMessageBox.information(self, "저장 완료", f"{ms.get_name()} 사망 기록이 저장되었습니다.")
                self._ok(ms, date_e, place_e, rites_e)
            self._save_btn(lay, save)
        return _tab_shell(build)
