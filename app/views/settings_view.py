"""
app/views/settings_view.py
---------------------------
Settings — two-column layout matching modern SaaS style.
"""
import logging, shutil, os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QStackedWidget, QFileDialog,
    QScrollArea, QSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from app.config import CONFIG
from app.database import get_db_path
from app.utils.theme import Th

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────

def field(value="", placeholder="", h=46, readonly=False) -> QLineEdit:
    f = QLineEdit(value)
    f.setPlaceholderText(placeholder)
    f.setFixedHeight(h)
    f.setReadOnly(readonly)
    f.setStyleSheet(f"""
        QLineEdit {{
            background: {'#F8FAFC' if readonly else 'white'};
            border: 1.5px solid #E2E8F0;
            border-radius: 10px;
            padding: 0 16px;
            font-size: 13px;
            color: {Th.INK_900};
        }}
        QLineEdit:focus {{
            border-color: {Th.PRIMARY};
            background: white;
        }}
    """)
    return f


def section_title(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(
        f"font-size:16px; font-weight:700; color:{Th.INK_900};"
    )
    return l


def field_label(text: str, hint: str = "") -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lo = QVBoxLayout(w)
    lo.setContentsMargins(0, 0, 0, 4)
    lo.setSpacing(2)
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size:13px; font-weight:500; color:{Th.INK_700};"
    )
    lo.addWidget(lbl)
    if hint:
        h = QLabel(hint)
        h.setStyleSheet(f"font-size:11px; color:{Th.INK_300};")
        lo.addWidget(h)
    return w


def save_btn(text="Save Changes", w=None) -> QPushButton:
    b = QPushButton(text)
    b.setFixedHeight(46)
    if w:
        b.setFixedWidth(w)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {Th.PRIMARY};
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 700;
        }}
        QPushButton:hover {{ background: {Th.PRIMARY_HOVER}; }}
    """)
    return b


def card(parent=None) -> tuple:
    """Returns (QFrame card, QVBoxLayout inner)"""
    c = QFrame(parent)
    c.setStyleSheet("""
        QFrame {
            background: white;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
        }
    """)
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    sh = Th.shadow(12, 1, 8)
    c.setGraphicsEffect(sh)
    lo = QVBoxLayout(c)
    lo.setContentsMargins(28, 24, 28, 24)
    lo.setSpacing(16)
    return c, lo


def divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{Th.DIVIDER}; border:none;")
    return f


def tab_btn(text, w=160) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setFixedHeight(48)
    b.setFixedWidth(w)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:transparent; color:{Th.INK_300};
            border:none; border-bottom:2px solid transparent;
            font-size:13px; font-weight:600;
        }}
        QPushButton:hover   {{ color:{Th.INK_700}; }}
        QPushButton:checked {{
            color:{Th.PRIMARY};
            border-bottom:2px solid {Th.PRIMARY};
        }}
    """)
    return b


# ── Settings page ─────────────────────────────────────────────────

class SettingsPage(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(f"background:{Th.INK_50};")
        self._build()
        self._load()

    def _build(self):
        # Outer scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:{Th.INK_50}; border:none; }}"
            f"{Th.SCROLLBAR}"
        )

        inner = QWidget()
        inner.setStyleSheet(f"background:{Th.INK_50};")
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(20)

        # Two-column layout
        cols = QHBoxLayout()
        cols.setSpacing(20)
        cols.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── LEFT column ───────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(20)
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        # General Settings card
        gen_card, gen_lo = card()
        gen_lo.addWidget(section_title("General Settings"))
        gen_lo.addWidget(divider())

        self.biz_name   = field(placeholder="e.g. My Shop")
        self.biz_footer = field(placeholder="e.g. Thank you for your business!")
        self.biz_curr   = field(placeholder="KES")
        self.biz_curr.setMaximumWidth(140)

        for lbl, hint, widget in [
            ("Business Name",   "", self.biz_name),
            ("Receipt Footer",  "Printed at bottom of every receipt", self.biz_footer),
            ("Currency Symbol", "3-letter code, e.g. KES, USD", self.biz_curr),
        ]:
            gen_lo.addWidget(field_label(lbl, hint))
            gen_lo.addWidget(widget)

        biz_save = save_btn("Save Changes")
        biz_save.clicked.connect(self._save_business)
        gen_lo.addSpacing(4)
        gen_lo.addWidget(biz_save)
        left.addWidget(gen_card)

        # Printer card
        prt_card, prt_lo = card()
        prt_lo.addWidget(section_title("Receipt Printer"))
        prt_lo.addWidget(divider())

        self.printer_port = field(placeholder="auto, /dev/usb/lp0, or COM3")
        prt_lo.addWidget(field_label(
            "Printer Port",
            "Leave 'auto' for USB plug-and-play"
        ))
        prt_lo.addWidget(self.printer_port)

        prt_save = save_btn("Save Changes")
        prt_save.clicked.connect(self._save_printer)
        prt_lo.addSpacing(4)
        prt_lo.addWidget(prt_save)
        left.addWidget(prt_card)

        cols.addLayout(left, 3)

        # ── RIGHT column ──────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(20)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Security card
        sec_card, sec_lo = card()
        sec_lo.addWidget(section_title("Security"))
        sec_lo.addWidget(divider())

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 480)
        self.timeout_spin.setSuffix("  min")
        self.timeout_spin.setFixedHeight(46)
        self.timeout_spin.setMaximumWidth(160)
        self.timeout_spin.setStyleSheet(f"""
            QSpinBox {{
                background: white;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 0 14px;
                font-size: 13px;
                color: {Th.INK_900};
            }}
            QSpinBox:focus {{ border-color: {Th.PRIMARY}; }}
            QSpinBox::up-button, QSpinBox::down-button {{ width: 0; }}
        """)

        sec_lo.addWidget(field_label(
            "Session Timeout",
            "Auto-logout after inactivity"
        ))
        sec_lo.addWidget(self.timeout_spin)

        sec_save = save_btn("Save Changes")
        sec_save.clicked.connect(self._save_session)
        sec_lo.addSpacing(4)
        sec_lo.addWidget(sec_save)
        right.addWidget(sec_card)

        # App info card
        info_card, info_lo = card()
        info_lo.addWidget(section_title("About PosFlow"))
        info_lo.addWidget(divider())

        for label, value in [
            ("Version",   CONFIG.get("app_version", "1.0.0")),
            ("Database",  os.path.basename(get_db_path())),
            ("Platform",  "Offline — Local Desktop"),
        ]:
            row = QHBoxLayout()
            l   = QLabel(label)
            l.setStyleSheet(f"font-size:13px; color:{Th.INK_500};")
            v   = QLabel(value)
            v.setStyleSheet(
                f"font-size:13px; font-weight:600; color:{Th.INK_900};"
            )
            v.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(l); row.addStretch(); row.addWidget(v)
            info_lo.addLayout(row)

        right.addWidget(info_card)

        cols.addLayout(right, 2)
        root.addLayout(cols)
        root.addStretch()

        scroll.setWidget(inner)
        page_lo = QVBoxLayout(self)
        page_lo.setContentsMargins(0, 0, 0, 0)
        page_lo.addWidget(scroll)

    def _load(self):
        try:
            from app.database import get_session
            from app.models.setting import Setting
            with get_session() as session:
                s = {x.key: x.value for x in session.query(Setting).all()}
            self.biz_name.setText(s.get("business_name", ""))
            self.biz_footer.setText(s.get("receipt_footer", ""))
            self.biz_curr.setText(s.get("currency", "KES"))
            self.timeout_spin.setValue(
                int(s.get("session_timeout_minutes", 30))
            )
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
            self._set("currency", self.biz_curr.text().strip() or "KES")
            self._toast("Business settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _save_session(self):
        try:
            self._set("session_timeout_minutes",
                       str(self.timeout_spin.value()))
            self._toast("Session settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _save_printer(self):
        try:
            self._set("printer_port",
                       self.printer_port.text().strip() or "auto")
            self._toast("Printer settings saved.")
        except Exception as e:
            self._toast(f"Error: {e}", error=True)

    def _toast(self, msg, error=False):
        bg = Th.DANGER if error else Th.SUCCESS
        t  = QLabel(f"  {'✕' if error else '✓'}  {msg}", self)
        t.setStyleSheet(f"""
            background:{bg}; color:white; border-radius:9px;
            padding:12px 20px; font-size:13px; font-weight:600;
        """)
        t.adjustSize(); t.setFixedHeight(44)
        t.move((self.width() - t.width()) // 2, self.height() - 70)
        t.show(); t.raise_()
        QTimer.singleShot(2600, t.deleteLater)


# ── Backup page ───────────────────────────────────────────────────

class BackupPage(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(f"background:{Th.INK_50};")
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:{Th.INK_50}; border:none; }}"
            f"{Th.SCROLLBAR}"
        )

        inner = QWidget()
        inner.setStyleSheet(f"background:{Th.INK_50};")
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(20)

        cols = QHBoxLayout()
        cols.setSpacing(20)
        cols.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Left — Export card ────────────────────────────────
        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        exp_card, exp_lo = card()
        exp_lo.addWidget(section_title("Export Backup"))
        exp_lo.addWidget(QLabel(
            "Creates a timestamped copy of posflow.db.\nSave to USB or external drive."
        ).setStyleSheet if False else self._styled_hint(
            "Creates a timestamped copy of posflow.db.\n"
            "Save to USB or external drive."
        ))
        exp_lo.addWidget(divider())

        # DB info
        db_path = get_db_path()
        db_size = (
            os.path.getsize(db_path) / 1024
            if os.path.exists(db_path) else 0
        )
        db_row = QHBoxLayout()
        db_icon = QLabel("🗄")
        db_icon.setStyleSheet("font-size:22px; background:transparent;")
        db_info = QVBoxLayout()
        db_info.setSpacing(2)
        dbt = QLabel("posflow.db")
        dbt.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{Th.INK_900};"
        )
        dbs = QLabel(f"{db_path}  ·  {db_size:.1f} KB")
        dbs.setStyleSheet(f"font-size:11px; color:{Th.INK_300};")
        db_info.addWidget(dbt); db_info.addWidget(dbs)
        db_row.addWidget(db_icon)
        db_row.addSpacing(10)
        db_row.addLayout(db_info, 1)
        exp_lo.addLayout(db_row)

        exp_lo.addWidget(field_label("Destination Folder"))
        dest_row = QHBoxLayout()
        dest_row.setSpacing(10)
        self.dest_field = field(readonly=True,
                                placeholder="Choose a folder...")
        browse = QPushButton("Browse")
        browse.setFixedSize(100, 46)
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.setStyleSheet(f"""
            QPushButton {{
                background:{Th.INK_100}; color:{Th.INK_700};
                border:none; border-radius:10px;
                font-size:13px; font-weight:600;
            }}
            QPushButton:hover {{ background:#E2E8F0; }}
        """)
        browse.clicked.connect(self._browse)
        dest_row.addWidget(self.dest_field)
        dest_row.addWidget(browse)
        exp_lo.addLayout(dest_row)

        self.export_btn = save_btn("Export Backup Now")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        exp_lo.addSpacing(4)
        exp_lo.addWidget(self.export_btn)
        left.addWidget(exp_card)
        cols.addLayout(left, 3)

        # ── Right — Tips card ─────────────────────────────────
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        tips_card, tips_lo = card()
        tips_lo.addWidget(section_title("Best Practices"))
        tips_lo.addWidget(divider())

        for icon, tip in [
            ("⚡", "Back up daily — at end of each business day."),
            ("💾", "Store on a USB drive kept off-site."),
            ("🔁", "To restore: replace posflow.db with your backup file and restart."),
            ("📅", "Keep at least the last 7 days of backups."),
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            ic = QLabel(icon)
            ic.setFixedWidth(22)
            ic.setStyleSheet("font-size:16px; background:transparent;")
            tx = QLabel(tip)
            tx.setWordWrap(True)
            tx.setStyleSheet(
                f"font-size:12px; color:{Th.INK_500};"
                " line-height: 1.5;"
            )
            row.addWidget(ic)
            row.addWidget(tx, 1)
            tips_lo.addLayout(row)

        self.last_bk = QLabel("")
        self.last_bk.setStyleSheet(
            f"font-size:12px; color:{Th.INK_300}; padding-top:8px;"
        )
        self._refresh_bk()
        tips_lo.addWidget(divider())
        tips_lo.addWidget(self.last_bk)
        right.addWidget(tips_card)
        cols.addLayout(right, 2)

        root.addLayout(cols)
        root.addStretch()
        scroll.setWidget(inner)

        page_lo = QVBoxLayout(self)
        page_lo.setContentsMargins(0, 0, 0, 0)
        page_lo.addWidget(scroll)

    def _styled_hint(self, text) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"font-size:12px; color:{Th.INK_300};")
        l.setWordWrap(True)
        return l

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
        folder = QFileDialog.getExistingDirectory(
            self, "Select Backup Destination"
        )
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
                    session.add(
                        Setting(key="last_backup_at", value=ts_str)
                    )
            self._refresh_bk()
            self._toast(f"Backup saved: {filename}")
        except Exception as e:
            self._toast(f"Backup failed: {e}", error=True)

    def _toast(self, msg, error=False):
        bg = Th.DANGER if error else Th.SUCCESS
        t  = QLabel(f"  {'✕' if error else '✓'}  {msg}", self)
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
        self.setStyleSheet(f"background:{Th.INK_50};")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet("background:white; border-bottom:1px solid #F1F5F9;")
        bl  = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0); bl.setSpacing(0)

        self.t_set = tab_btn("Settings")
        self.t_bak = tab_btn("Backup & Restore", 180)
        self.t_set.setChecked(True)
        self.t_set.clicked.connect(lambda: self._sw(0))
        self.t_bak.clicked.connect(lambda: self._sw(1))
        bl.addWidget(self.t_set); bl.addWidget(self.t_bak); bl.addStretch()
        root.addWidget(bar)

        self.stack = QStackedWidget()
        self.stack.addWidget(SettingsPage(self.user))
        self.stack.addWidget(BackupPage(self.user))
        root.addWidget(self.stack)

    def _sw(self, i):
        self.t_set.setChecked(i == 0)
        self.t_bak.setChecked(i == 1)
        self.stack.setCurrentIndex(i)


from PyQt6.QtWidgets import QStackedWidget
