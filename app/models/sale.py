"""
app/models/sale.py
------------------
Sale and SaleItem models.
A Sale has one or more SaleItems (line items).
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Sale(Base):
    __tablename__ = "sales"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    receipt_number: Mapped[str]           = mapped_column(String(30), unique=True, nullable=False)
    cashier_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status:         Mapped[str]           = mapped_column(String(20), default="completed", nullable=False)
    # status: pending | dispatched | completed
    payment_method: Mapped[str]           = mapped_column(String(20), nullable=False)
    # payment_method: cash | mpesa | card | credit
    payment_ref:    Mapped[str | None]    = mapped_column(String(100), nullable=True)
    subtotal:       Mapped[float]         = mapped_column(Float, nullable=False)
    discount:       Mapped[float]         = mapped_column(Float, default=0.0, nullable=False)
    total:          Mapped[float]         = mapped_column(Float, nullable=False)
    notes:          Mapped[str | None]    = mapped_column(Text, nullable=True)
    is_reprinted:   Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    created_at:     Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at:   Mapped[datetime|None] = mapped_column(DateTime, nullable=True)

    # Relationships
    cashier  = relationship("User", back_populates="sales", foreign_keys=[cashier_id])
    items    = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    returns  = relationship("ReturnTransaction", back_populates="original_sale")

    def __repr__(self) -> str:
        return f"<Sale id={self.id} receipt={self.receipt_number!r} total={self.total}>"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id:           Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id:      Mapped[int]   = mapped_column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id:   Mapped[int]   = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str]   = mapped_column(String(150), nullable=False)  # snapshot at time of sale
    unit_price:   Mapped[float] = mapped_column(Float, nullable=False)         # snapshot at time of sale
    quantity:     Mapped[float] = mapped_column(Float, nullable=False)
    line_total:   Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    sale    = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    def __repr__(self) -> str:
        return f"<SaleItem product={self.product_name!r} qty={self.quantity} total={self.line_total}>"
