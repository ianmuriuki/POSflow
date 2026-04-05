"""
app/views/returns_view.py
--------------------------
Returns processing — search sale, select items, confirm return.
"""

import logging
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QDialog, QComboBox,
    QDoubleSpinBox, QGraphicsDropShadowEffect, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from app.config import CONFIG

logger   = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")

RETURN_REASONS = [
    "Wrong item delivered",
    "Damaged / defective product",
    "Customer changed mind",
    "Excess quantity dispatched",
    "Expired product",
    "Quality not as expected",
    "Other",
]


def card_shadow():
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(14)
    s.setOffset(0, 2)
    s.setColor(QColor(0, 0, 0, 14))
    return s


def solid_btn(text, bg="#1A3C6B", fg="white", hover="#2E75B6", h=44, fs=13):
    b = QPushButton(text)
    b.setFixedHeight(h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:none; border-radius:9px;
            font-size:{fs}px; font-weight:bold;
        }}
        QPushButton:hover {{ background:{hover}; }}
        QPushButton:disabled {{ background:#E5E7EB; color:#9CA3AF; }}
    """)
    return b


def field_style():
    return """
        QLineEdit {
            border:1.5px solid #E5E7EB; border-radius:9px;
            padding:0 14px; font-size:13px;
            background:white; color:#111827;
        }
        QLineEdit:focus { border-color:#1A3C6B; background:white; }
    """


# ── Return item row ───────────────────────────────────────────────

class ReturnItemRow(QFrame):
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border-bottom:1px solid #F3F4F6;
            }
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # Product info
        info = QVBoxLayout()
        info.setSpacing(3)
        name = QLabel(self.item["product_name"])
        name.setStyleSheet("font-size:13px; font-weight:bold; color:#111827; background:transparent;")
        meta = QLabel(
            f"{CURRENCY} {self.item['unit_price']:,.2f}  ·  "
            f"Sold: {self.item['quantity']:g}"
        )
        meta.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        info.addWidget(name)
        info.addWidget(meta)

        # Line total
        total = QLabel(f"{CURRENCY} {self.item['line_total']:,.2f}")
        total.setFixedWidth(100)
        total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total.setStyleSheet("font-size:13px; font-weight:bold; color:#1A3C6B; background:transparent;")

        # Return qty spinner
        qty_lbl = QLabel("Return qty")
        qty_lbl.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, self.item["quantity"])
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(0)
        self.qty_spin.setFixedSize(90, 34)
        self.qty_spin.setStyleSheet("""
            QDoubleSpinBox {
                border:1.5px solid #E5E7EB; border-radius:8px;
                padding:0 10px; font-size:13px;
                color:#111827; background:#FAFAFA;
            }
            QDoubleSpinBox:focus { border-color:#1A3C6B; background:white; }
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button { width:0; }
        """)

        qty_col = QVBoxLayout()
        qty_col.setSpacing(2)
        qty_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_col.addWidget(qty_lbl)
        qty_col.addWidget(self.qty_spin)

        layout.addLayout(info, 1)
        layout.addWidget(total)
        layout.addSpacing(16)
        layout.addLayout(qty_col)

    def return_qty(self) -> float:
        return self.qty_spin.value()

    def refund_amount(self) -> float:
        return self.qty_spin.value() * self.item["unit_price"]


# ── History row ───────────────────────────────────────────────────

class HistoryRow(QFrame):
    def __init__(self, ret: dict, parent=None):
        super().__init__(parent)
        self.ret = ret
        self.setFixedHeight(64)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border-bottom:1px solid #F3F4F6;
            }
            QFrame:hover { background:#FAFAFA; }
        """)
        self._build()

    def _build(self):
        r = self.ret
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Date + receipt
        date_col = QVBoxLayout()
        date_col.setSpacing(3)
        dt = QLabel(r["created_at"])
        dt.setStyleSheet("font-size:12px; color:#6B7280; background:transparent;")
        rcpt = QLabel(f"Sale #{r['receipt_number']}")
        rcpt.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        date_col.addWidget(dt)
        date_col.addWidget(rcpt)

        # Product
        prod = QLabel(r["product_name"])
        prod.setStyleSheet("font-size:13px; font-weight:bold; color:#111827; background:transparent;")

        # Qty
        qty = QLabel(f"−{r['quantity']:g} units")
        qty.setStyleSheet("font-size:12px; color:#DC2626; font-weight:bold; background:transparent;")
        qty.setFixedWidth(90)

        # Refund
        refund = QLabel(f"{CURRENCY} {r['refund_amount']:,.2f}")
        refund.setStyleSheet("font-size:13px; font-weight:bold; color:#1A3C6B; background:transparent;")
        refund.setFixedWidth(110)
        refund.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Reason
        reason = QLabel(r["reason"])
        reason.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        reason.setFixedWidth(180)

        layout.addLayout(date_col)
        layout.addWidget(prod, 1)
        layout.addWidget(qty)
        layout.addWidget(reason)
        layout.addWidget(refund)


# ── Main Returns View ─────────────────────────────────────────────

class ReturnsView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user         = user
        self.current_sale = None
        self.item_rows    = []
        self.setStyleSheet("background:#F8FAFC;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Tab bar
        tab_bar = QFrame()
        tab_bar.setFixedHeight(50)
        tab_bar.setStyleSheet("background:white; border-bottom:1px solid #E5E7EB;")
        tbl = QHBoxLayout(tab_bar)
        tbl.setContentsMargins(24, 0, 24, 0)
        tbl.setSpacing(0)

        self.t_new  = self._tab("Process Return")
        self.t_hist = self._tab("Return History")
        self.t_new.setChecked(True)
        self.t_new.clicked.connect(lambda: self._switch(0))
        self.t_hist.clicked.connect(lambda: self._switch(1))

        tbl.addWidget(self.t_new)
        tbl.addWidget(self.t_hist)
        tbl.addStretch()
        root.addWidget(tab_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.stack.addWidget(self._build_process_page())
        self.stack.addWidget(self._build_history_page())

    def _tab(self, text):
        b = QPushButton(text)
        b.setCheckable(True)
        b.setFixedHeight(50)
        b.setFixedWidth(160)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                background:transparent; color:#9CA3AF;
                border:none; border-bottom:2px solid transparent;
                font-size:13px; font-weight:600;
            }
            QPushButton:hover   { color:#374151; }
            QPushButton:checked {
                color:#1A3C6B;
                border-bottom:2px solid #1A3C6B;
            }
        """)
        return b

    def _switch(self, idx):
        self.t_new.setChecked(idx == 0)
        self.t_hist.setChecked(idx == 1)
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            self._load_history()

    # ── Process Return page ───────────────────────────────────────

    def _build_process_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background:#F8FAFC;")
        outer = QHBoxLayout(page)
        outer.setContentsMargins(24, 20, 24, 24)
        outer.setSpacing(20)

        # ── Left panel — search + sale info ──────────────────
        left = QVBoxLayout()
        left.setSpacing(16)

        # Search card
        search_card = QFrame()
        search_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        search_card.setGraphicsEffect(card_shadow())
        sc_layout = QVBoxLayout(search_card)
        sc_layout.setContentsMargins(20, 18, 20, 18)
        sc_layout.setSpacing(12)

        sc_title = QLabel("Find Sale")
        sc_title.setStyleSheet("font-size:14px; font-weight:bold; color:#111827;")
        sc_sub   = QLabel("Enter a receipt number to load the sale")
        sc_sub.setStyleSheet("font-size:12px; color:#9CA3AF;")

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.receipt_input = QLineEdit()
        self.receipt_input.setPlaceholderText("e.g. RCP-20260330-0001")
        self.receipt_input.setFixedHeight(42)
        self.receipt_input.setStyleSheet(field_style())
        self.receipt_input.returnPressed.connect(self._search_sale)

        self.search_btn = solid_btn("Search", h=42, fs=12)
        self.search_btn.setFixedWidth(90)
        self.search_btn.clicked.connect(self._search_sale)

        search_row.addWidget(self.receipt_input)
        search_row.addWidget(self.search_btn)

        self.search_err = QLabel("")
        self.search_err.setStyleSheet("""
            color:#DC2626; background:#FEF2F2;
            border:1px solid #FECACA; border-radius:8px;
            padding:8px 12px; font-size:12px;
        """)
        self.search_err.hide()

        sc_layout.addWidget(sc_title)
        sc_layout.addWidget(sc_sub)
        sc_layout.addLayout(search_row)
        sc_layout.addWidget(self.search_err)
        left.addWidget(search_card)

        # Sale info card (hidden until found)
        self.sale_card = QFrame()
        self.sale_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        self.sale_card.setGraphicsEffect(card_shadow())
        self.sale_card_layout = QVBoxLayout(self.sale_card)
        self.sale_card_layout.setContentsMargins(20, 16, 20, 16)
        self.sale_card_layout.setSpacing(10)
        self.sale_card.hide()
        left.addWidget(self.sale_card)

        left.addStretch()
        outer.addLayout(left, 2)

        # ── Right panel — items + confirm ─────────────────────
        right = QVBoxLayout()
        right.setSpacing(16)

        # Items card
        self.items_card = QFrame()
        self.items_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        self.items_card.setGraphicsEffect(card_shadow())
        self.items_layout = QVBoxLayout(self.items_card)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(0)

        items_header = QFrame()
        items_header.setFixedHeight(44)
        items_header.setStyleSheet("""
            background:#FAFAFA;
            border-radius:12px 12px 0 0;
            border-bottom:1px solid #F3F4F6;
        """)
        ihl = QHBoxLayout(items_header)
        ihl.setContentsMargins(20, 0, 20, 0)
        ih_title = QLabel("Sale Items")
        ih_title.setStyleSheet("font-size:13px; font-weight:bold; color:#374151; background:transparent;")
        ih_hint  = QLabel("Set return quantity for each item")
        ih_hint.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        ihl.addWidget(ih_title)
        ihl.addStretch()
        ihl.addWidget(ih_hint)
        self.items_layout.addWidget(items_header)

        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.items_scroll.setFixedHeight(240)
        self.items_scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollBar:vertical { width:4px; background:transparent; }
            QScrollBar::handle:vertical { background:#E5E7EB; border-radius:2px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height:0; }
        """)
        self.items_inner = QWidget()
        self.items_inner.setStyleSheet("background:transparent;")
        self.items_vbox  = QVBoxLayout(self.items_inner)
        self.items_vbox.setContentsMargins(0, 0, 0, 0)
        self.items_vbox.setSpacing(0)

        empty_items = QLabel("Search for a sale to see its items")
        empty_items.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_items.setStyleSheet("font-size:13px; color:#D1D5DB; background:transparent;")
        self.items_vbox.addStretch()
        self.items_vbox.addWidget(empty_items)
        self.items_vbox.addStretch()

        self.items_scroll.setWidget(self.items_inner)
        self.items_layout.addWidget(self.items_scroll)
        right.addWidget(self.items_card)

        # Reason + confirm card
        confirm_card = QFrame()
        confirm_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        confirm_card.setGraphicsEffect(card_shadow())
        cc_layout = QVBoxLayout(confirm_card)
        cc_layout.setContentsMargins(20, 18, 20, 18)
        cc_layout.setSpacing(12)

        rsn_lbl = QLabel("Return Reason")
        rsn_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(RETURN_REASONS)
        self.reason_combo.setFixedHeight(42)
        self.reason_combo.setStyleSheet("""
            QComboBox {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 14px; font-size:13px;
                background:#FAFAFA; color:#111827;
            }
            QComboBox:focus { border-color:#1A3C6B; background:white; }
            QComboBox::drop-down { border:none; width:28px; }
            QComboBox QAbstractItemView {
                border:1px solid #E5E7EB;
                selection-background-color:#EFF6FF;
                selection-color:#1A3C6B; font-size:13px;
            }
        """)

        # Refund summary
        self.refund_lbl = QLabel(f"Refund total:  {CURRENCY} 0.00")
        self.refund_lbl.setStyleSheet("""
            font-size:15px; font-weight:bold; color:#1A3C6B;
            background:#EFF6FF; border-radius:8px;
            padding:10px 16px;
        """)

        self.confirm_btn = solid_btn("Confirm Return", h=48, fs=14)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._confirm_return)

        cc_layout.addWidget(rsn_lbl)
        cc_layout.addWidget(self.reason_combo)
        cc_layout.addWidget(self.refund_lbl)
        cc_layout.addWidget(self.confirm_btn)
        right.addWidget(confirm_card)

        right.addStretch()
        outer.addLayout(right, 3)

        return page

    # ── History page ──────────────────────────────────────────────

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background:#F8FAFC;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # Toolbar
        bar = QHBoxLayout()
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search by product or receipt...")
        self.hist_search.setFixedHeight(40)
        self.hist_search.setMaximumWidth(300)
        self.hist_search.setStyleSheet(field_style())
        self.hist_search.textChanged.connect(self._filter_history)
        bar.addWidget(self.hist_search)
        bar.addStretch()
        layout.addLayout(bar)

        # Table card
        table_card = QFrame()
        table_card.setStyleSheet("""
            QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
        """)
        table_card.setGraphicsEffect(card_shadow())
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        # Column header
        col_hdr = QFrame()
        col_hdr.setFixedHeight(40)
        col_hdr.setStyleSheet("""
            background:#FAFAFA;
            border-radius:12px 12px 0 0;
            border-bottom:1px solid #F3F4F6;
        """)
        chl = QHBoxLayout(col_hdr)
        chl.setContentsMargins(20, 0, 20, 0)
        chl.setSpacing(0)
        for txt, w in [
            ("Date", 160), ("Product", 0), ("Qty", 90),
            ("Reason", 180), ("Refund", 110)
        ]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size:11px; font-weight:bold; color:#9CA3AF; background:transparent; letter-spacing:0.5px;")
            if w:
                lbl.setFixedWidth(w)
            else:
                chl.addWidget(lbl, 1)
                continue
            chl.addWidget(lbl)
        tc_layout.addWidget(col_hdr)

        self.hist_scroll = QScrollArea()
        self.hist_scroll.setWidgetResizable(True)
        self.hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.hist_scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollBar:vertical { width:4px; background:transparent; }
            QScrollBar::handle:vertical { background:#E5E7EB; border-radius:2px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height:0; }
        """)
        self.hist_inner  = QWidget()
        self.hist_inner.setStyleSheet("background:transparent;")
        self.hist_vbox   = QVBoxLayout(self.hist_inner)
        self.hist_vbox.setContentsMargins(0, 0, 0, 0)
        self.hist_vbox.setSpacing(0)
        self.hist_vbox.addStretch()
        self.hist_scroll.setWidget(self.hist_inner)
        tc_layout.addWidget(self.hist_scroll)
        layout.addWidget(table_card)

        self.hist_count = QLabel("")
        self.hist_count.setStyleSheet("font-size:11px; color:#9CA3AF;")
        layout.addWidget(self.hist_count)

        self.all_history = []
        return page

    # ── Logic ─────────────────────────────────────────────────────

    def _search_sale(self):
        receipt = self.receipt_input.text().strip().upper()
        if not receipt:
            return
        self.search_err.hide()

        try:
            from app.database import get_session
            from app.models.sale import Sale, SaleItem
            with get_session() as session:
                sale = session.query(Sale).filter_by(receipt_number=receipt).first()
                if not sale:
                    self.search_err.setText(f"No sale found with receipt number '{receipt}'.")
                    self.search_err.show()
                    self._clear_sale()
                    return

                self.current_sale = {
                    "id":             sale.id,
                    "receipt_number": sale.receipt_number,
                    "total":          sale.total,
                    "payment_method": sale.payment_method,
                    "created_at":     sale.created_at.strftime("%d %b %Y  %H:%M"),
                    "cashier_id":     sale.cashier_id,
                }
                self.current_items = [
                    {
                        "id":           it.id,
                        "product_id":   it.product_id,
                        "product_name": it.product_name,
                        "unit_price":   it.unit_price,
                        "quantity":     it.quantity,
                        "line_total":   it.line_total,
                    }
                    for it in sale.items
                ]

            self._populate_sale_card()
            self._populate_items()

        except Exception as e:
            logger.error("Sale search error: %s", e)
            self.search_err.setText("An error occurred while searching.")
            self.search_err.show()

    def _clear_sale(self):
        self.current_sale  = None
        self.current_items = []
        self.sale_card.hide()
        while self.items_vbox.count():
            it = self.items_vbox.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.item_rows = []
        self.confirm_btn.setEnabled(False)

    def _populate_sale_card(self):
        # Clear old content
        while self.sale_card_layout.count():
            it = self.sale_card_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        s = self.current_sale

        title = QLabel(f"Receipt  {s['receipt_number']}")
        title.setStyleSheet("font-size:14px; font-weight:bold; color:#111827;")

        rows = QFrame()
        rows.setStyleSheet("background:#F8FAFC; border-radius:8px;")
        rl = QVBoxLayout(rows)
        rl.setContentsMargins(14, 10, 14, 10)
        rl.setSpacing(6)

        for label, val in [
            ("Date",           s["created_at"]),
            ("Total",          f"{CURRENCY} {s['total']:,.2f}"),
            ("Payment",        s["payment_method"].title()),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:12px; color:#9CA3AF;")
            v   = QLabel(val)
            v.setStyleSheet("font-size:12px; font-weight:bold; color:#111827;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(v)
            rl.addLayout(row)

        self.sale_card_layout.addWidget(title)
        self.sale_card_layout.addWidget(rows)
        self.sale_card.show()

    def _populate_items(self):
        while self.items_vbox.count():
            it = self.items_vbox.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        self.item_rows = []
        for item in self.current_items:
            row = ReturnItemRow(item)
            row.qty_spin.valueChanged.connect(self._update_refund)
            self.item_rows.append(row)
            self.items_vbox.addWidget(row)
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background:#F3F4F6;")
            self.items_vbox.addWidget(div)

        self.items_vbox.addStretch()
        self._update_refund()

    def _update_refund(self):
        total = sum(r.refund_amount() for r in self.item_rows)
        self.refund_lbl.setText(f"Refund total:  {CURRENCY} {total:,.2f}")
        self.confirm_btn.setEnabled(
            total > 0 and self.current_sale is not None
        )

    def _confirm_return(self):
        reason = self.reason_combo.currentText()
        items_to_return = [
            (row.item, row.return_qty())
            for row in self.item_rows
            if row.return_qty() > 0
        ]

        if not items_to_return:
            return

        try:
            from app.database import get_session
            from app.models.return_transaction import ReturnTransaction
            from app.models.product import Product
            from app.models.stock_movement import StockMovement

            with get_session() as session:
                for item, qty in items_to_return:
                    refund = qty * item["unit_price"]

                    session.add(ReturnTransaction(
                        original_sale_id=self.current_sale["id"],
                        processed_by=self.user.id,
                        product_id=item["product_id"],
                        quantity=qty,
                        reason=reason,
                        refund_amount=refund,
                    ))

                    # Restore stock
                    p = session.get(Product, item["product_id"])
                    if p:
                        before   = p.stock
                        p.stock += qty
                        session.add(StockMovement(
                            product_id=p.id,
                            user_id=self.user.id,
                            movement_type="return",
                            quantity_change=qty,
                            stock_before=before,
                            stock_after=p.stock,
                            reference_id=self.current_sale["id"],
                            reason=f"Return — {reason}",
                        ))

            total_refund = sum(r * i["unit_price"] for i, r in items_to_return)
            self._toast(
                f"Return processed  ·  {CURRENCY} {total_refund:,.2f} refund  ·  Stock restored"
            )
            self.receipt_input.clear()
            self._clear_sale()

        except Exception as e:
            logger.error("Return error: %s", e)
            self._toast(f"Error: {e}", error=True)

    def _load_history(self):
        try:
            from app.database import get_session
            from app.models.return_transaction import ReturnTransaction
            from app.models.sale import Sale
            with get_session() as session:
                rows = (
                    session.query(ReturnTransaction, Sale.receipt_number)
                    .join(Sale, ReturnTransaction.original_sale_id == Sale.id)
                    .order_by(ReturnTransaction.created_at.desc())
                    .all()
                )
                self.all_history = [
                    {
                        "created_at":     r.ReturnTransaction.created_at.strftime("%d %b %Y  %H:%M"),
                        "receipt_number": r.receipt_number,
                        "product_name":   r.ReturnTransaction.product_id,
                        "quantity":       r.ReturnTransaction.quantity,
                        "reason":         r.ReturnTransaction.reason,
                        "refund_amount":  r.ReturnTransaction.refund_amount,
                        "product_id":     r.ReturnTransaction.product_id,
                    }
                    for r in rows
                ]
                # Load product names separately
                from app.models.product import Product
                prod_names = {
                    p.id: p.name
                    for p in session.query(Product).all()
                }
                for h in self.all_history:
                    h["product_name"] = prod_names.get(h["product_id"], "Unknown")

            self._filter_history()
        except Exception as e:
            logger.error("History load error: %s", e)

    def _filter_history(self):
        q   = self.hist_search.text().strip().lower()
        out = [
            r for r in self.all_history
            if not q or q in r["product_name"].lower()
            or q in r["receipt_number"].lower()
        ]
        self._render_history(out)

    def _render_history(self, rows):
        while self.hist_vbox.count():
            it = self.hist_vbox.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        if not rows:
            empty = QLabel("No return records found.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("font-size:14px; color:#D1D5DB; background:transparent;")
            self.hist_vbox.addStretch()
            self.hist_vbox.addWidget(empty)
            self.hist_vbox.addStretch()
            self.hist_count.setText("0 records")
            return

        for r in rows:
            self.hist_vbox.addWidget(HistoryRow(r))
        self.hist_vbox.addStretch()
        self.hist_count.setText(f"{len(rows)} records")

    def _toast(self, msg: str, error=False):
        bg    = "#DC2626" if error else "#059669"
        icon  = "✕" if error else "✓"
        toast = QLabel(f"  {icon}  {msg}", self)
        toast.setStyleSheet(f"""
            background:{bg}; color:white;
            border-radius:10px; padding:12px 20px;
            font-size:13px; font-weight:bold;
        """)
        toast.adjustSize()
        toast.setFixedHeight(44)
        toast.move((self.width() - toast.width()) // 2, self.height() - 80)
        toast.show()
        toast.raise_()
        QTimer.singleShot(2800, toast.deleteLater)
