"""
app/models/setting.py
----------------------
App-wide key-value settings stored in the database.
These can be updated at runtime (e.g. business name, printer port).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Setting(Base):
    __tablename__ = "app_settings"

    key:   Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    def __repr__(self) -> str:
        return f"<Setting key={self.key!r} value={self.value!r}>"
