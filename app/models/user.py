"""
app/models/user.py
------------------
User model — represents a system user (Admin, Manager, or Cashier).
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    username:      Mapped[str]      = mapped_column(String(50), unique=True, nullable=False)
    full_name:     Mapped[str]      = mapped_column(String(100), nullable=False)
    role:          Mapped[str]      = mapped_column(String(20), nullable=False)   # admin | manager | cashier
    password_hash: Mapped[str]      = mapped_column(String(255), nullable=False)
    is_active:     Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at:    Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    sales           = relationship("Sale", back_populates="cashier", foreign_keys="Sale.cashier_id")
    stock_movements = relationship("StockMovement", back_populates="user")
    returns         = relationship("ReturnTransaction", back_populates="processed_by_user")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"

    @property
    def is_cashier(self) -> bool:
        return self.role == "cashier"

    @property
    def can_manage_stock(self) -> bool:
        return self.role in ("admin", "manager")

    @property
    def can_view_reports(self) -> bool:
        return self.role in ("admin", "manager")
