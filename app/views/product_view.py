"""
app/views/product_view.py
--------------------------
Product management screen — list, add, edit, deactivate.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QGridLayout, QDialog,
    QFormLayout, QComboBox, QDoubleSpinBox, QMessageBox,
    QGraphicsDropShadowEffect, QSizePolicy, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Food & Beverages", "Grocery", "Meat & Poultry", "Dairy",
    "Hardware", "Electronics", "Clothing", "Stationery",
    "Cleaning", "Pharmaceuticals", "Other"
]

UNITS = ["piece", "kg", "g", "litre", "ml", "pack", "box", "dozen", "pair"]


# ── Helpers ─────────────────────────────────────────────────────

def card_shadow() -> QGraphicsDropShadowEffect:
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(18)
    s.setOffset(0, 2)
    s.setColor(QColor(0, 0, 0, 18))
    return s


def _field(placeholder="", read_only=False) -> QLineEdit:
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setReadOnly(read_only)
    f.setFixedHeight(40)
    f.setStyleSheet("""
        QLineEdit {
            border: 1.5px solid #E5E7EB;
            border-radius: 8px;
            padding: 0 12px;
            font-size: 13px;
            color: #111827;
            background: #FAFAFA;
        }
        QLineEdit:focus {
            border-color: #1A3C6B;
            background: white;
        }
        QLineEdit:read-only {
            background: #F3F4F6;
            color: #9CA3AF;
        }
    """)
    return f


def _combo(items: list) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    c.setFixedHeight(40)
    c.setStyleSheet("""
        QComboBox {
            border: 1.5px solid #E5E7EB;
            border-radius: 8px;
            padding: 0 12px;
            font-size: 13px;
            color: #111827;
            background: #FAFAFA;
        }
        QComboBox:focus { border-color: #1A3C6B; background: white; }
        QComboBox::drop-down { border: none; width: 28px; }
        QComboBox QAbstractItemView {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            selection-background-color: #EFF6FF;
            selection-color: #1A3C6B;
            font-size: 13px;
        }
    """)
    return c


def _spinbox(min_val=0.0, max_val=999999.0, decimals=2, prefix="") -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_val, max_val)
    s.setDecimals(decimals)
    s.setPrefix(prefix)
    s.setFixedHeight(40)
    s.setStyleSheet("""
        QDoubleSpinBox {
            border: 1.5px solid #E5E7EB;
            border-radius: 8px;
            padding: 0 12px;
            font-size: 13px;
            color: #111827;
            background: #FAFAFA;
        }
        QDoubleSpinBox:focus { border-color: #1A3C6B; background: white; }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0; }
    """)
    return s


def _label(text, size=12, bold=False, color="#6B7280") -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"font-size: {size}px; font-weight: {'bold' if bold else '400'}; color: {color}; background: transparent;")
    return l


# ── Product Card Widget ──────────────────────────────────────────

class ProductCard(QFrame):
    edit_clicked   = pyqtSignal(dict)
    toggle_clicked = pyqtSignal(int, bool)

    def __init__(self, product: dict, parent=None):
        super().__init__(parent)
        self.product = product
        self.setFixedHeight(148)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._build()
        self.setGraphicsEffect(card_shadow())

    def _build(self):
        p = self.product
        is_active = p.get("is_active", True)
        low_stock = p.get("stock", 0) <= p.get("low_stock_threshold", 5)

        self.setStyleSheet(f"""
            QFrame {{
                background: {'white' if is_active else '#FAFAFA'};
                border-radius: 12px;
                border: 1px solid {'#E5E7EB' if is_active else '#F3F4F6'};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(8)

        # ── Row 1: name + badge ──────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        name = QLabel(p["name"])
        name.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {'#111827' if is_active else '#9CA3AF'};
            background: transparent;
        """)
        name.setWordWrap(True)
        top.addWidget(name, 1)

        if not is_active:
            badge = QLabel("Inactive")
            badge.setStyleSheet("""
                background: #F3F4F6; color: #9CA3AF;
                border-radius: 6px; padding: 2px 8px; font-size: 11px;
            """)
            top.addWidget(badge)
        elif low_stock:
            badge = QLabel("Low Stock")
            badge.setStyleSheet("""
                background: #FEF3C7; color: #D97706;
                border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: bold;
            """)
            top.addWidget(badge)

        outer.addLayout(top)

        # ── Row 2: category + unit ───────────────────────────
        meta = QHBoxLayout()
        meta.setSpacing(6)

        cat = QLabel(p.get("category", "—"))
        cat.setStyleSheet("font-size: 11px; color: #6B7280; background: #F3F4F6; border-radius: 4px; padding: 2px 8px;")

        unit = QLabel(p.get("unit", "piece"))
        unit.setStyleSheet("font-size: 11px; color: #6B7280; background: #F3F4F6; border-radius: 4px; padding: 2px 8px;")

        meta.addWidget(cat)
        meta.addWidget(unit)
        meta.addStretch()
        outer.addLayout(meta)

        # ── Row 3: price + stock ─────────────────────────────
        mid = QHBoxLayout()

        price = QLabel(f"KES {p.get('price', 0):,.2f}")
        price.setStyleSheet("font-size: 18px; font-weight: bold; color: #1A3C6B; background: transparent;")

        stock_color = "#D97706" if low_stock else "#059669"
        stock = QLabel(f"Stock: {p.get('stock', 0):g} {p.get('unit','')}")
        stock.setStyleSheet(f"font-size: 12px; color: {stock_color}; background: transparent;")

        mid.addWidget(price)
        mid.addStretch()
        mid.addWidget(stock)
        outer.addLayout(mid)

        # ── Row 4: barcode + actions ─────────────────────────
        bot = QHBoxLayout()

        bc = p.get("barcode") or ""
        barcode_lbl = QLabel(f"# {bc}" if bc else "No barcode")
        barcode_lbl.setStyleSheet("font-size: 11px; color: #D1D5DB; background: transparent;")
        bot.addWidget(barcode_lbl)
        bot.addStretch()

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(58, 28)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #EFF6FF; color: #1A3C6B;
                border: none; border-radius: 6px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #DBEAFE; }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.product))

        toggle_label = "Activate" if not is_active else "Deactivate"
        toggle_btn = QPushButton(toggle_label)
        toggle_btn.setFixedSize(78, 28)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#FEF2F2' if is_active else '#F0FDF4'};
                color: {'#DC2626' if is_active else '#059669'};
                border: none; border-radius: 6px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {'#FEE2E2' if is_active else '#DCFCE7'};
            }}
        """)
        toggle_btn.clicked.connect(
            lambda: self.toggle_clicked.emit(self.product["id"], not is_active)
        )

        bot.addWidget(edit_btn)
        bot.addSpacing(6)
        bot.addWidget(toggle_btn)
        outer.addLayout(bot)


# ── Add / Edit Dialog ────────────────────────────────────────────

class ProductDialog(QDialog):
    def __init__(self, user, product: dict = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.product = product
        self.is_edit = product is not None
        self.setWindowTitle("Edit Product" if self.is_edit else "New Product")
        self.setFixedWidth(480)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: white; border-radius: 16px; }")
        self._build()
        if self.is_edit:
            self._populate()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(6)

        # Title
        title = QLabel("Edit Product" if self.is_edit else "Add New Product")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        sub = QLabel("All fields marked * are required")
        sub.setStyleSheet("font-size: 12px; color: #9CA3AF; margin-bottom: 12px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        def row(label_text, widget):
            layout.addWidget(_label(label_text, size=12, bold=True, color="#374151"))
            layout.addWidget(widget)
            layout.addSpacing(4)

        # Fields
        self.name_input    = _field("e.g. White Sugar 1kg")
        self.barcode_input = _field("Scan or type barcode (optional)")
        self.cat_input     = _combo(CATEGORIES)
        self.unit_input    = _combo(UNITS)
        self.price_input   = _spinbox(0.01, 999999, 2, "KES ")
        self.stock_input   = _spinbox(0, 99999, 2)
        self.threshold_input = _spinbox(0, 9999, 0)
        self.threshold_input.setValue(5)

        row("Product Name *", self.name_input)
        row("Barcode", self.barcode_input)
        row("Category *", self.cat_input)
        row("Unit of Measure *", self.unit_input)
        row("Selling Price *", self.price_input)

        if not self.is_edit:
            row("Opening Stock *", self.stock_input)

        row("Low Stock Alert Threshold", self.threshold_input)

        layout.addSpacing(12)

        # Buttons
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(44)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet("""
            QPushButton {
                background: #F3F4F6; color: #374151;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #E5E7EB; }
        """)
        cancel.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save Product")
        self.save_btn.setFixedHeight(44)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #1A3C6B; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #2E75B6; }
            QPushButton:disabled { background: #D1D5DB; }
        """)
        self.save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel)
        btn_row.addSpacing(8)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        # Error
        self.err = QLabel("")
        self.err.setStyleSheet("""
            color: #DC2626; background: #FEF2F2;
            border: 1px solid #FECACA; border-radius: 8px;
            padding: 8px; font-size: 12px; margin-top: 8px;
        """)
        self.err.setWordWrap(True)
        self.err.hide()
        layout.addWidget(self.err)

    def _populate(self):
        p = self.product
        self.name_input.setText(p.get("name", ""))
        self.barcode_input.setText(p.get("barcode") or "")
        idx = self.cat_input.findText(p.get("category", ""))
        if idx >= 0:
            self.cat_input.setCurrentIndex(idx)
        idx2 = self.unit_input.findText(p.get("unit", "piece"))
        if idx2 >= 0:
            self.unit_input.setCurrentIndex(idx2)
        self.price_input.setValue(p.get("price", 0))
        self.threshold_input.setValue(p.get("low_stock_threshold", 5))

    def _save(self):
        name  = self.name_input.text().strip()
        price = self.price_input.value()

        if not name:
            self._show_err("Product name is required.")
            return
        if price <= 0:
            self._show_err("Price must be greater than zero.")
            return

        self.result_data = {
            "name":                name,
            "barcode":             self.barcode_input.text().strip() or None,
            "category":            self.cat_input.currentText(),
            "unit":                self.unit_input.currentText(),
            "price":               price,
            "stock":               self.stock_input.value() if not self.is_edit else None,
            "low_stock_threshold": self.threshold_input.value(),
        }
        self.accept()

    def _show_err(self, msg):
        self.err.setText(msg)
        self.err.show()


# ── Main Product View ────────────────────────────────────────────

class ProductView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.all_products = []
        self.filtered = []
        self.setStyleSheet("background: #F3F4F6;")
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Toolbar ──────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or barcode...")
        self.search.setFixedHeight(42)
        self.search.setMaximumWidth(320)
        self.search.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #E5E7EB;
                border-radius: 10px;
                padding: 0 16px 0 16px;
                font-size: 13px;
                background: white;
                color: #111827;
            }
            QLineEdit:focus { border-color: #1A3C6B; }
        """)
        self.search.textChanged.connect(self._filter)

        self.cat_filter = _combo(["All Categories"] + CATEGORIES)
        self.cat_filter.setFixedHeight(42)
        self.cat_filter.setFixedWidth(180)
        self.cat_filter.currentTextChanged.connect(self._filter)

        self.status_filter = _combo(["Active", "Inactive", "All"])
        self.status_filter.setFixedHeight(42)
        self.status_filter.setFixedWidth(110)
        self.status_filter.currentTextChanged.connect(self._filter)

        toolbar.addWidget(self.search)
        toolbar.addWidget(self.cat_filter)
        toolbar.addWidget(self.status_filter)
        toolbar.addStretch()

        # Stats
        self.stat_label = _label("", size=12, color="#6B7280")
        toolbar.addWidget(self.stat_label)

        if self.user.is_admin:
            add_btn = QPushButton("+ Add Product")
            add_btn.setFixedHeight(42)
            add_btn.setFixedWidth(140)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet("""
                QPushButton {
                    background: #1A3C6B; color: white;
                    border: none; border-radius: 10px;
                    font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background: #2E75B6; }
            """)
            add_btn.clicked.connect(self._open_add_dialog)
            toolbar.addWidget(add_btn)

        root.addLayout(toolbar)

        # ── Scroll grid ───────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { width: 6px; background: transparent; }
            QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.grid_container)
        root.addWidget(scroll)

        # Empty state
        self.empty_state = QWidget()
        self.empty_state.setStyleSheet("background: transparent;")
        es_layout = QVBoxLayout(self.empty_state)
        es_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_icon = QLabel("📦")
        es_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_icon.setStyleSheet("font-size: 48px; background: transparent;")
        es_text = QLabel("No products found")
        es_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_text.setStyleSheet("font-size: 16px; font-weight: bold; color: #9CA3AF; background: transparent;")
        es_sub = QLabel("Try adjusting your filters or add a new product")
        es_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_sub.setStyleSheet("font-size: 13px; color: #D1D5DB; background: transparent;")
        es_layout.addWidget(es_icon)
        es_layout.addWidget(es_text)
        es_layout.addWidget(es_sub)
        self.empty_state.hide()
        root.addWidget(self.empty_state)

    # ── Data ─────────────────────────────────────────────────────

    def _load_products(self):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                products = session.query(Product).order_by(Product.name).all()
                self.all_products = [
                    {
                        "id":                  p.id,
                        "name":                p.name,
                        "category":            p.category,
                        "price":               p.price,
                        "unit":                p.unit,
                        "barcode":             p.barcode,
                        "stock":               p.stock,
                        "low_stock_threshold": p.low_stock_threshold,
                        "is_active":           p.is_active,
                    }
                    for p in products
                ]
            self._filter()
        except Exception as e:
            logger.error("Failed to load products: %s", e)

    def _filter(self):
        query   = self.search.text().strip().lower()
        cat     = self.cat_filter.currentText()
        status  = self.status_filter.currentText()

        result = []
        for p in self.all_products:
            if query and query not in p["name"].lower() and query not in (p["barcode"] or "").lower():
                continue
            if cat != "All Categories" and p["category"] != cat:
                continue
            if status == "Active"   and not p["is_active"]:
                continue
            if status == "Inactive" and p["is_active"]:
                continue
            result.append(p)

        self.filtered = result
        self._render_grid()

    def _render_grid(self):
        # Clear existing cards
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.filtered:
            self.empty_state.show()
            self.stat_label.setText("")
            return

        self.empty_state.hide()
        cols = 3
        for i, p in enumerate(self.filtered):
            card = ProductCard(p)
            card.edit_clicked.connect(self._open_edit_dialog)
            card.toggle_clicked.connect(self._toggle_product)
            self.grid.addWidget(card, i // cols, i % cols)

        # Fill remaining cells in last row
        remainder = len(self.filtered) % cols
        if remainder:
            row = len(self.filtered) // cols
            for c in range(remainder, cols):
                spacer = QWidget()
                spacer.setStyleSheet("background: transparent;")
                self.grid.addWidget(spacer, row, c)

        active = sum(1 for p in self.all_products if p["is_active"])
        self.stat_label.setText(
            f"{len(self.filtered)} of {len(self.all_products)} products  ·  {active} active"
        )

    # ── Actions ──────────────────────────────────────────────────

    def _open_add_dialog(self):
        dlg = ProductDialog(self.user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._create_product(dlg.result_data)

    def _open_edit_dialog(self, product: dict):
        dlg = ProductDialog(self.user, product=product, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_product(product["id"], dlg.result_data)

    def _create_product(self, data: dict):
        try:
            from app.database import get_session
            from app.models.product import Product
            from app.models.stock_movement import StockMovement
            with get_session() as session:
                p = Product(
                    name=data["name"],
                    category=data["category"],
                    price=data["price"],
                    unit=data["unit"],
                    barcode=data["barcode"],
                    stock=data["stock"],
                    low_stock_threshold=data["low_stock_threshold"],
                    is_active=True,
                    created_by=self.user.id,
                )
                session.add(p)
                session.flush()

                # Record opening stock movement
                if data["stock"] > 0:
                    session.add(StockMovement(
                        product_id=p.id,
                        user_id=self.user.id,
                        movement_type="opening_stock",
                        quantity_change=data["stock"],
                        stock_before=0,
                        stock_after=data["stock"],
                        reason="Opening stock on product creation",
                    ))

            self._show_toast(f"'{data['name']}' added successfully.")
            self._load_products()
        except Exception as e:
            logger.error("Create product error: %s", e)
            QMessageBox.critical(self, "Error", f"Could not save product.\n{e}")

    def _update_product(self, product_id: int, data: dict):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                p = session.get(Product, product_id)
                if p:
                    p.name                = data["name"]
                    p.category            = data["category"]
                    p.price               = data["price"]
                    p.unit                = data["unit"]
                    p.barcode             = data["barcode"]
                    p.low_stock_threshold = data["low_stock_threshold"]

            self._show_toast(f"'{data['name']}' updated.")
            self._load_products()
        except Exception as e:
            logger.error("Update product error: %s", e)
            QMessageBox.critical(self, "Error", f"Could not update product.\n{e}")

    def _toggle_product(self, product_id: int, new_state: bool):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                p = session.get(Product, product_id)
                if p:
                    p.is_active = new_state
            self._load_products()
        except Exception as e:
            logger.error("Toggle product error: %s", e)

    # ── Toast notification ────────────────────────────────────────

    def _show_toast(self, message: str):
        toast = QLabel(f"  ✓  {message}", self)
        toast.setStyleSheet("""
            background: #1A3C6B;
            color: white;
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: bold;
        """)
        toast.setFixedHeight(44)
        toast.adjustSize()
        toast.move(
            (self.width() - toast.width()) // 2,
            self.height() - 80
        )
        toast.show()
        toast.raise_()
        QTimer.singleShot(2400, toast.deleteLater)
