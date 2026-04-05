"""
app/views/users_view.py
------------------------
User management — Admin only.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QDialog, QComboBox,
    QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from app.config import CONFIG

logger = logging.getLogger(__name__)

ROLES = ["cashier", "manager", "admin"]

ROLE_META = {
    "admin":   ("Admin",   "#7C3AED", "#F5F3FF"),
    "manager": ("Manager", "#059669", "#ECFDF5"),
    "cashier": ("Cashier", "#1A3C6B", "#EFF6FF"),
}


def card_shadow():
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(12)
    s.setOffset(0, 1)
    s.setColor(QColor(0, 0, 0, 12))
    return s


def pill(text, fg, bg):
    l = QLabel(text)
    l.setStyleSheet(f"""
        color:{fg}; background:{bg};
        border-radius:5px; padding:3px 10px;
        font-size:11px; font-weight:bold;
    """)
    l.setFixedHeight(22)
    return l


def solid_btn(text, bg="#1A3C6B", fg="white", hover="#2E75B6", h=44, w=None, fs=13):
    b = QPushButton(text)
    b.setFixedHeight(h)
    if w:
        b.setFixedWidth(w)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:none; border-radius:9px;
            font-size:{fs}px; font-weight:bold;
        }}
        QPushButton:hover {{ background:{hover}; }}
        QPushButton:disabled {{ background:#E5E7EB; color:#9CA3AF; }}
    """)
    return b


def field(placeholder="", password=False):
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setFixedHeight(44)
    if password:
        f.setEchoMode(QLineEdit.EchoMode.Password)
    f.setStyleSheet("""
        QLineEdit {
            border:1.5px solid #E5E7EB; border-radius:9px;
            padding:0 14px; font-size:13px;
            background:#FAFAFA; color:#111827;
        }
        QLineEdit:focus { border-color:#1A3C6B; background:white; }
    """)
    return f


def combo(items):
    c = QComboBox()
    c.addItems(items)
    c.setFixedHeight(44)
    c.setStyleSheet("""
        QComboBox {
            border:1.5px solid #E5E7EB; border-radius:9px;
            padding:0 14px; font-size:13px;
            background:#FAFAFA; color:#111827;
        }
        QComboBox:focus { border-color:#1A3C6B; background:white; }
        QComboBox::drop-down { border:none; width:28px; }
        QComboBox QAbstractItemView {
            border:1px solid #E5E7EB;
            selection-background-color:#EFF6FF;
            selection-color:#1A3C6B; font-size:13px;
        }
    """)
    return c


# ── User Row ──────────────────────────────────────────────────────

class UserRow(QFrame):
    def __init__(self, user: dict, on_edit, on_toggle, current_user_id, parent=None):
        super().__init__(parent)
        self.user_data       = user
        self.on_edit         = on_edit
        self.on_toggle       = on_toggle
        self.current_user_id = current_user_id
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border-bottom:1px solid #F3F4F6;
            }
            QFrame:hover { background:#FAFAFA; }
        """)
        self._build()

    def _build(self):
        u = self.user_data
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Avatar
        av = QLabel(u["full_name"][0].upper())
        av.setFixedSize(38, 38)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_fg, role_bg = ROLE_META.get(u["role"], ("", "#EFF6FF", "#1A3C6B"))[1:3]
        av.setStyleSheet(f"""
            background:{role_bg};
            color:{role_fg};
            border-radius:19px;
            font-size:15px; font-weight:bold;
        """)

        # Info
        info = QVBoxLayout()
        info.setSpacing(3)
        name = QLabel(u["full_name"])
        name.setStyleSheet(f"""
            font-size:13px; font-weight:bold;
            color:{'#111827' if u['is_active'] else '#9CA3AF'};
            background:transparent;
        """)
        uname = QLabel(f"@{u['username']}")
        uname.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        info.addWidget(name)
        info.addWidget(uname)

        # Role badge
        role_lbl, role_fg, role_bg = ROLE_META.get(u["role"], ("Unknown", "#374151", "#F3F4F6"))
        role_badge = pill(role_lbl, role_fg, role_bg)
        role_badge.setFixedWidth(76)

        # Status badge
        if u["is_active"]:
            status = pill("Active", "#059669", "#ECFDF5")
        else:
            status = pill("Inactive", "#9CA3AF", "#F3F4F6")
        status.setFixedWidth(72)

        # Last login
        ll = QLabel(u.get("last_login") or "Never")
        ll.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        ll.setFixedWidth(150)

        # Buttons
        is_self = u["id"] == self.current_user_id
        edit_btn = solid_btn("Edit", "#EFF6FF", "#1A3C6B", "#DBEAFE", h=32, w=68, fs=12)
        edit_btn.clicked.connect(lambda: self.on_edit(self.user_data))

        if not is_self:
            if u["is_active"]:
                tog = solid_btn("Deactivate", "#FEF2F2", "#DC2626", "#FEE2E2", h=32, w=96, fs=12)
            else:
                tog = solid_btn("Activate", "#ECFDF5", "#059669", "#D1FAE5", h=32, w=96, fs=12)
            tog.clicked.connect(lambda: self.on_toggle(self.user_data))
        else:
            tog = QLabel("(You)")
            tog.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
            tog.setFixedWidth(96)

        layout.addWidget(av)
        layout.addLayout(info, 1)
        layout.addWidget(role_badge)
        layout.addWidget(status)
        layout.addWidget(ll)
        layout.addWidget(edit_btn)
        layout.addWidget(tog)


# ── Add / Edit Dialog ─────────────────────────────────────────────

class UserDialog(QDialog):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit   = user_data is not None
        self.setWindowTitle("Edit User" if self.is_edit else "New User")
        self.setFixedWidth(440)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()
        if self.is_edit:
            self._populate()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background:white; border-radius:16px;
                border:1px solid #E5E7EB;
            }
        """)
        card.setGraphicsEffect(card_shadow())
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Edit User" if self.is_edit else "Add New User")
        title.setStyleSheet("font-size:17px; font-weight:bold; color:#111827;")
        close = QPushButton("✕")
        close.setFixedSize(28, 28)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet("""
            QPushButton {
                background:#F3F4F6; color:#6B7280;
                border:none; border-radius:7px; font-size:12px;
            }
            QPushButton:hover { background:#E5E7EB; }
        """)
        close.clicked.connect(self.reject)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close)
        layout.addLayout(hdr)

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
            return l

        self.fullname_input = field("Full name")
        self.username_input = field("Username  (no spaces)")
        self.role_combo     = combo([r.title() for r in ROLES])
        self.password_input = field(
            "Leave blank to keep current" if self.is_edit else "Password",
            password=True
        )

        layout.addWidget(lbl("Full Name"))
        layout.addWidget(self.fullname_input)
        layout.addWidget(lbl("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(lbl("Role"))
        layout.addWidget(self.role_combo)
        layout.addWidget(lbl("Password"))
        layout.addWidget(self.password_input)

        # Error
        self.err = QLabel("")
        self.err.setStyleSheet("""
            color:#DC2626; background:#FEF2F2;
            border:1px solid #FECACA; border-radius:8px;
            padding:8px 12px; font-size:12px;
        """)
        self.err.setWordWrap(True)
        self.err.hide()
        layout.addWidget(self.err)

        layout.addSpacing(4)
        save = solid_btn("Save User", h=48, fs=14)
        save.clicked.connect(self._save)
        layout.addWidget(save)

    def _populate(self):
        u = self.user_data
        self.fullname_input.setText(u["full_name"])
        self.username_input.setText(u["username"])
        idx = ROLES.index(u["role"]) if u["role"] in ROLES else 0
        self.role_combo.setCurrentIndex(idx)

    def _save(self):
        full = self.fullname_input.text().strip()
        uname = self.username_input.text().strip().lower().replace(" ", "")
        role  = ROLES[self.role_combo.currentIndex()]
        pwd   = self.password_input.text()

        if not full or not uname:
            self.err.setText("Full name and username are required.")
            self.err.show()
            return
        if not self.is_edit and not pwd:
            self.err.setText("Password is required for new users.")
            self.err.show()
            return

        self.result_data = {
            "full_name": full,
            "username":  uname,
            "role":      role,
            "password":  pwd or None,
        }
        self.accept()


# ── Main Users View ───────────────────────────────────────────────

class UsersView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.current_user = user
        self.all_users    = []
        self.setStyleSheet("background:#F8FAFC;")
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search users...")
        self.search.setFixedHeight(40)
        self.search.setMaximumWidth(260)
        self.search.setStyleSheet("""
            QLineEdit {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 14px; font-size:13px;
                background:white; color:#111827;
            }
            QLineEdit:focus { border-color:#1A3C6B; }
        """)
        self.search.textChanged.connect(self._filter)

        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Roles", "Admin", "Manager", "Cashier"])
        self.role_filter.setFixedHeight(40)
        self.role_filter.setFixedWidth(130)
        self.role_filter.setStyleSheet("""
            QComboBox {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 12px; font-size:13px;
                background:white; color:#111827;
            }
            QComboBox:focus { border-color:#1A3C6B; }
            QComboBox::drop-down { border:none; width:26px; }
            QComboBox QAbstractItemView {
                border:1px solid #E5E7EB;
                selection-background-color:#EFF6FF;
                selection-color:#1A3C6B;
            }
        """)
        self.role_filter.currentTextChanged.connect(self._filter)

        bar.addWidget(self.search)
        bar.addWidget(self.role_filter)
        bar.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-size:12px; color:#9CA3AF;")
        bar.addWidget(self.count_lbl)

        add_btn = solid_btn("+ Add User", h=40, w=120, fs=13)
        add_btn.clicked.connect(self._open_add)
        bar.addWidget(add_btn)
        root.addLayout(bar)

        # List card
        list_card = QFrame()
        list_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        list_card.setGraphicsEffect(card_shadow())
        lc_layout = QVBoxLayout(list_card)
        lc_layout.setContentsMargins(0, 0, 0, 0)
        lc_layout.setSpacing(0)

        # Column header
        col_hdr = QFrame()
        col_hdr.setFixedHeight(38)
        col_hdr.setStyleSheet("""
            background:#FAFAFA;
            border-radius:12px 12px 0 0;
            border-bottom:1px solid #F3F4F6;
        """)
        chl = QHBoxLayout(col_hdr)
        chl.setContentsMargins(20, 0, 20, 0)
        chl.setSpacing(16)
        for txt, w in [("", 38), ("User", 0), ("Role", 76),
                       ("Status", 72), ("Last Login", 150), ("", 172)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size:11px; font-weight:bold; color:#9CA3AF; "
                              "background:transparent; letter-spacing:0.5px;")
            if w == 0:
                chl.addWidget(lbl, 1)
            else:
                lbl.setFixedWidth(w)
                chl.addWidget(lbl)
        lc_layout.addWidget(col_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollBar:vertical { width:4px; background:transparent; }
            QScrollBar::handle:vertical { background:#E5E7EB; border-radius:2px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height:0; }
        """)
        self.rows_widget = QWidget()
        self.rows_widget.setStyleSheet("background:transparent;")
        self.rows_vbox   = QVBoxLayout(self.rows_widget)
        self.rows_vbox.setContentsMargins(0, 0, 0, 0)
        self.rows_vbox.setSpacing(0)
        self.rows_vbox.addStretch()
        scroll.setWidget(self.rows_widget)
        lc_layout.addWidget(scroll)
        root.addWidget(list_card)

    def _load(self):
        try:
            from app.database import get_session
            from app.models.user import User as UserModel
            with get_session() as session:
                users = session.query(UserModel).order_by(UserModel.full_name).all()
                self.all_users = [
                    {
                        "id":         u.id,
                        "full_name":  u.full_name,
                        "username":   u.username,
                        "role":       u.role,
                        "is_active":  u.is_active,
                        "last_login": u.last_login.strftime("%d %b %Y %H:%M")
                                      if u.last_login else None,
                    }
                    for u in users
                ]
            self._filter()
        except Exception as e:
            logger.error("Users load error: %s", e)

    def _filter(self):
        q    = self.search.text().strip().lower()
        role = self.role_filter.currentText().lower()
        out  = []
        for u in self.all_users:
            if q and q not in u["full_name"].lower() and q not in u["username"].lower():
                continue
            if role != "all roles" and u["role"] != role:
                continue
            out.append(u)
        self._render(out)

    def _render(self, users):
        while self.rows_vbox.count():
            it = self.rows_vbox.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        if not users:
            empty = QLabel("No users found.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("font-size:14px; color:#D1D5DB; background:transparent;")
            self.rows_vbox.addStretch()
            self.rows_vbox.addWidget(empty)
            self.rows_vbox.addStretch()
            self.count_lbl.setText("")
            return

        for u in users:
            row = UserRow(u, self._open_edit, self._toggle_user, self.current_user.id)
            self.rows_vbox.addWidget(row)
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background:#F3F4F6;")
            self.rows_vbox.addWidget(div)
        self.rows_vbox.addStretch()
        self.count_lbl.setText(f"{len(users)} users")

    def _open_add(self):
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._create_user(dlg.result_data)

    def _open_edit(self, user_data):
        dlg = UserDialog(user_data=user_data, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_user(user_data["id"], dlg.result_data)

    def _create_user(self, data):
        try:
            from app.database import get_session
            from app.models.user import User as UserModel
            from app.services.auth_service import AuthService
            with get_session() as session:
                existing = session.query(UserModel).filter_by(
                    username=data["username"]
                ).first()
                if existing:
                    self._toast("Username already exists.", error=True)
                    return
                session.add(UserModel(
                    full_name=data["full_name"],
                    username=data["username"],
                    role=data["role"],
                    password_hash=AuthService.hash_password(data["password"]),
                    is_active=True,
                ))
            self._toast(f"User '{data['full_name']}' created.")
            self._load()
        except Exception as e:
            logger.error("Create user error: %s", e)
            self._toast(f"Error: {e}", error=True)

    def _update_user(self, user_id, data):
        try:
            from app.database import get_session
            from app.models.user import User as UserModel
            from app.services.auth_service import AuthService
            with get_session() as session:
                u = session.get(UserModel, user_id)
                if u:
                    u.full_name = data["full_name"]
                    u.username  = data["username"]
                    u.role      = data["role"]
                    if data["password"]:
                        u.password_hash = AuthService.hash_password(data["password"])
            self._toast(f"User '{data['full_name']}' updated.")
            self._load()
        except Exception as e:
            logger.error("Update user error: %s", e)
            self._toast(f"Error: {e}", error=True)

    def _toggle_user(self, user_data):
        action = "deactivate" if user_data["is_active"] else "activate"
        try:
            from app.database import get_session
            from app.models.user import User as UserModel
            with get_session() as session:
                u = session.get(UserModel, user_data["id"])
                if u:
                    u.is_active = not u.is_active
            self._toast(f"User '{user_data['full_name']}' {action}d.")
            self._load()
        except Exception as e:
            logger.error("Toggle user error: %s", e)

    def _toast(self, msg, error=False):
        bg    = "#DC2626" if error else "#1A3C6B"
        icon  = "✕" if error else "✓"
        toast = QLabel(f"  {icon}  {msg}", self)
        toast.setStyleSheet(f"""
            background:{bg}; color:white;
            border-radius:10px; padding:12px 20px;
            font-size:13px; font-weight:bold;
        """)
        toast.adjustSize()
        toast.setFixedHeight(44)
        toast.move((self.width() - toast.width()) // 2, self.height() - 80)
        toast.show()
        toast.raise_()
        QTimer.singleShot(2600, toast.deleteLater)
