"""
app/models/product.py
---------------------
Product model — represents an item in the product catalogue.
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id:                  Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:                Mapped[str]      = mapped_column(String(150), nullable=False)
    category:            Mapped[str]      = mapped_column(String(80), nullable=False)
    price:               Mapped[float]    = mapped_column(Float, nullable=False)
    unit:                Mapped[str]      = mapped_column(String(30), default="piece", nullable=False)
    barcode:             Mapped[str|None] = mapped_column(String(100), unique=True, nullable=True)
    stock:               Mapped[float]    = mapped_column(Float, default=0.0, nullable=False)
    low_stock_threshold: Mapped[float]    = mapped_column(Float, default=5.0, nullable=False)
    is_active:           Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_by:          Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at:          Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at:          Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc),
                                                          onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sale_items      = relationship("SaleItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    returns         = relationship("ReturnTransaction", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} stock={self.stock}>"

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.low_stock_threshold

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock <= 0
