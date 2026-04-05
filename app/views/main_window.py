"""
app/views/main_window.py
-------------------------
Main application shell — clean sidebar + content area.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont
from app.config import CONFIG
from app.utils.theme import Th

logger = logging.getLogger(__name__)

# SVG-style unicode icon map (thin, modern)
NAV = [
    ("Point of Sale", "pos",      ["admin", "manager", "cashier"]),
    ("Products",      "products", ["admin"]),
    ("Stock",         "stock",    ["admin", "manager"]),
    ("Returns",       "returns",  ["admin", "manager"]),
    ("Reports",       "reports",  ["admin", "manager"]),
    ("Users",         "users",    ["admin"]),
    ("Settings",      "settings", ["admin"]),
]

ICONS = {
    "pos":      "⊞",
    "products": "◫",
    "stock":    "≡",
    "returns":  "↺",
    "reports":  "⊟",
    "users":    "◯",
    "settings": "◎",
}


class NavItem(QFrame):
    def __init__(self, icon, label, key, on_click, parent=None):
        super().__init__(parent)
        self.key      = key
        self.on_click = on_click
        self.active   = False
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(icon, label)
        self._style()

    def _build(self, icon, label):
        lo = QHBoxLayout(self)
        lo.setContentsMargins(16, 0, 16, 0)
        lo.setSpacing(12)

        self.indicator = QFrame()
        self.indicator.setFixedSize(3, 22)
        self.indicator.setStyleSheet("background: transparent; border-radius: 2px;")

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFixedWidth(18)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.text_lbl = QLabel(label)
        self.text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        lo.addWidget(self.indicator)
        lo.addWidget(self.icon_lbl)
        lo.addWidget(self.text_lbl)
        lo.addStretch()

    def _style(self):
        if self.active:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.10);
                    border-radius: 8px;
                }
            """)
            self.indicator.setStyleSheet(
                "background: #60A5FA; border-radius: 2px;"
            )
            self.icon_lbl.setStyleSheet(
                "color: white; font-size: 16px; background: transparent;"
            )
            self.text_lbl.setStyleSheet(
                "color: white; font-size: 13px; font-weight: 600; background: transparent;"
            )
        else:
            self.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background: rgba(255,255,255,0.06);
                }
            """)
            self.indicator.setStyleSheet(
                "background: transparent; border-radius: 2px;"
            )
            self.icon_lbl.setStyleSheet(
                "color: rgba(255,255,255,0.45); font-size: 16px; background: transparent;"
            )
            self.text_lbl.setStyleSheet(
                "color: rgba(255,255,255,0.55); font-size: 13px; font-weight: 500;"
                " background: transparent;"
            )

    def set_active(self, active: bool):
        self.active = active
        self._style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click(self.key)


class Sidebar(QFrame):
    def __init__(self, user, on_navigate, on_logout, parent=None):
        super().__init__(parent)
        self.user        = user
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.nav_items   = {}
        self.setFixedWidth(224)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1B3F6E,
                    stop:1 #152E52
                );
                border: none;
            }
        """)
        self._build()

    def _build(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(12, 0, 12, 16)
        lo.setSpacing(2)

        # ── Logo ─────────────────────────────────────────────
        logo_wrap = QWidget()
        logo_wrap.setFixedHeight(64)
        logo_wrap.setStyleSheet("background: transparent;")
        ll = QVBoxLayout(logo_wrap)
        ll.setContentsMargins(16, 0, 16, 0)
        ll.setSpacing(1)
        ll.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        brand = QLabel("POSFLOW")
        brand.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)
        biz = QLabel(CONFIG.get("business_name", "My Business"))
        biz.setStyleSheet("""
            color: rgba(255,255,255,0.40);
            font-size: 11px;
            font-weight: 400;
            background: transparent;
        """)
        ll.addWidget(brand)
        ll.addWidget(biz)
        lo.addWidget(logo_wrap)

        # Top thin rule
        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet("background: rgba(255,255,255,0.08);")
        lo.addWidget(rule)
        lo.addSpacing(8)

        # ── Nav items ─────────────────────────────────────────
        for label, key, roles in NAV:
            if self.user.role not in roles:
                continue
            item = NavItem(ICONS.get(key, "·"), label, key, self.on_navigate)
            self.nav_items[key] = item
            lo.addWidget(item)

        lo.addStretch()

        # Bottom rule
        rule2 = QFrame()
        rule2.setFixedHeight(1)
        rule2.setStyleSheet("background: rgba(255,255,255,0.08);")
        lo.addWidget(rule2)
        lo.addSpacing(12)

        # ── User badge ────────────────────────────────────────
        user_row = QWidget()
        user_row.setStyleSheet("background: transparent;")
        ur = QHBoxLayout(user_row)
        ur.setContentsMargins(4, 0, 4, 0)
        ur.setSpacing(10)

        initials = self.user.full_name[0].upper()
        av = QLabel(initials)
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet("""
            background: rgba(255,255,255,0.15);
            color: white;
            border-radius: 17px;
            font-size: 14px;
            font-weight: 700;
        """)

        info = QVBoxLayout()
        info.setSpacing(1)
        nm = QLabel(self.user.full_name)
        nm.setStyleSheet("color: white; font-size: 12px; font-weight: 600; background: transparent;")
        nm.setMaximumWidth(120)
        rl = QLabel(self.user.role.title())
        rl.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 11px; background: transparent;")
        info.addWidget(nm); info.addWidget(rl)

        ur.addWidget(av)
        ur.addLayout(info)
        ur.addStretch()
        lo.addWidget(user_row)
        lo.addSpacing(8)

        # ── Logout ────────────────────────────────────────────
        logout = QPushButton("Sign out")
        logout.setFixedHeight(36)
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet("""
            QPushButton {
                background: rgba(220,38,38,0.12);
                color: #FCA5A5;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(220,38,38,0.22);
                color: #FEE2E2;
            }
        """)
        logout.clicked.connect(self.on_logout)
        lo.addWidget(logout)

    def set_active(self, key: str):
        for k, item in self.nav_items.items():
            item.set_active(k == key)


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.setWindowTitle(CONFIG.get("business_name", "PosFlow"))
        self.setMinimumSize(1120, 700)
        self._views   = {}
        self._cur_key = None
        self._build_ui()
        first = next(
            (k for _, k, r in NAV if user.role in r), None
        )
        if first:
            self._navigate(first)

    def _build_ui(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(Th.APP_STYLE)

        root = QWidget()
        root.setStyleSheet("background: #F8FAFC;")
        self.setCentralWidget(root)

        lo = QHBoxLayout(root)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        self.sidebar = Sidebar(
            self.current_user,
            self._navigate,
            self._logout,
        )
        lo.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #F8FAFC;")
        right.addWidget(self.stack)
        lo.addLayout(right)

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #F1F5F9;
            }
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(28, 0, 28, 0)

        self.page_title = QLabel("")
        self.page_title.setStyleSheet(
            f"color: {Th.INK_900}; font-size: 14px; font-weight: 600;"
        )
        bl.addWidget(self.page_title)
        bl.addStretch()

        self.clock = QLabel()
        self.clock.setStyleSheet(
            f"color: {Th.INK_300}; font-size: 12px;"
        )
        self._tick()
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)
        bl.addWidget(self.clock)
        return bar

    def _tick(self):
        self.clock.setText(
            QDateTime.currentDateTime().toString("ddd dd MMM yyyy   hh:mm:ss")
        )

    def _navigate(self, key: str):
        title_map = {k: l for l, k, _ in NAV}
        self.page_title.setText(title_map.get(key, ""))
        self.sidebar.set_active(key)
        self._cur_key = key

        if key not in self._views:
            self._views[key] = self._load_view(key)
            self.stack.addWidget(self._views[key])
        self.stack.setCurrentWidget(self._views[key])

    def _load_view(self, key: str) -> QWidget:
        try:
            if key == "pos":
                from app.views.sale_view import SaleView
                return SaleView(self.current_user)
            if key == "products":
                from app.views.product_view import ProductView
                return ProductView(self.current_user)
            if key == "stock":
                from app.views.stock_view import StockView
                return StockView(self.current_user)
            if key == "returns":
                from app.views.returns_view import ReturnsView
                return ReturnsView(self.current_user)
            if key == "reports":
                from app.views.reports_view import ReportsView
                return ReportsView(self.current_user)
            if key == "users":
                from app.views.users_view import UsersView
                return UsersView(self.current_user)
            if key == "settings":
                from app.views.settings_view import SettingsView
                return SettingsView(self.current_user)
        except Exception as e:
            logger.error("Load view '%s' error: %s", key, e)

        # Placeholder
        icons = {k: ICONS.get(k, "·") for _, k, _ in NAV}
        titles = {k: l for l, k, _ in NAV}
        w = QWidget()
        w.setStyleSheet("background: #F8FAFC;")
        vl = QVBoxLayout(w)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic = QLabel(icons.get(key, "·"))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 40px; color: #CBD5E1; background: transparent;")
        lb = QLabel(f"{titles.get(key, '')} module")
        lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lb.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {Th.INK_300}; background: transparent;")
        vl.addWidget(ic); vl.addSpacing(8); vl.addWidget(lb)
        return w

    def _logout(self):
        from app.views.login_view import LoginView
        self.login = LoginView()
        self.login.show()
        self.close()
