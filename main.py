"""
main.py
-------
PosFlow application entry point.
Initialises Qt, checks the database, and launches the login screen.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from app.config import CONFIG

# ── Logging setup ───────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, CONFIG.get("log_level", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting PosFlow v%s", CONFIG.get("app_version", "1.0.0"))

    app = QApplication(sys.argv)
    app.setApplicationName("PosFlow")
    app.setOrganizationName(CONFIG.get("business_name", "PosFlow"))

    # Apply design system
    from app.utils.theme import Th
    app.setStyleSheet(Th.APP_STYLE)
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Import here to avoid circular imports at module level
    from app.views.login_view import LoginView
    window = LoginView()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
