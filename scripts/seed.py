"""
scripts/seed.py
---------------
Run once on first setup to create the default Admin account and app settings.
Usage: python scripts/seed.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcrypt
from app.database import get_session
from app.models.user import User
from app.models.setting import Setting

DEFAULT_SETTINGS = [
    ("business_name",           "My Business"),
    ("currency",                "KES"),
    ("receipt_footer",          "Thank you for your business!"),
    ("printer_port",            "auto"),
    ("session_timeout_minutes", "30"),
    ("last_backup_at",          ""),
]

def seed():
    with get_session() as session:

        # ── Admin account ──────────────────────────────────────
        existing = session.query(User).filter_by(username="admin").first()
        if existing:
            print("Admin account already exists — skipping.")
        else:
            password_hash = bcrypt.hashpw(b"admin1234", bcrypt.gensalt()).decode()
            admin = User(
                username="admin",
                full_name="System Admin",
                role="admin",
                password_hash=password_hash,
                is_active=True,
            )
            session.add(admin)
            print("Admin account created.")
            print("  Username : admin")
            print("  Password : admin1234")
            print("  !! Change this password after first login !!")

        # ── App settings ───────────────────────────────────────
        for key, value in DEFAULT_SETTINGS:
            exists = session.query(Setting).filter_by(key=key).first()
            if not exists:
                session.add(Setting(key=key, value=value))
                print(f"Setting added: {key} = {value}")

        print("\nSeed complete. Database is ready.")

if __name__ == "__main__":
    seed()
