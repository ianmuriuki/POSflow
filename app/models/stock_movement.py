"""
app/models/stock_movement.py
-----------------------------
StockMovement — immutable audit log of every stock change.
No record here should ever be deleted or edited.
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id:              Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id:      Mapped[int]          = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    user_id:         Mapped[int]          = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    movement_type:   Mapped[str]          = mapped_column(String(30), nullable=False)
    # movement_type: sale | return | adjustment_add | adjustment_remove | opening_stock | dispatch
    quantity_change: Mapped[float]        = mapped_column(Float, nullable=False)  # negative = deduction
    stock_before:    Mapped[float]        = mapped_column(Float, nullable=False)
    stock_after:     Mapped[float]        = mapped_column(Float, nullable=False)
    reference_id:    Mapped[int | None]   = mapped_column(Integer, nullable=True)  # sale_id or return_id
    reason:          Mapped[str | None]   = mapped_column(Text, nullable=True)
    created_at:      Mapped[datetime]     = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    user    = relationship("User", back_populates="stock_movements")

    def __repr__(self) -> str:
        return (f"<StockMovement product_id={self.product_id} "
                f"type={self.movement_type!r} change={self.quantity_change}>")
