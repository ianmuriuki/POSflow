"""
app/services/auth_service.py
-----------------------------
Handles login, password verification, and session user context.
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass
import bcrypt

from app.database import get_session
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class SessionUser:
    """
    Plain data object holding the logged-in user's info.
    Safe to pass around outside database sessions.
    """
    id:         int
    username:   str
    full_name:  str
    role:       str
    is_active:  bool

    @property
    def is_admin(self):    return self.role == "admin"
    @property
    def is_manager(self):  return self.role == "manager"
    @property
    def is_cashier(self):  return self.role == "cashier"
    @property
    def can_manage_stock(self): return self.role in ("admin", "manager")
    @property
    def can_view_reports(self): return self.role in ("admin", "manager")


class AuthService:

    @staticmethod
    def login(username: str, password: str) -> SessionUser | None:
        """
        Verify credentials. Returns a SessionUser on success, None on failure.
        """
        with get_session() as session:
            user = session.query(User).filter_by(
                username=username,
                is_active=True
            ).first()

            if not user:
                logger.warning("Login failed — unknown user: '%s'", username)
                return None

            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                logger.warning("Login failed — wrong password for: '%s'", username)
                return None

            # Update last login timestamp
            user.last_login = datetime.now(timezone.utc)

            # Copy all needed data into a plain object BEFORE session closes
            session_user = SessionUser(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
            )

        logger.info("User '%s' logged in (role: %s)", username, session_user.role)
        return session_user

    @staticmethod
    def hash_password(plain: str) -> str:
        """Hash a plain-text password. Used when creating/updating users."""
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
