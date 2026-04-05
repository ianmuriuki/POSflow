"""
app/views/login_view.py
-----------------------
Login screen — the first screen the user sees.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.config import CONFIG

logger = logging.getLogger(__name__)


class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PosFlow — Login")
        self.setMinimumSize(1100, 700)
        self.showMaximized()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("QWidget { background-color: #1A3C6B; }")

        # ── Outer layout — centers the card both ways ────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        outer.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._build_card())
        row.addStretch(1)

        outer.addLayout(row)
        outer.addStretch(1)

    def _build_card(self) -> QFrame:
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(0)

        # ── Logo / title ─────────────────────────────────────
        logo = QLabel("POSFLOW")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            color: #1A3C6B;
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 6px;
            background: transparent;
        """)

        biz = QLabel(CONFIG.get("business_name", "My Business"))
        biz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        biz.setStyleSheet("color: #6B7280; font-size: 13px; background: transparent;")

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #E5E7EB; background: #E5E7EB; margin: 16px 0px;")
        divider.setFixedHeight(1)

        welcome = QLabel("Welcome back")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("color: #1A3C6B; font-size: 20px; font-weight: bold; background: transparent;")

        hint = QLabel("Sign in to continue")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #9CA3AF; font-size: 12px; background: transparent; margin-bottom: 24px;")

        # ── Fields ───────────────────────────────────────────
        user_label = QLabel("Username")
        user_label.setStyleSheet("color: #374151; font-size: 12px; font-weight: bold; background: transparent; margin-top: 8px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(46)
        self.username_input.setStyleSheet(self._field_style())

        pass_label = QLabel("Password")
        pass_label.setStyleSheet("color: #374151; font-size: 12px; font-weight: bold; background: transparent; margin-top: 12px;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(46)
        self.password_input.setStyleSheet(self._field_style())
        self.password_input.returnPressed.connect(self._attempt_login)

        # ── Error box ─────────────────────────────────────────
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            color: #DC2626;
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 8px;
            padding: 10px;
            font-size: 12px;
            margin-top: 12px;
        """)
        self.error_label.hide()

        # ── Button ────────────────────────────────────────────
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A3C6B;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover  { background-color: #2E75B6; }
            QPushButton:pressed{ background-color: #14305A; }
            QPushButton:disabled{ background-color: #9CA3AF; }
        """)
        self.login_btn.clicked.connect(self._attempt_login)

        # ── Version ───────────────────────────────────────────
        version = QLabel(f"PosFlow v{CONFIG.get('app_version', '1.0.0')}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #D1D5DB; font-size: 11px; background: transparent; margin-top: 24px;")

        # ── Assemble ──────────────────────────────────────────
        for w in [logo, biz, divider, welcome, hint,
                  user_label, self.username_input,
                  pass_label, self.password_input,
                  self.error_label, self.login_btn, version]:
            layout.addWidget(w)

        return card

    def _field_style(self):
        return """
            QLineEdit {
                border: 1.5px solid #D1D5DB;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 13px;
                color: #111827;
                background-color: #F9FAFB;
            }
            QLineEdit:focus {
                border-color: #2E75B6;
                background-color: white;
            }
        """

    def _attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        self.error_label.hide()

        try:
            from app.services.auth_service import AuthService
            user = AuthService.login(username, password)
            if user:
                self._open_main_window(user)
            else:
                self._show_error("Incorrect username or password.")
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            logger.error("Login error: %s", e)
            self._show_error("An error occurred. Please try again.")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()

    def _open_main_window(self, user):
        from app.views.main_window import MainWindow
        self.main_window = MainWindow(user)
        self.main_window.showMaximized()
        self.close()
