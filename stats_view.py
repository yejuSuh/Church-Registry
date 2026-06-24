from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from constants import C


class StatsView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        title = QLabel("현황 통계")
        title.setStyleSheet(f"font-size:18px;font-weight:bold;color:{C['text']};")
        lay.addWidget(title)

        s = self.db.stats()
        cr = QHBoxLayout(); cr.setSpacing(12)
        for label, val, col in [
            ("👥  활성 교인",  s["active"],   C["accent"]),
            ("😴  냉담자",     s["lapsed"],   C["orange"]),
            ("✝  세례 기록",  s["baptisms"], C["success"]),
            ("💒  혼인 기록",  s["weddings"], "#8E44AD"),
        ]:
            card = QWidget(); card.setObjectName("stat_card"); card.setFixedSize(170, 95)
            cl = QVBoxLayout(card); cl.setContentsMargins(8, 8, 8, 8)
            nl = QLabel(str(val)); nl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nl.setStyleSheet(f"font-size:34px;font-weight:bold;color:{col};background:transparent;")
            ll = QLabel(label); ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ll.setStyleSheet(f"font-size:11px;color:{C['muted']};background:transparent;")
            cl.addWidget(nl); cl.addWidget(ll); cr.addWidget(card)
        cr.addStretch()
        lay.addLayout(cr)
        lay.addSpacing(16)

        al = QLabel("구역별 교인 현황")
        al.setStyleSheet(f"font-size:14px;font-weight:bold;color:{C['text']};")
        lay.addWidget(al)
        lay.addSpacing(6)

        for i, row in enumerate(s["areas"]):
            rf = QWidget()
            rf.setStyleSheet(
                f"background:{C['header'] if i % 2 == 0 else C['card']};border-radius:4px;"
            )
            rl = QHBoxLayout(rf); rl.setContentsMargins(12, 4, 12, 4)
            la = QLabel(row["area"] or "—")
            la.setStyleSheet("font-size:12px;background:transparent;")
            lc = QLabel(f"{row['cnt']}명")
            lc.setStyleSheet(
                f"font-size:12px;font-weight:bold;color:{C['accent']};background:transparent;"
            )
            rl.addWidget(la); rl.addStretch(); rl.addWidget(lc)
            lay.addWidget(rf)
        lay.addStretch()
