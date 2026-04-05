"""
app/models/return_transaction.py
---------------------------------
ReturnTransaction — records a customer return linked to an original sale.
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ReturnTransaction(Base):
    __tablename__ = "return_transactions"

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_sale_id: Mapped[int]      = mapped_column(Integer, ForeignKey("sales.id"), nullable=False)
    processed_by:     Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    product_id:       Mapped[int]      = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity:         Mapped[float]    = mapped_column(Float, nullable=False)
    reason:           Mapped[str]      = mapped_column(Text, nullable=False)
    refund_amount:    Mapped[float]    = mapped_column(Float, nullable=False)
    created_at:       Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    original_sale      = relationship("Sale", back_populates="returns")
    processed_by_user  = relationship("User", back_populates="returns")
    product            = relationship("Product", back_populates="returns")

    def __repr__(self) -> str:
        return (f"<ReturnTransaction id={self.id} "
                f"sale_id={self.original_sale_id} qty={self.quantity}>")
