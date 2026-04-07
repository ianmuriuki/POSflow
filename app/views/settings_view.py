"""
app/views/settings_view.py
---------------------------
Settings — clean, minimalist, professional.
No box-in-a-box. Cards with soft shadows only.
"""
import logging, shutil, os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QStackedWidget, QFileDialog,
    QScrollArea, QSpinBox, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from app.config import CONFIG
from app.database import get_db_path
from app.utils.theme import Th

logger = logging.getLogger(__name__)


# ── Design tokens ────────────────────────────────────────────────
BG_PAGE    = "#F0F2F5"
BG_CARD    = "#FFFFFF"
BG_INPUT   = "#F8FAFC"
BORDER_IN  = "#E2E8F0"
TEXT_LABEL = "#94A3B8"    # small muted labels
TEXT_BODY  = "#1E293B"
TEXT_HINT  = "#94A3B8"
ACCENT     = "#1B3F6E"
ACCENT_HV  = "#2563A8"


# ── Reusable atoms ────────────────────────────────────────────────

def _card(parent=None) -> tuple:
    """Returns (QFrame card, QVBoxLayout inner_layout)"""
    c = QFrame(parent)
    c.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border-radius: 12px;
            border: none;
        }}
    """)
    c.setGraphicsEffect(Th.shadow(20, 3, 10))
    lo = QVBoxLayout(c)
    lo.setContentsMargins(28, 24, 28, 28)
    lo.setSpacing(0)
    return c, lo


def _card_title(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"""
        font-size: 15px;
        font-weight: 700;
        color: {TEXT_BODY};
        background: transparent;
    """)
    return l


def _card_divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{BORDER_IN}; border:none; margin: 16px 0;")
    return f


def _field_label(text: str) -> QLabel:
    """Small uppercase muted label — sits ABOVE the input."""
    l = QLabel(text.upper())
    l.setStyleSheet(f"""
        font-size: 10px;
        font-weight: 700;
        color: {TEXT_LABEL};
        letter-spacing: 0.8px;
        background: transparent;
        margin-bottom: 6px;
    """)
    return l


def _field_hint(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"""
        font-size: 11px;
        color: {TEXT_HINT};
        background: transparent;
        margin-top: 4px;
    """)
    return l


def _input(value="", placeholder="", readonly=False) -> QLineEdit:
    f = QLineEdit(value)
    f.setPlaceholderText(placeholder)
    f.setFixedHeight(44)
    f.setReadOnly(readonly)
    f.setStyleSheet(f"""
        QLineEdit {{
            background: {BG_INPUT if not readonly else '#F1F5F9'};
            border: 1.5px solid {BORDER_IN};
            border-radius: 8px;
            padding: 0 14px;
            font-size: 13px;
            color: {TEXT_BODY};
            font-family: 'Segoe UI', 'Inter', Arial;
        }}
        QLineEdit:focus {{
            border-color: {ACCENT};
            background: white;
            outline: none;
        }}
        QLineEdit:read-only {{
            color: {TEXT_LABEL};
        }}
    """)
    return f


def _spinbox(min_v=5, max_v=480, suffix=" min") -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_v, max_v)
    s.setSuffix(suffix)
    s.setFixedHeight(44)
    s.setFixedWidth(140)
    s.setStyleSheet(f"""
        QSpinBox {{
            background: {BG_INPUT};
            border: 1.5px solid {BORDER_IN};
            border-radius: 8px;
            padding: 0 14px;
            font-size: 13px;
            color: {TEXT_BODY};
        }}
        QSpinBox:focus {{ border-color: {ACCENT}; background: white; }}
        QSpinBox::up-button, QSpinBox::down-button {{ width: 0; }}
    """)
    return s


def _save_btn(text="Save Changes", full_width=True) -> QPushButton:
    b = QPushButton(text)
    b.setFixedHeight(46)
    if full_width:
        b.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
    else:
        b.setFixedWidth(180)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {ACCENT};
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}
        QPushButton:hover   {{ background: {ACCENT_HV}; }}
        QPushButton:pressed {{ background: #163260; }}
    """)
    return b


def _field_group(label: str, widget, hint: str = "") -> QWidget:
    """
    Stacks:  LABEL (uppercase small)
             INPUT widget
             hint (optional muted text)
    No border around the group — just spacing.
    """
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lo = QVBoxLayout(w)
    lo.setContentsMargins(0, 0, 0, 0)
    lo.setSpacing(0)
    lo.addWidget(_field_label(label))
    lo.addWidget(widget)
    if hint:
        lo.addWidget(_field_hint(hint))
    return w


def _tab_btn(text: str, width: int = 160) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setFixedHeight(46)
    b.setFixedWidth(width)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {TEXT_LABEL};
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover   {{ color: {TEXT_BODY}; }}
        QPushButton:checked {{
            color: {ACCENT};
            border-bottom: 2px solid {ACCENT};
        }}
    """)
    return b


def _info_row(label: str, value: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lo = QHBoxLayout(w)
    lo.setContentsMargins(0, 8, 0, 8)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"font-size:13px; color:{TEXT_LABEL}; background:transparent;")
    val = QLabel(value)
    val.setStyleSheet(f"font-size:13px; font-weight:600; color:{TEXT_BODY}; background:transparent;")
    val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    lo.addWidget(lbl)
    lo.addStretch()
    lo.addWidget(val)
    return w


# ── Settings Page ─────────────────────────────────────────────────

class SettingsPage(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(f"background:{BG_PAGE};")
        self._build()
        self._load()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:{BG_PAGE}; border:none; }}"
            f"{Th.SCROLLBAR}"
        )

        inner = QWidget()
        inner.setStyleSheet(f"background:{BG_PAGE};")
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(20)

        # ── 3-column grid ─────────────────────────────────────
        grid = QHBoxLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Column 1 — General Settings (widest) ─────────────
        col1 = QVBoxLayout()
        col1.setSpacing(20)
        col1.setAlignment(Qt.AlignmentFlag.AlignTop)

        gen_card, gen_lo = _card()

        gen_lo.addWidget(_card_title("General Settings"))
        gen_lo.addWidget(_card_divider())

        self.biz_name   = _input(placeholder="e.g. Baraka Stores")
        self.biz_footer = _input(placeholder="e.g. Thank you for shopping with us")
        self.biz_curr   = _input(placeholder="KES")
        self.biz_curr.setMaximumWidth(120)

        gen_lo.addWidget(_field_group("Business Name",   self.biz_name))
        gen_lo.addSpacing(16)
        gen_lo.addWidget(_field_group(
            "Receipt Footer",
            self.biz_footer,
            "Printed at the bottom of every receipt"
        ))
        gen_lo.addSpacing(16)
        gen_lo.addWidget(_field_group(
            "Currency Symbol",
            self.biz_curr,
            "3-letter code · e.g. KES, USD, TZS"
        ))
        gen_lo.addSpacing(24)

        gen_save = _save_btn()
        gen_save.clicked.connect(self._save_business)
        gen_lo.addWidget(gen_save)
        col1.addWidget(gen_card)

        # Printer card
        prt_card, prt_lo = _card()
        prt_lo.addWidget(_card_title("Receipt Printer"))
        prt_lo.addWidget(_card_divider())

        self.printer_port = _input(
            placeholder="auto  ·  /dev/usb/lp0  ·  COM3"
        )
        prt_lo.addWidget(_field_group(
            "Printer Port",
            self.printer_port,
            "Leave 'auto' for USB plug-and-play detection"
        ))
        prt_lo.addSpacing(24)
        prt_save = _save_btn()
        prt_save.clicked.connect(self._save_printer)
        prt_lo.addWidget(prt_save)
        col1.addWidget(prt_card)
        col1.addStretch()

        grid.addLayout(col1, 3)

        # ── Column 2 — Security + About (narrower) ────────────
        col2 = QVBoxLayout()
        col2.setSpacing(20)
        col2.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Security card
        sec_card, sec_lo = _card()
        sec_lo.addWidget(_card_title("Security"))
        sec_lo.addWidget(_card_divider())

        self.timeout_spin = _spinbox()
        sec_lo.addWidget(_field_group(
            "Session Timeout",
            self.timeout_spin,
            "Auto-logout after inactivity"
        ))
        sec_lo.addSpacing(24)
        sec_save = _save_btn()
        sec_save.clicked.connect(self._save_session)
        sec_lo.addWidget(sec_save)
        col2.addWidget(sec_card)

        # About card
        abt_card, abt_lo = _card()
        abt_lo.addWidget(_card_title("About PosFlow"))
        abt_lo.addWidget(_card_divider())

        for label, value in [
            ("Version",   CONFIG.get("app_version", "1.0.0")),
            ("Database",  os.path.basename(get_db_path())),
            ("Platform",  "Offline · Local"),
        ]:
            abt_lo.addWidget(_info_row(label, value))

        col2.addWidget(abt_card)
        col2.addStretch()

        grid.addLayout(col2, 2)
        root.addLayout(grid)
        root.addStretch()

        scroll.setWidget(inner)
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.addWidget(scroll)

    def _load(self):
        try:
            from app.database import get_session
            from app.models.setting import Setting
            with get_session() as session:
                s = {x.key: x.value for x in session.query(Setting).all()}
            self.biz_name.setText(s.get("business_name", ""))
            self.biz_footer.setText(s.get("receipt_footer", ""))
            self.biz_curr.setText(s.get("currency", "KES"))
            self.timeout_spin.setValue(int(s.get("session_timeout_minutes", 30)))
            self.printer_port.setText(s.get("printer_port", "auto"))
        except Exception as e:
            logger.error("Settings load: %s", e)

    def _set(self, key, value):
        from app.database import get_session
        from app.models.setting import Setting
        with get_session() as session:
            s = session.get(Setting, key)
            if s:
                s.value = value
            else:
                session.add(Setting(key=key, value=value))

    def _save_business(self):
        try:
            self._set("business_name",  self.biz_name.text().strip())
            self._set("receipt_footer", self.biz_footer.text().strip())
            self._set("currency",       self.biz_curr.text().strip() or "KES")
            self._toast("Business settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _save_session(self):
        try:
            self._set("session_timeout_minutes", str(self.timeout_spin.value()))
            self._toast("Session settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _save_printer(self):
        try:
            self._set("printer_port", self.printer_port.text().strip() or "auto")
            self._toast("Printer settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _toast(self, msg, error=False):
        bg = "#DC2626" if error else "#059669"
        ic = "✕" if error else "✓"
        t  = QLabel(f"  {ic}  {msg}", self)
        t.setStyleSheet(f"""
            background:{bg}; color:white; border-radius:9px;
            padding:12px 20px; font-size:13px; font-weight:600;
        """)
        t.adjustSize(); t.setFixedHeight(44)
        t.move((self.width() - t.width()) // 2, self.height() - 70)
        t.show(); t.raise_()
        QTimer.singleShot(2600, t.deleteLater)


# ── Backup Page ───────────────────────────────────────────────────

class BackupPage(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(f"background:{BG_PAGE};")
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:{BG_PAGE}; border:none; }}"
            f"{Th.SCROLLBAR}"
        )

        inner = QWidget()
        inner.setStyleSheet(f"background:{BG_PAGE};")
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(20)

        grid = QHBoxLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Left — Export ─────────────────────────────────────
        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        exp_card, exp_lo = _card()
        exp_lo.addWidget(_card_title("Export Database Backup"))
        sub = QLabel("Creates a timestamped copy of posflow.db you can store on USB or cloud.")
        sub.setStyleSheet(f"font-size:12px; color:{TEXT_LABEL}; background:transparent; margin-top:4px;")
        sub.setWordWrap(True)
        exp_lo.addWidget(sub)
        exp_lo.addWidget(_card_divider())

        # DB info strip
        db_strip = QFrame()
        db_strip.setStyleSheet(f"""
            QFrame {{
                background: {BG_INPUT};
                border-radius: 8px;
                border: 1.5px solid {BORDER_IN};
            }}
        """)
        db_strip.setFixedHeight(52)
        ds = QHBoxLayout(db_strip)
        ds.setContentsMargins(16, 0, 16, 0)
        db_path = get_db_path()
        db_size = os.path.getsize(db_path) / 1024 if os.path.exists(db_path) else 0
        db_ic   = QLabel("🗄")
        db_ic.setStyleSheet("font-size:20px; background:transparent;")
        db_nm   = QLabel(f"posflow.db  ·  {db_size:.1f} KB")
        db_nm.setStyleSheet(f"font-size:12px; font-weight:600; color:{TEXT_BODY}; background:transparent;")
        db_pt   = QLabel(db_path)
        db_pt.setStyleSheet(f"font-size:10px; color:{TEXT_LABEL}; background:transparent;")
        db_pt.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ds.addWidget(db_ic); ds.addSpacing(8); ds.addWidget(db_nm); ds.addStretch(); ds.addWidget(db_pt)
        exp_lo.addWidget(db_strip)
        exp_lo.addSpacing(16)

        exp_lo.addWidget(_field_label("Destination Folder"))
        dest_row = QHBoxLayout()
        dest_row.setSpacing(10)
        self.dest_field = _input(readonly=True, placeholder="Choose a destination folder...")
        browse = QPushButton("Browse")
        browse.setFixedSize(100, 44)
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.setStyleSheet(f"""
            QPushButton {{
                background: {BG_INPUT}; color: {TEXT_BODY};
                border: 1.5px solid {BORDER_IN};
                border-radius: 8px; font-size:13px; font-weight:600;
            }}
            QPushButton:hover {{ background: #E2E8F0; border-color:#CBD5E1; }}
        """)
        browse.clicked.connect(self._browse)
        dest_row.addWidget(self.dest_field); dest_row.addWidget(browse)
        exp_lo.addLayout(dest_row)
        exp_lo.addSpacing(20)

        self.export_btn = _save_btn("Export Backup Now")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        exp_lo.addWidget(self.export_btn)
        left.addWidget(exp_card)
        grid.addLayout(left, 3)

        # ── Right — Tips ──────────────────────────────────────
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        tips_card, tips_lo = _card()
        tips_lo.addWidget(_card_title("Best Practices"))
        tips_lo.addWidget(_card_divider())

        for icon, tip in [
            ("⚡", "Back up at end of each business day."),
            ("💾", "Store backup on USB kept off-site."),
            ("🔁", "Restore: replace posflow.db and restart."),
            ("📅", "Keep at least 7 days of backups."),
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            ic = QLabel(icon)
            ic.setFixedWidth(22)
            ic.setStyleSheet("font-size:15px; background:transparent;")
            tx = QLabel(tip)
            tx.setWordWrap(True)
            tx.setStyleSheet(f"font-size:12px; color:{TEXT_LABEL}; line-height:1.5;")
            row.addWidget(ic); row.addWidget(tx, 1)
            tips_lo.addLayout(row)
            tips_lo.addSpacing(10)

        tips_lo.addWidget(_card_divider())
        self.last_bk = QLabel("Last backup: Never")
        self.last_bk.setStyleSheet(f"font-size:12px; color:{TEXT_LABEL};")
        self._refresh_bk()
        tips_lo.addWidget(self.last_bk)
        right.addWidget(tips_card)
        right.addStretch()

        grid.addLayout(right, 2)
        root.addLayout(grid)
        root.addStretch()
        scroll.setWidget(inner)

        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.addWidget(scroll)

    def _refresh_bk(self):
        try:
            from app.database import get_session
            from app.models.setting import Setting
            with get_session() as session:
                s   = session.get(Setting, "last_backup_at")
                val = s.value if s else ""
            if hasattr(self, 'last_bk'):
                self.last_bk.setText(
                    f"Last backup: {val}" if val else "Last backup: Never"
                )
        except Exception:
            pass

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
        if folder:
            self.dest_field.setText(folder)
            self.export_btn.setEnabled(True)

    def _export(self):
        dest = self.dest_field.text().strip()
        if not dest or not os.path.isdir(dest):
            self._toast("Select a valid folder first.", error=True)
            return
        try:
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"posflow_backup_{ts}.db"
            shutil.copy2(get_db_path(), os.path.join(dest, filename))
            from app.database import get_session
            from app.models.setting import Setting
            ts_str = datetime.now().strftime("%d %b %Y  %H:%M")
            with get_session() as session:
                s = session.get(Setting, "last_backup_at")
                if s:
                    s.value = ts_str
                else:
                    session.add(Setting(key="last_backup_at", value=ts_str))
            self._refresh_bk()
            self._toast(f"Saved: {filename}")
        except Exception as e:
            self._toast(f"Backup failed: {e}", error=True)

    def _toast(self, msg, error=False):
        bg = "#DC2626" if error else "#059669"
        ic = "✕" if error else "✓"
        t  = QLabel(f"  {ic}  {msg}", self)
        t.setStyleSheet(f"""
            background:{bg}; color:white; border-radius:9px;
            padding:12px 20px; font-size:13px; font-weight:600;
        """)
        t.adjustSize(); t.setFixedHeight(44)
        t.move((self.width() - t.width()) // 2, self.height() - 70)
        t.show(); t.raise_()
        QTimer.singleShot(2600, t.deleteLater)


# ── Shell ─────────────────────────────────────────────────────────

class SettingsView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(f"background:{BG_PAGE};")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Tab bar
        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {BORDER_IN};
            }}
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(28, 0, 28, 0)
        bl.setSpacing(0)

        self.t_set = _tab_btn("Settings",         148)
        self.t_bak = _tab_btn("Backup & Restore",  180)
        self.t_set.setChecked(True)
        self.t_set.clicked.connect(lambda: self._sw(0))
        self.t_bak.clicked.connect(lambda: self._sw(1))
        bl.addWidget(self.t_set)
        bl.addWidget(self.t_bak)
        bl.addStretch()
        root.addWidget(bar)

        self.stack = QStackedWidget()
        self.stack.addWidget(SettingsPage(self.user))
        self.stack.addWidget(BackupPage(self.user))
        root.addWidget(self.stack)

    def _sw(self, i):
        self.t_set.setChecked(i == 0)
        self.t_bak.setChecked(i == 1)
        self.stack.setCurrentIndex(i)
