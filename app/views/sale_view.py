"""
app/views/sale_view.py
-----------------------
POS Screen — inspired by modern restaurant/retail POS design.
Clean product grid with category pills, inline qty controls,
and a professional cart panel.
"""
import logging
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QGridLayout, QDialog,
    QComboBox, QGraphicsDropShadowEffect, QSizePolicy,
    QButtonGroup, QAbstractButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from app.config import CONFIG
from app.utils.theme import Th

logger   = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")


# ─────────────────────────────────────────────────────────────────
# Category pill tab
# ─────────────────────────────────────────────────────────────────
class CategoryPill(QPushButton):
    def __init__(self, label: str, count: int = 0, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        display = f"{label}  {count}" if count else label
        self.setText(display)
        self._style()
        self.toggled.connect(lambda _: self._style())

    def _style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Th.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 18px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: white;
                    color: {Th.INK_500};
                    border: 1.5px solid #E2E8F0;
                    border-radius: 18px;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    border-color: {Th.PRIMARY};
                    color: {Th.PRIMARY};
                    background: {Th.PRIMARY_LIGHT};
                }}
            """)


# ─────────────────────────────────────────────────────────────────
# Product card  (matches the Tasty Station card style)
# ─────────────────────────────────────────────────────────────────
class ProductCard(QFrame):
    add_requested = pyqtSignal(dict)

    def __init__(self, product: dict, cart_qty: int = 0, parent=None):
        super().__init__(parent)
        self.product  = product
        self.cart_qty = cart_qty
        self.out      = product.get("stock", 0) <= 0
        self.setFixedSize(176, 148)
        self.setCursor(
            Qt.CursorShape.ArrowCursor if self.out
            else Qt.CursorShape.PointingHandCursor
        )
        self._apply_shadow()
        self._build()

    def _apply_shadow(self):
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(16)
        sh.setOffset(0, 2)
        sh.setColor(QColor(15, 23, 42, 10))
        self.setGraphicsEffect(sh)

    def _build(self):
        p = self.product
        selected = self.cart_qty > 0

        self.setStyleSheet(f"""
            QFrame {{
                background: {'#F8FAFC' if self.out else 'white'};
                border-radius: 14px;
                border: 1px solid #F1F5F9;
            }}
            QFrame:hover {{
                border-color: {'transparent' if self.out else '#E2E8F0'};
            }}
        """)

        lo = QVBoxLayout(self)
        lo.setContentsMargins(14, 14, 14, 12)
        lo.setSpacing(0)

        # Category label
        cat = QLabel(p.get("category", ""))
        cat.setStyleSheet(
            f"font-size:10px; color:{Th.INK_300}; font-weight:500;"
            " background:transparent;"
        )
        lo.addWidget(cat)
        lo.addSpacing(4)

        # Product name
        name = QLabel(p["name"])
        name.setWordWrap(True)
        name.setStyleSheet(
            f"font-size:13px; font-weight:700;"
            f" color:{'#CBD5E1' if self.out else Th.INK_900};"
            " background:transparent;"
        )
        lo.addWidget(name)
        lo.addStretch()

        # Price row + qty controls
        bottom = QHBoxLayout()
        bottom.setSpacing(0)
        bottom.setContentsMargins(0, 0, 0, 0)

        price = QLabel(f"{CURRENCY} {p['price']:,.2f}")
        price.setStyleSheet(
            f"font-size:13px; font-weight:700;"
            f" color:{'#CBD5E1' if self.out else Th.PRIMARY};"
            " background:transparent;"
        )
        bottom.addWidget(price)
        bottom.addStretch()

        if not self.out:
            ctrl = self._qty_control()
            bottom.addWidget(ctrl)

        lo.addLayout(bottom)

        # Out of stock label
        if self.out:
            lo.addSpacing(4)
            oos = QLabel("Out of stock")
            oos.setStyleSheet(
                f"font-size:10px; color:{Th.INK_300}; background:transparent;"
            )
            lo.addWidget(oos)

    def _qty_control(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lo = QHBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        if self.cart_qty > 0:
            # Show −  N  + inline
            minus = self._ctrl_btn("−", primary=False)
            minus.clicked.connect(self._on_minus)

            count = QLabel(str(self.cart_qty))
            count.setFixedWidth(26)
            count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count.setStyleSheet(
                f"font-size:13px; font-weight:700; color:{Th.INK_900};"
                " background:transparent;"
            )

            plus = self._ctrl_btn("+", primary=True)
            plus.clicked.connect(self._on_plus)

            lo.addWidget(minus)
            lo.addWidget(count)
            lo.addWidget(plus)
        else:
            # Show a single + button
            add = self._ctrl_btn("+", primary=True, size=30)
            add.clicked.connect(self._on_plus)
            lo.addWidget(add)

        return w

    def _ctrl_btn(self, text: str, primary: bool,
                  size: int = 26) -> QPushButton:
        b = QPushButton(text)
        b.setFixedSize(size, size)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {Th.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: {size // 2}px;
                    font-size: 16px;
                    font-weight: 700;
                }}
                QPushButton:hover {{ background: {Th.PRIMARY_HOVER}; }}
            """)
        else:
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {Th.INK_100};
                    color: {Th.INK_700};
                    border: none;
                    border-radius: {size // 2}px;
                    font-size: 16px;
                    font-weight: 700;
                }}
                QPushButton:hover {{ background: #E2E8F0; }}
            """)
        return b

    def _on_plus(self):
        if self.product.get("stock", 0) > self.cart_qty:
            self.add_requested.emit({"action": "add", "product": self.product})

    def _on_minus(self):
        self.add_requested.emit({"action": "remove", "product": self.product})

    def refresh(self, cart_qty: int):
        self.cart_qty = cart_qty
        # Rebuild in place
        old = self.layout()
        while old.count():
            item = old.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        old.deleteLater()
        self._build()


# ─────────────────────────────────────────────────────────────────
# Cart line item
# ─────────────────────────────────────────────────────────────────
class CartItem(QWidget):
    remove_clicked = pyqtSignal(int)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setFixedHeight(56)
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        lo = QHBoxLayout(self)
        lo.setContentsMargins(20, 0, 20, 0)
        lo.setSpacing(12)

        # Qty bubble
        qty_lbl = QLabel(f"{self.item['quantity']:g}×")
        qty_lbl.setFixedWidth(28)
        qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_lbl.setStyleSheet(f"""
            background: {Th.PRIMARY_LIGHT};
            color: {Th.PRIMARY};
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            padding: 2px 0;
        """)

        # Name + unit price
        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(self.item["name"])
        name.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{Th.INK_900};"
            " background:transparent;"
        )
        unit = QLabel(f"{CURRENCY} {self.item['unit_price']:,.2f} each")
        unit.setStyleSheet(
            f"font-size:11px; color:{Th.INK_300}; background:transparent;"
        )
        info.addWidget(name)
        info.addWidget(unit)

        # Line total
        total = QLabel(f"{CURRENCY} {self.item['line_total']:,.2f}")
        total.setStyleSheet(
            f"font-size:13px; font-weight:700; color:{Th.INK_900};"
            " background:transparent;"
        )
        total.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # Remove
        rm = QPushButton("×")
        rm.setFixedSize(22, 22)
        rm.setCursor(Qt.CursorShape.PointingHandCursor)
        rm.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Th.INK_300};
                border: none;
                border-radius: 11px;
                font-size: 16px;
                font-weight: 400;
            }}
            QPushButton:hover {{
                background: {Th.DANGER_LIGHT};
                color: {Th.DANGER};
            }}
        """)
        rm.clicked.connect(
            lambda: self.remove_clicked.emit(self.item["product_id"])
        )

        lo.addWidget(qty_lbl)
        lo.addLayout(info, 1)
        lo.addWidget(total)
        lo.addSpacing(4)
        lo.addWidget(rm)


# ─────────────────────────────────────────────────────────────────
# Payment Dialog — cash change calculator
# ─────────────────────────────────────────────────────────────────
class PaymentDialog(QDialog):
    def __init__(self, total: float, parent=None):
        super().__init__(parent)
        self.total            = total
        self.selected_payment = "cash"
        self.selected_ref     = None
        self.tendered_amount  = None
        self.change_amount    = None
        self.do_print         = False

        self.setModal(True)
        self.setFixedWidth(420)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background:white; border-radius:16px; border:none; }"
        )
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(40); sh.setOffset(0, 8)
        sh.setColor(QColor(15, 23, 42, 30))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)

        lo = QVBoxLayout(card)
        lo.setContentsMargins(28, 24, 28, 24)
        lo.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Payment")
        title.setStyleSheet(
            f"font-size:18px; font-weight:700; color:{Th.INK_900};"
        )
        close = QPushButton("✕")
        close.setFixedSize(30, 30)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet(f"""
            QPushButton {{
                background:{Th.INK_100}; color:{Th.INK_500};
                border:none; border-radius:8px; font-size:14px;
            }}
            QPushButton:hover {{ background:#E2E8F0; }}
        """)
        close.clicked.connect(self.reject)
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(close)
        lo.addLayout(hdr)

        # Amount due chip
        chip = QFrame()
        chip.setFixedHeight(80)
        chip.setStyleSheet(f"""
            QFrame {{
                background: {Th.PRIMARY_LIGHT};
                border-radius: 12px;
                border: none;
            }}
        """)
        cl = QVBoxLayout(chip)
        cl.setSpacing(2)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        due_lbl = QLabel("Amount Due")
        due_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        due_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{Th.PRIMARY_DIM};"
            " letter-spacing:0.5px; background:transparent;"
        )
        due_val = QLabel(f"{CURRENCY} {self.total:,.2f}")
        due_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        due_val.setStyleSheet(
            f"font-size:28px; font-weight:800; color:{Th.PRIMARY};"
            " background:transparent;"
        )
        cl.addWidget(due_lbl); cl.addWidget(due_val)
        lo.addWidget(chip)

        # Payment method selector — pill buttons
        pm_lbl = QLabel("Payment Method")
        pm_lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{Th.INK_300};"
            " letter-spacing:0.5px;"
        )
        lo.addWidget(pm_lbl)

        pm_row = QHBoxLayout()
        pm_row.setSpacing(8)
        self._pm_group = QButtonGroup(self)
        self._pm_group.setExclusive(True)

        for label, key in [
            ("Cash", "cash"), ("M-Pesa", "mpesa"),
            ("Card", "card"), ("Credit", "credit")
        ]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setFixedHeight(38)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setProperty("pm_key", key)
            self._pm_group.addButton(b)
            pm_row.addWidget(b)
            if key == "cash":
                b.setChecked(True)

        self._pm_group.buttonToggled.connect(self._on_pm_change)
        self._style_pm_btns()
        lo.addLayout(pm_row)

        # Reference field (hidden by default)
        self.ref_lbl = QLabel("Transaction Reference")
        self.ref_lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{Th.INK_300};"
            " letter-spacing:0.5px;"
        )
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. QKJ4RT92...")
        self.ref_input.setFixedHeight(44)
        self.ref_input.setStyleSheet(Th.input_style())
        self.ref_lbl.hide(); self.ref_input.hide()
        lo.addWidget(self.ref_lbl); lo.addWidget(self.ref_input)

        # Cash section
        self.cash_section = QWidget()
        self.cash_section.setStyleSheet("background:transparent;")
        cs = QVBoxLayout(self.cash_section)
        cs.setContentsMargins(0, 0, 0, 0)
        cs.setSpacing(10)

        tend_lbl = QLabel("Amount Tendered")
        tend_lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{Th.INK_300};"
            " letter-spacing:0.5px;"
        )

        self.tendered_input = QLineEdit()
        self.tendered_input.setPlaceholderText(
            f"Enter amount given by customer"
        )
        self.tendered_input.setFixedHeight(48)
        self.tendered_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Th.INK_50};
                border: 2px solid #E2E8F0;
                border-radius: 10px;
                padding: 0 16px;
                font-size: 18px;
                font-weight: 700;
                color: {Th.INK_900};
            }}
            QLineEdit:focus {{
                border-color: {Th.PRIMARY};
                background: white;
            }}
        """)
        self.tendered_input.textChanged.connect(self._calc_change)

        # Change display
        self.change_box = QFrame()
        self.change_box.setFixedHeight(52)
        self.change_box.setStyleSheet(f"""
            QFrame {{
                background: {Th.INK_50};
                border-radius: 10px;
                border: 1px solid #E2E8F0;
            }}
        """)
        cbl = QHBoxLayout(self.change_box)
        cbl.setContentsMargins(16, 0, 16, 0)

        change_title = QLabel("Change")
        change_title.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{Th.INK_500};"
            " background:transparent;"
        )
        self.change_val = QLabel("—")
        self.change_val.setStyleSheet(
            f"font-size:20px; font-weight:700; color:{Th.INK_300};"
            " background:transparent;"
        )
        self.change_val.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        cbl.addWidget(change_title)
        cbl.addStretch()
        cbl.addWidget(self.change_val)

        cs.addWidget(tend_lbl)
        cs.addWidget(self.tendered_input)
        cs.addWidget(self.change_box)
        lo.addWidget(self.cash_section)

        # Quick amount buttons
        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        for amt in [500, 1000, 2000, 5000]:
            b = QPushButton(f"{CURRENCY} {amt:,}")
            b.setFixedHeight(34)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: white;
                    color: {Th.INK_700};
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {Th.PRIMARY};
                    color: {Th.PRIMARY};
                    background: {Th.PRIMARY_LIGHT};
                }}
            """)
            b.clicked.connect(
                lambda _, a=amt: self._set_quick(a)
            )
            quick_row.addWidget(b)
        lo.addLayout(quick_row)

        lo.addSpacing(4)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel = Th.btn_secondary("Cancel", h=48)
        cancel.clicked.connect(self.reject)

        self.complete_btn = Th.btn_primary(
            f"Charge  {CURRENCY} {self.total:,.2f}", h=48
        )
        self.complete_btn.setEnabled(False)
        self.complete_btn.clicked.connect(lambda: self._finish(False))

        self.print_btn = Th.btn_success("Print Receipt", h=48, w=130)
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(lambda: self._finish(True))

        btn_row.addWidget(cancel)
        btn_row.addWidget(self.complete_btn, 1)
        btn_row.addWidget(self.print_btn)
        lo.addLayout(btn_row)

    def _style_pm_btns(self):
        for btn in self._pm_group.buttons():
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {Th.PRIMARY};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 700;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {Th.INK_50};
                        color: {Th.INK_500};
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        border-color: {Th.PRIMARY};
                        color: {Th.PRIMARY};
                    }}
                """)

    def _on_pm_change(self, btn, checked):
        if not checked:
            return
        self._style_pm_btns()
        key = btn.property("pm_key")
        self.selected_payment = key
        show_cash = key == "cash"
        show_ref  = key in ("mpesa", "card")
        self.cash_section.setVisible(show_cash)
        self.ref_lbl.setVisible(show_ref)
        self.ref_input.setVisible(show_ref)
        if not show_cash:
            self._set_btns_enabled(True)
        else:
            self._set_btns_enabled(False)

    def _calc_change(self):
        try:
            tendered = float(
                self.tendered_input.text().replace(",", "") or 0
            )
            change = tendered - self.total
            self.tendered_amount = tendered
            self.change_amount   = max(change, 0)

            if tendered <= 0:
                self.change_val.setText("—")
                self.change_val.setStyleSheet(
                    f"font-size:20px; font-weight:700; color:{Th.INK_300};"
                    " background:transparent;"
                )
                self.change_box.setStyleSheet(f"""
                    QFrame {{
                        background: {Th.INK_50};
                        border-radius: 10px;
                        border: 1px solid #E2E8F0;
                    }}
                """)
                self._set_btns_enabled(False)
            elif change < 0:
                self.change_val.setText(
                    f"Short  {CURRENCY} {abs(change):,.2f}"
                )
                self.change_val.setStyleSheet(
                    f"font-size:14px; font-weight:700; color:{Th.DANGER};"
                    " background:transparent;"
                )
                self.change_box.setStyleSheet(f"""
                    QFrame {{
                        background: {Th.DANGER_LIGHT};
                        border-radius: 10px;
                        border: 1px solid #FECACA;
                    }}
                """)
                self._set_btns_enabled(False)
            else:
                self.change_val.setText(f"{CURRENCY} {change:,.2f}")
                self.change_val.setStyleSheet(
                    f"font-size:20px; font-weight:700; color:{Th.SUCCESS};"
                    " background:transparent;"
                )
                self.change_box.setStyleSheet(f"""
                    QFrame {{
                        background: {Th.SUCCESS_LIGHT};
                        border-radius: 10px;
                        border: 1px solid #A7F3D0;
                    }}
                """)
                self._set_btns_enabled(True)
        except ValueError:
            self._set_btns_enabled(False)

    def _set_quick(self, amount: float):
        self.tendered_input.setText(str(amount))

    def _set_btns_enabled(self, enabled: bool):
        self.complete_btn.setEnabled(enabled)
        self.print_btn.setEnabled(enabled)

    def _finish(self, do_print: bool):
        self.do_print     = do_print
        self.selected_ref = self.ref_input.text().strip() or None
        if self.selected_payment != "cash":
            self.tendered_amount = self.total
            self.change_amount   = 0
            self._set_btns_enabled(True)
        self.accept()


# ─────────────────────────────────────────────────────────────────
# Main Sale View
# ─────────────────────────────────────────────────────────────────
class SaleView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user              = user
        self.cart              = {}       # product_id -> item dict
        self.all_products      = []
        self.filtered          = []
        self.active_category   = "All"
        self.setStyleSheet(f"background: {Th.INK_50};")
        self._build_ui()
        self._load_products()

    # ─── Layout ──────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left(), 1)

        # Right divider
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFixedWidth(1)
        vline.setStyleSheet(f"background: {Th.DIVIDER}; border: none;")
        root.addWidget(vline)

        root.addWidget(self._build_right(), 0)

    def _build_left(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {Th.INK_50};")
        lo = QVBoxLayout(w)
        lo.setContentsMargins(28, 20, 20, 20)
        lo.setSpacing(16)

        # ── Search bar ────────────────────────────────────────
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search product or scan barcode..."
        )
        self.search.setFixedHeight(44)
        self.search.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 0 16px 0 16px;
                font-size: 13px;
                color: {Th.INK_900};
            }}
            QLineEdit:focus {{
                border-color: {Th.PRIMARY};
            }}
        """)
        self.search.textChanged.connect(self._filter)
        lo.addWidget(self.search)

        # ── Category pills ────────────────────────────────────
        self.cat_scroll = QScrollArea()
        self.cat_scroll.setFixedHeight(44)
        self.cat_scroll.setWidgetResizable(True)
        self.cat_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.cat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.cat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cat_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        self.cat_widget = QWidget()
        self.cat_widget.setStyleSheet("background: transparent;")
        self.cat_layout = QHBoxLayout(self.cat_widget)
        self.cat_layout.setContentsMargins(0, 0, 0, 0)
        self.cat_layout.setSpacing(8)
        self.cat_layout.addStretch()
        self.cat_scroll.setWidget(self.cat_widget)
        lo.addWidget(self.cat_scroll)

        # ── Product grid ─────────────────────────────────────
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
            f"{Th.SCROLLBAR}"
        )

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.grid_scroll.setWidget(self.grid_container)
        lo.addWidget(self.grid_scroll, 1)

        # Empty state
        self.empty_lbl = QLabel("No products found")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(
            f"font-size:15px; color:{Th.INK_300}; background:transparent;"
        )
        self.empty_lbl.hide()
        lo.addWidget(self.empty_lbl)

        return w

    def _build_right(self) -> QWidget:
        """Cart panel — fixed width, clean, no ruled lines."""
        w = QWidget()
        w.setFixedWidth(380)
        w.setStyleSheet("background: white;")
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        # ── Cart header ───────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet("background: white;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(20, 0, 20, 0)

        cart_title = QLabel("Order Summary")
        cart_title.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{Th.INK_900};"
        )
        self.count_pill = QLabel("0 items")
        self.count_pill.setStyleSheet(f"""
            background: {Th.INK_100};
            color: {Th.INK_500};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        clear_btn = QPushButton("Clear all")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Th.DANGER};
                border: none;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ color: #991B1B; }}
        """)
        clear_btn.clicked.connect(self._clear_cart)

        hl.addWidget(cart_title)
        hl.addSpacing(8)
        hl.addWidget(self.count_pill)
        hl.addStretch()
        hl.addWidget(clear_btn)
        lo.addWidget(hdr)

        # Thin rule
        lo.addWidget(self._rule())

        # ── Cart items scroll ─────────────────────────────────
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cart_scroll.setStyleSheet(
            f"QScrollArea {{ background: white; border: none; }}"
            f"{Th.SCROLLBAR}"
        )

        self.cart_inner = QWidget()
        self.cart_inner.setStyleSheet("background: white;")
        self.cart_vbox = QVBoxLayout(self.cart_inner)
        self.cart_vbox.setContentsMargins(0, 8, 0, 8)
        self.cart_vbox.setSpacing(0)
        self.cart_vbox.addStretch()

        self.cart_scroll.setWidget(self.cart_inner)
        lo.addWidget(self.cart_scroll, 1)

        # Empty cart placeholder
        self.empty_cart = QWidget()
        self.empty_cart.setStyleSheet("background: white;")
        ecl = QVBoxLayout(self.empty_cart)
        ecl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ec_icon = QLabel("🛒")
        ec_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ec_icon.setStyleSheet("font-size:36px; background:transparent;")

        ec_text = QLabel("Cart is empty")
        ec_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ec_text.setStyleSheet(
            f"font-size:14px; font-weight:600; color:{Th.INK_300};"
            " background:transparent;"
        )
        ec_sub = QLabel("Tap a product to add it")
        ec_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ec_sub.setStyleSheet(
            f"font-size:12px; color:{Th.INK_300}; background:transparent;"
        )
        ecl.addWidget(ec_icon)
        ecl.addSpacing(8)
        ecl.addWidget(ec_text)
        ecl.addWidget(ec_sub)
        lo.addWidget(self.empty_cart)

        # ── Payment summary ───────────────────────────────────
        summary = QWidget()
        summary.setStyleSheet("background: white;")
        sl = QVBoxLayout(summary)
        sl.setContentsMargins(20, 16, 20, 0)
        sl.setSpacing(0)

        sl.addWidget(self._rule())
        sl.addSpacing(14)

        # Subtotal row
        sub_row = QHBoxLayout()
        sub_lbl = QLabel("Subtotal")
        sub_lbl.setStyleSheet(
            f"font-size:13px; color:{Th.INK_500}; background:transparent;"
        )
        self.subtotal_val = QLabel(f"{CURRENCY} 0.00")
        self.subtotal_val.setStyleSheet(
            f"font-size:13px; color:{Th.INK_700}; background:transparent;"
        )
        sub_row.addWidget(sub_lbl); sub_row.addStretch()
        sub_row.addWidget(self.subtotal_val)
        sl.addLayout(sub_row)
        sl.addSpacing(6)

        # Total row — larger
        tot_row = QHBoxLayout()
        tot_lbl = QLabel("Total Payable")
        tot_lbl.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{Th.INK_900};"
            " background:transparent;"
        )
        self.total_val = QLabel(f"{CURRENCY} 0.00")
        self.total_val.setStyleSheet(
            f"font-size:22px; font-weight:800; color:{Th.PRIMARY};"
            " background:transparent;"
        )
        tot_row.addWidget(tot_lbl); tot_row.addStretch()
        tot_row.addWidget(self.total_val)
        sl.addLayout(tot_row)
        sl.addSpacing(20)

        lo.addWidget(summary)

        # ── Action buttons ────────────────────────────────────
        actions = QWidget()
        actions.setStyleSheet("background: white;")
        al = QVBoxLayout(actions)
        al.setContentsMargins(20, 0, 20, 24)
        al.setSpacing(10)

        self.charge_btn = Th.btn_primary(
            f"Place Order  ·  {CURRENCY} 0.00", h=52, fs=14
        )
        self.charge_btn.setEnabled(False)
        self.charge_btn.clicked.connect(self._open_payment)

        self.fast_btn = QPushButton("⚡  Fast Sale — Cash")
        self.fast_btn.setFixedHeight(44)
        self.fast_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fast_btn.setEnabled(False)
        self.fast_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Th.SUCCESS_LIGHT};
                color: {Th.SUCCESS};
                border: 1.5px solid {Th.SUCCESS};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {Th.SUCCESS};
                color: white;
            }}
            QPushButton:disabled {{
                background: {Th.INK_50};
                color: {Th.INK_300};
                border-color: #E2E8F0;
            }}
        """)
        self.fast_btn.clicked.connect(self._fast_sale)

        al.addWidget(self.charge_btn)
        al.addWidget(self.fast_btn)
        lo.addWidget(actions)

        return w

    def _rule(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background: {Th.DIVIDER}; border: none;")
        return f

    # ─── Data loading ─────────────────────────────────────────────

    def _load_products(self):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                prods = (
                    session.query(Product)
                    .filter_by(is_active=True)
                    .order_by(Product.name)
                    .all()
                )
                self.all_products = [
                    {
                        "id":       p.id, "name":     p.name,
                        "category": p.category, "price":    p.price,
                        "unit":     p.unit, "barcode":  p.barcode,
                        "stock":    p.stock,
                        "low_stock_threshold": p.low_stock_threshold,
                    }
                    for p in prods
                ]
            self._rebuild_category_pills()
            self._filter()
        except Exception as e:
            logger.error("Load products: %s", e)

    def _rebuild_category_pills(self):
        # Clear existing pills
        while self.cat_layout.count():
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cats = ["All"] + sorted(
            set(p["category"] for p in self.all_products)
        )

        self._pill_group = QButtonGroup(self)
        self._pill_group.setExclusive(True)

        for cat in cats:
            count = (
                len(self.all_products) if cat == "All"
                else sum(
                    1 for p in self.all_products if p["category"] == cat
                )
            )
            pill = CategoryPill(cat, count)
            if cat == self.active_category:
                pill.setChecked(True)
            self._pill_group.addButton(pill)
            self.cat_layout.addWidget(pill)
            pill.clicked.connect(
                lambda _, c=cat: self._select_category(c)
            )

        self.cat_layout.addStretch()

    def _select_category(self, cat: str):
        self.active_category = cat
        self._filter()

    def _filter(self):
        q   = self.search.text().strip().lower()
        cat = self.active_category

        self.filtered = [
            p for p in self.all_products
            if (not q
                or q in p["name"].lower()
                or q in (p["barcode"] or "").lower())
            and (cat == "All" or p["category"] == cat)
        ]
        self._render_grid()

    def _render_grid(self):
        # Clear existing cards
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.filtered:
            self.empty_lbl.show()
            return

        self.empty_lbl.hide()
        cols = 4
        for i, p in enumerate(self.filtered):
            qty  = self.cart.get(p["id"], {}).get("quantity", 0)
            card = ProductCard(p, cart_qty=int(qty))
            card.add_requested.connect(self._on_card_action)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _refresh_card(self, product_id: int):
        """Refresh only the card that changed — no full re-render."""
        cols = 4
        for i, p in enumerate(self.filtered):
            if p["id"] != product_id:
                continue
            idx  = self.grid_layout.indexOf(
                self.grid_layout.itemAtPosition(i // cols, i % cols)
                and self.grid_layout.itemAtPosition(i // cols, i % cols).widget()
            )
            old_card = self.grid_layout.itemAtPosition(
                i // cols, i % cols
            )
            if old_card and old_card.widget():
                old_card.widget().deleteLater()

            qty  = self.cart.get(product_id, {}).get("quantity", 0)
            card = ProductCard(p, cart_qty=int(qty))
            card.add_requested.connect(self._on_card_action)
            self.grid_layout.addWidget(card, i // cols, i % cols)
            break

    # ─── Cart logic ───────────────────────────────────────────────

    def _on_card_action(self, payload: dict):
        action  = payload["action"]
        product = payload["product"]
        pid     = product["id"]

        if action == "add":
            if pid in self.cart:
                if self.cart[pid]["quantity"] >= product["stock"]:
                    self._toast("No more stock available.", error=True)
                    return
                self.cart[pid]["quantity"]   += 1
                self.cart[pid]["line_total"]  = (
                    self.cart[pid]["quantity"] * self.cart[pid]["unit_price"]
                )
            else:
                self.cart[pid] = {
                    "product_id": pid,
                    "name":       product["name"],
                    "unit_price": product["price"],
                    "quantity":   1,
                    "line_total": product["price"],
                    "stock":      product["stock"],
                    "unit":       product["unit"],
                }
        elif action == "remove":
            if pid in self.cart:
                self.cart[pid]["quantity"] -= 1
                if self.cart[pid]["quantity"] <= 0:
                    del self.cart[pid]
                else:
                    self.cart[pid]["line_total"] = (
                        self.cart[pid]["quantity"]
                        * self.cart[pid]["unit_price"]
                    )

        self._refresh_card(pid)
        self._refresh_cart_panel()

    def _remove_from_cart(self, pid: int):
        self.cart.pop(pid, None)
        # Re-render to update card
        self._render_grid()
        self._refresh_cart_panel()

    def _clear_cart(self):
        self.cart.clear()
        self._render_grid()
        self._refresh_cart_panel()

    def _refresh_cart_panel(self):
        # Clear cart items
        while self.cart_vbox.count():
            item = self.cart_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.cart:
            self.empty_cart.show()
            self.cart_scroll.hide()
            self._update_totals(0)
            self.charge_btn.setEnabled(False)
            self.fast_btn.setEnabled(False)
            self.charge_btn.setText(f"Place Order  ·  {CURRENCY} 0.00")
            self.count_pill.setText("0 items")
            return

        self.empty_cart.hide()
        self.cart_scroll.show()

        for item in self.cart.values():
            ci = CartItem(item)
            ci.remove_clicked.connect(self._remove_from_cart)
            self.cart_vbox.addWidget(ci)
            # Thin separator
            sep = self._rule()
            self.cart_vbox.addWidget(sep)

        self.cart_vbox.addStretch()

        total = sum(i["line_total"] for i in self.cart.values())
        count = int(sum(i["quantity"] for i in self.cart.values()))
        self._update_totals(total)
        self.charge_btn.setEnabled(True)
        self.fast_btn.setEnabled(True)
        self.charge_btn.setText(
            f"Place Order  ·  {CURRENCY} {total:,.2f}"
        )
        self.count_pill.setText(
            f"{count} item{'s' if count != 1 else ''}"
        )
        self.count_pill.setStyleSheet(f"""
            background: {Th.PRIMARY_LIGHT};
            color: {Th.PRIMARY};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)

    def _update_totals(self, total: float):
        self.subtotal_val.setText(f"{CURRENCY} {total:,.2f}")
        self.total_val.setText(f"{CURRENCY} {total:,.2f}")

    # ─── Checkout ─────────────────────────────────────────────────

    def _open_payment(self):
        total = sum(i["line_total"] for i in self.cart.values())
        dlg   = PaymentDialog(total, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._process_sale(
                payment_method  = dlg.selected_payment,
                payment_ref     = dlg.selected_ref,
                do_print        = dlg.do_print,
                tendered_amount = dlg.tendered_amount,
                change_amount   = dlg.change_amount,
            )

    def _fast_sale(self):
        total = sum(i["line_total"] for i in self.cart.values())
        self._process_sale("cash", None, False, total, 0)

    def _process_sale(self, payment_method, payment_ref,
                      do_print, tendered_amount, change_amount):
        try:
            from app.database import get_session
            from app.models.sale import Sale, SaleItem
            from app.models.product import Product
            from app.models.stock_movement import StockMovement
            from app.models.setting import Setting

            total         = sum(i["line_total"] for i in self.cart.values())
            cart_snapshot = list(self.cart.values())

            with get_session() as session:
                receipt_no = self._gen_receipt(session)
                sale = Sale(
                    receipt_number = receipt_no,
                    cashier_id     = self.user.id,
                    status         = "completed",
                    payment_method = payment_method,
                    payment_ref    = payment_ref,
                    subtotal       = total,
                    discount       = 0,
                    total          = total,
                    completed_at   = datetime.now(timezone.utc),
                )
                session.add(sale); session.flush()

                for item in cart_snapshot:
                    session.add(SaleItem(
                        sale_id      = sale.id,
                        product_id   = item["product_id"],
                        product_name = item["name"],
                        unit_price   = item["unit_price"],
                        quantity     = item["quantity"],
                        line_total   = item["line_total"],
                    ))
                    p = session.get(Product, item["product_id"])
                    if p:
                        before   = p.stock
                        p.stock -= item["quantity"]
                        session.add(StockMovement(
                            product_id      = p.id,
                            user_id         = self.user.id,
                            movement_type   = "sale",
                            quantity_change = -item["quantity"],
                            stock_before    = before,
                            stock_after     = p.stock,
                            reference_id    = sale.id,
                            reason          = f"Sale #{receipt_no}",
                        ))

                settings = {
                    s.key: s.value
                    for s in session.query(Setting).all()
                }

            sale_data = {
                "receipt_number": receipt_no,
                "date_str":       datetime.now().strftime("%d %b %Y  %H:%M"),
                "cashier_name":   self.user.full_name,
                "business_name":  settings.get("business_name", "My Business"),
                "receipt_footer": settings.get("receipt_footer","Thank you for your business!"),
                "items": [
                    {
                        "name":       i["name"],
                        "quantity":   i["quantity"],
                        "unit_price": i["unit_price"],
                        "line_total": i["line_total"],
                    }
                    for i in cart_snapshot
                ],
                "subtotal":       total,
                "discount":       0,
                "total":          total,
                "payment_method": payment_method,
                "payment_ref":    payment_ref,
                "tendered":       tendered_amount if payment_method == "cash" else None,
                "change":         change_amount   if payment_method == "cash" else None,
            }

            self._toast(f"Sale recorded  ·  {receipt_no}")
            self._clear_cart()
            self._load_products()

            if do_print:
                from app.views.receipt_preview import ReceiptPreview
                ReceiptPreview(sale_data, parent=self).exec()

        except Exception as e:
            logger.error("Sale error: %s", e)
            self._toast(f"Error: {e}", error=True)

    def _gen_receipt(self, session) -> str:
        from app.models.sale import Sale
        today = datetime.now().strftime("%Y%m%d")
        count = session.query(Sale).filter(
            Sale.receipt_number.like(f"RCP-{today}-%")
        ).count()
        return f"RCP-{today}-{count + 1:04d}"

    def _toast(self, msg: str, error=False):
        bg   = Th.DANGER if error else Th.PRIMARY
        icon = "✕" if error else "✓"
        t    = QLabel(f"  {icon}  {msg}", self)
        t.setStyleSheet(f"""
            background:{bg}; color:white; border-radius:10px;
            padding:12px 20px; font-size:13px; font-weight:600;
        """)
        t.adjustSize(); t.setFixedHeight(44)
        t.move((self.width() - t.width()) // 2, self.height() - 80)
        t.show(); t.raise_()
        QTimer.singleShot(2600, t.deleteLater)
