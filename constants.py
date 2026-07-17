import os
import sys

APP_TITLE  = "보스톤 한인 천주교 | 교적 관리 시스템"

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle — database lives next to the executable
    _DIR = os.path.dirname(sys.executable)
else:
    # Running as a plain Python script
    _DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_DIR, "parish.db")
_ARROW_SVG   = os.path.join(_DIR, "arrow_down.svg").replace("\\", "/")

# ── Design tokens ─────────────────────────────────────────────────────────────
C = dict(
    bg="#F4F6F9", card="#FFFFFF", sidebar="#2D4A6A", accent="#7090B5",
    accent_dk="#4A6A8A", success="#1D6A72", danger="#8C2D3A",
    header="#EDF1F7", border="#D0D8E4", text="#1A1A2E", muted="#6B7280",
    orange="#E67E22", white="#FFFFFF", row_alt="#F8FAFC", plum="#8E44AD",
)

# Body/UI face: a real designed sans on each platform (Segoe UI on Windows,
# Apple SD Gothic Neo on macOS handles Hangul natively) instead of Arial,
# which was the single most generic choice available and rendered Korean
# via whatever fallback the OS happened to pick.
FONT_UI = "'Segoe UI','Apple SD Gothic Neo','Malgun Gothic',Arial,sans-serif"
# Ledger face: used narrowly, only for the registration-number "seal chip"
# and a couple of wordmark moments -- restrained on purpose, see ui_helpers.mk_regno.
FONT_LEDGER = "Georgia,'Apple SD Gothic Neo',serif"

# Single source of truth for button corner radius. A few buttons can't be
# styled through the shared #btn_* rules below (they need dynamic per-state
# styling applied in Python -- the forgot-password tab switcher, the detail
# panel's close button) but should still look like they belong to the same
# system, so they import this constant instead of hardcoding their own value.
BTN_RADIUS = "3px"

SS = f"""
QWidget{{background:{C['bg']};color:{C['text']};font-family:{FONT_UI};font-size:13px;}}
#sidebar{{background:{C['sidebar']};}}
#sidebar QLabel{{color:{C['white']};background:transparent;}}
#sidebar QPushButton{{background:transparent;color:{C['white']};border:none;
  text-align:left;padding:10px 16px;font-size:13px;border-radius:{BTN_RADIUS};}}
#sidebar QPushButton:hover{{background:{C['accent']};}}
#card,QDialog{{background:{C['card']};}}
#toolbar{{background:{C['card']};border-bottom:1px solid {C['border']};}}
#filterbar{{background:{C['header']};border-bottom:1px solid {C['border']};}}
/* Flat, text-forward buttons: only the single primary action per screen
   (btn_accent) gets a solid fill. Everything else -- repeated "+ 추가"
   actions, cancel, delete -- is a quiet outline/ghost button that leans on
   color and weight for hierarchy instead of a heavy color block, so a
   record-dense screen with five "+ 추가" buttons doesn't read as five
   equally-loud CTAs. */
/* Every button gets a 1px border -- transparent on the solid-fill accent
   button, colored on the outline ones -- so Qt's box model (border sits
   outside the padding, unlike CSS border-box) doesn't make the outlined
   buttons 2px taller/wider than accent when they sit in the same row. */
QPushButton{{border-radius:{BTN_RADIUS};padding:6px 14px;font-size:13px;
  border:1px solid transparent;cursor:pointer;}}
QPushButton#btn_accent{{background:{C['accent']};color:white;font-weight:bold;}}
QPushButton#btn_accent:hover{{background:{C['accent_dk']};}}
QPushButton#btn_success{{background:transparent;color:{C['success']};font-weight:bold;
  border-color:{C['success']};}}
QPushButton#btn_success:hover{{background:#E8F0F1;}}
QPushButton#btn_danger{{background:transparent;color:{C['danger']};font-weight:bold;
  border-color:{C['danger']};}}
QPushButton#btn_danger:hover{{background:#F4EAEB;}}
QPushButton#btn_muted{{background:transparent;color:{C['muted']};border-color:{C['border']};}}
QPushButton#btn_muted:hover{{background:{C['header']};color:{C['text']};}}
QLineEdit,QComboBox,QTextEdit{{background:{C['card']};border:1px solid {C['border']};
  border-radius:5px;padding:5px 8px;font-size:13px;}}
QLineEdit:focus,QComboBox:focus,QTextEdit:focus{{border:1.5px solid {C['accent']};}}
QComboBox::drop-down{{subcontrol-origin:padding;subcontrol-position:top right;width:26px;background:{C['header']};border-left:1px solid {C['border']};border-top-right-radius:4px;border-bottom-right-radius:4px;}}
QComboBox::down-arrow{{image:url({_ARROW_SVG});width:10px;height:6px;}}
QComboBox::drop-down:hover{{background:{C['border']};}}
QComboBox QAbstractItemView{{background:{C['card']};color:{C['text']};
  border:1px solid {C['border']};border-radius:5px;padding:4px;outline:0;
  selection-background-color:{C['accent']};selection-color:white;}}
QComboBox QAbstractItemView::item{{padding:5px 8px;border-radius:3px;min-height:20px;}}
QComboBox QAbstractItemView::item:hover{{background:{C['header']};}}
QTableWidget{{background:{C['card']};gridline-color:{C['border']};border:none;font-size:13px;outline:0;}}
QTableWidget::item{{padding:4px 8px;border:none;}}
QTableWidget::item:selected{{background:{C['accent']};color:white;}}
QHeaderView::section{{background:{C['header']};color:{C['sidebar']};font-weight:bold;
  padding:6px 8px;border:none;border-right:1px solid {C['border']};border-bottom:1px solid {C['border']};}}
#section_hdr{{background:{C['header']};border-left:3px solid {C['accent']};color:{C['sidebar']};
  font-family:{FONT_LEDGER};font-weight:bold;padding:4px 10px 4px 8px;}}
#stat_card{{background:{C['card']};border:1px solid {C['border']};border-radius:10px;}}
#detail_hdr{{background:{C['accent']};}}
#detail_hdr QLabel{{color:white;background:transparent;}}
/* No chip/box -- just the seal-face typography (see ui_helpers.mk_regno)
   set directly against the header, inheriting the white text color from
   the #detail_hdr QLabel rule above. */
QLabel#regno{{background:transparent;border:none;padding:0;}}
#detail_btnbar{{background:{C['header']};border-bottom:1px solid {C['border']};}}
QScrollBar:vertical{{background:{C['bg']};width:8px;border-radius:4px;}}
QScrollBar::handle:vertical{{background:{C['border']};border-radius:4px;min-height:30px;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar:horizontal{{height:0;}}
QCheckBox{{background:transparent;spacing:6px;margin-left:4px;}}
QLabel#fl{{color:{C['muted']};font-size:11px;background:transparent;}}
QLabel#fv{{color:{C['text']};font-size:13px;background:transparent;}}
QLabel#mu{{color:{C['muted']};font-size:11px;background:transparent;}}
QTabWidget::pane{{border:none;background:{C['card']};}}
QTabBar{{background:{C['header']};}}
QTabBar::tab{{background:{C['header']};color:{C['muted']};padding:7px 18px;
  border:none;border-bottom:2px solid transparent;font-size:13px;margin-right:2px;}}
QTabBar::tab:selected{{color:{C['accent']};background:{C['card']};
  border-bottom:2px solid {C['accent']};font-weight:bold;}}
QTabBar::tab:hover:!selected{{background:{C['border']};}}
"""

AREAS = [
    ("00101","평화/동부"),("00102","기쁨/서부"),("00103","선행/남부"),
    ("00104","진실/북부 1"),("00105","온유/북부 2"),("00106","인내/중부"),
    ("00107","절제/내슈아"),("00108","친절/에이어"),("00109","반석회"),
    ("00110","청년회"),("00111","스프링필드 공소"),("00112","무소속"),
]
AREA_MAP  = {a[0]: a[1] for a in AREAS}
AREA_DISP = [f"{a[0]}  {a[1]}" for a in AREAS]
RELATIONS = [
    "본인","처","남편","자","녀","부","모","형","오빠","누나","언니",
    "남동생","여동생","조부","조모","손자","손녀","외손자","외손녀",
    "장인","장모","시부","시모","삼촌","고모","이모","사위","자부","기타",
]
