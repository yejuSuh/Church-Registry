import os

APP_TITLE  = "보스톤 한인 천주교 | 교적 관리 시스템"

_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_FILES = sorted(f for f in os.listdir(_DIR) if f.endswith(".sqlite"))
DB_PATH      = os.path.join(_DIR, SQLITE_FILES[0]) if SQLITE_FILES else os.path.join(_DIR, "church_registry.sqlite")
_ARROW_SVG = os.path.join(_DIR, "arrow_down.svg").replace("\\", "/")

C = dict(
    bg="#F4F6F9", card="#FFFFFF", sidebar="#2D4A6A", accent="#7090B5",
    accent_dk="#4A6A8A", success="#1D6A72", danger="#8C2D3A",
    header="#EDF1F7", border="#D0D8E4", text="#1A1A2E", muted="#6B7280",
    orange="#E67E22", white="#FFFFFF", row_alt="#F8FAFC",
)

SS = f"""
QWidget{{background:{C['bg']};color:{C['text']};font-family:Arial;font-size:13px;}}
#sidebar{{background:{C['sidebar']};}}
#sidebar QLabel{{color:{C['white']};background:transparent;}}
#sidebar QPushButton{{background:transparent;color:{C['white']};border:none;
  text-align:left;padding:10px 16px;font-size:13px;border-radius:6px;}}
#sidebar QPushButton:hover{{background:{C['accent']};}}
#card,QDialog{{background:{C['card']};}}
#toolbar{{background:{C['card']};border-bottom:1px solid {C['border']};}}
#filterbar{{background:{C['header']};border-bottom:1px solid {C['border']};}}
QPushButton{{border-radius:5px;padding:6px 14px;font-size:13px;border:none;cursor:pointer;}}
QPushButton#btn_accent{{background:{C['accent']};color:white;font-weight:bold;}}
QPushButton#btn_accent:hover{{background:{C['accent_dk']};}}
QPushButton#btn_success{{background:{C['success']};color:white;}}
QPushButton#btn_success:hover{{background:#145A5E;}}
QPushButton#btn_danger{{background:{C['danger']};color:white;}}
QPushButton#btn_danger:hover{{background:#922B21;}}
QPushButton#btn_muted{{background:{C['border']};color:{C['text']};}}
QPushButton#btn_muted:hover{{background:#C8CDD5;}}
QLineEdit,QComboBox,QTextEdit{{background:{C['card']};border:1px solid {C['border']};
  border-radius:5px;padding:5px 8px;font-size:13px;}}
QLineEdit:focus,QComboBox:focus,QTextEdit:focus{{border:1.5px solid {C['accent']};}}
QComboBox::drop-down{{subcontrol-origin:padding;subcontrol-position:top right;width:26px;background:{C['header']};border-left:1px solid {C['border']};border-top-right-radius:4px;border-bottom-right-radius:4px;}}
QComboBox::down-arrow{{image:url({_ARROW_SVG});width:10px;height:6px;}}
QComboBox::drop-down:hover{{background:{C['border']};}}
QTableWidget{{background:{C['card']};gridline-color:{C['border']};border:none;font-size:13px;outline:0;}}
QTableWidget::item{{padding:4px 8px;border:none;}}
QTableWidget::item:selected{{background:{C['accent']};color:white;}}
QHeaderView::section{{background:{C['header']};color:{C['accent']};font-weight:bold;
  padding:6px 8px;border:none;border-right:1px solid {C['border']};border-bottom:1px solid {C['border']};}}
#section_hdr{{background:{C['header']};border-radius:4px;color:{C['accent']};
  font-weight:bold;padding:4px 10px;}}
#stat_card{{background:{C['card']};border:1px solid {C['border']};border-radius:10px;}}
#detail_hdr{{background:{C['accent']};}}
#detail_hdr QLabel{{color:white;background:transparent;}}
#detail_btnbar{{background:{C['header']};border-bottom:1px solid {C['border']};}}
QScrollBar:vertical{{background:{C['bg']};width:8px;border-radius:4px;}}
QScrollBar::handle:vertical{{background:{C['border']};border-radius:4px;min-height:30px;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar:horizontal{{height:0;}}
QCheckBox{{background:transparent;spacing:4px;margin-left:4px;}}
QCheckBox::indicator{{width:12px;height:12px;border:1.5px solid {C['border']};border-radius:3px;background:{C['card']};}}
QCheckBox::indicator:checked{{background:{C['accent']};border-color:{C['accent']};image:none;}}
QCheckBox::indicator:hover{{border-color:{C['accent']};}}
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
