"""
app/views/stock_view.py
------------------------
Stock management — clean redesign.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QDialog, QComboBox,
    QDoubleSpinBox, QGraphicsDropShadowEffect, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from app.config import CONFIG

logger = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")

ADJUSTMENT_REASONS = [
    "New stock received",
    "Damaged / expired goods",
    "Stock count correction",
    "Goods returned to supplier",
    "Internal use / consumption",
    "Other",
]


def card_shadow():
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(12)
    s.setOffset(0, 1)
    s.setColor(QColor(0, 0, 0, 12))
    return s


def pill(text, fg, bg) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"""
        color:{fg}; background:{bg};
        border-radius:5px; padding:3px 10px;
        font-size:11px; font-weight:bold;
    """)
    l.setFixedHeight(22)
    return l


def action_btn(text, bg, fg, hover, w=90, h=36) -> QPushButton:
    b = QPushButton(text)
    b.setFixedSize(w, h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:none; border-radius:8px;
            font-size:12px; font-weight:bold;
        }}
        QPushButton:hover {{ background:{hover}; }}
    """)
    return b


def divider_line() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet("background:#F3F4F6; border:none;")
    return f


# ── Stock Row (list style, much cleaner than cards) ──────────────

class StockRow(QFrame):
    def __init__(self, product: dict, on_adjust, parent=None):
        super().__init__(parent)
        self.product   = product
        self.on_adjust = on_adjust
        self.setFixedHeight(68)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border-bottom:1px solid #F3F4F6;
            }
            QFrame:hover { background:#FAFAFA; }
        """)
        self._build()

    def _build(self):
        p   = self.product
        out = p["stock"] <= 0
        low = not out and p["stock"] <= p["low_stock_threshold"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 20, 0)
        layout.setSpacing(0)

        # Name + category
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)
        name = QLabel(p["name"])
        name.setStyleSheet("font-size:13px; font-weight:bold; color:#111827; background:transparent;")
        cat  = QLabel(f"{p['category']}  ·  {p['unit']}")
        cat.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")
        info.addWidget(name)
        info.addWidget(cat)

        # Stock number
        stock_color = "#DC2626" if out else ("#D97706" if low else "#059669")
        stock_val = QLabel(f"{p['stock']:g}")
        stock_val.setFixedWidth(70)
        stock_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        stock_val.setStyleSheet(f"font-size:20px; font-weight:bold; color:{stock_color}; background:transparent;")

        unit_lbl = QLabel(p["unit"])
        unit_lbl.setFixedWidth(44)
        unit_lbl.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent; margin-left:4px;")

        # Status badge
        if out:
            badge = pill("Out of Stock", "#DC2626", "#FEF2F2")
        elif low:
            badge = pill("Low Stock",    "#D97706", "#FFFBEB")
        else:
            badge = pill("In Stock",     "#059669", "#ECFDF5")
        badge.setFixedWidth(88)

        # Adjust button
        adj = action_btn("Adjust", "#1A3C6B", "white", "#2E75B6", w=82, h=34)
        adj.clicked.connect(lambda: self.on_adjust(self.product))

        layout.addLayout(info, 1)
        layout.addSpacing(16)
        layout.addWidget(stock_val)
        layout.addWidget(unit_lbl)
        layout.addSpacing(20)
        layout.addWidget(badge)
        layout.addSpacing(16)
        layout.addWidget(adj)


# ── Adjustment Dialog — clean, no overlap ───────────────────────

class AdjustDialog(QDialog):
    def __init__(self, product: dict, user, parent=None):
        super().__init__(parent)
        self.product   = product
        self.user      = user
        self.direction = "add"
        self.setWindowTitle("Stock Adjustment")
        self.setFixedWidth(420)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        # Outer wrapper for rounded shadow card
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background:white;
                border-radius:16px;
                border:1px solid #E5E7EB;
            }
        """)
        card.setGraphicsEffect(card_shadow())
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ── Header ───────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("Adjust Stock")
        title.setStyleSheet("font-size:17px; font-weight:bold; color:#111827;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background:#F3F4F6; color:#6B7280;
                border:none; border-radius:7px; font-size:12px;
            }
            QPushButton:hover { background:#E5E7EB; color:#374151; }
        """)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        layout.addLayout(hdr)

        # Product name
        pname = QLabel(self.product["name"])
        pname.setStyleSheet("font-size:12px; color:#6B7280; margin-top:-8px;")
        layout.addWidget(pname)

        # ── Current stock chip ───────────────────────────────
        chip = QFrame()
        chip.setFixedHeight(54)
        chip.setStyleSheet("background:#F8FAFC; border-radius:10px; border:1px solid #E5E7EB;")
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(18, 0, 18, 0)
        clbl = QLabel("Current stock")
        clbl.setStyleSheet("font-size:12px; color:#6B7280; background:transparent;")
        cval = QLabel(f"{self.product['stock']:g}  {self.product['unit']}")
        cval.setStyleSheet("font-size:16px; font-weight:bold; color:#1A3C6B; background:transparent;")
        chip_layout.addWidget(clbl)
        chip_layout.addStretch()
        chip_layout.addWidget(cval)
        layout.addWidget(chip)

        # ── Direction toggle ─────────────────────────────────
        dir_lbl = QLabel("Adjustment type")
        dir_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
        layout.addWidget(dir_lbl)

        toggle = QFrame()
        toggle.setFixedHeight(44)
        toggle.setStyleSheet("background:#F3F4F6; border-radius:10px;")
        tl = QHBoxLayout(toggle)
        tl.setContentsMargins(4, 4, 4, 4)
        tl.setSpacing(4)

        self.add_btn = QPushButton("+ Add Stock")
        self.rem_btn = QPushButton("− Remove Stock")
        for b in (self.add_btn, self.rem_btn):
            b.setCheckable(True)
            b.setFixedHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setChecked(True)
        self._restyle_toggle()

        self.add_btn.clicked.connect(lambda: self._set_dir("add"))
        self.rem_btn.clicked.connect(lambda: self._set_dir("remove"))

        tl.addWidget(self.add_btn)
        tl.addWidget(self.rem_btn)
        layout.addWidget(toggle)

        # ── Quantity ─────────────────────────────────────────
        qty_lbl = QLabel("Quantity")
        qty_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.01, 99999)
        self.qty_input.setDecimals(2)
        self.qty_input.setValue(1)
        self.qty_input.setFixedHeight(46)
        self.qty_input.setStyleSheet("""
            QDoubleSpinBox {
                border:1.5px solid #E5E7EB; border-radius:10px;
                padding:0 14px; font-size:15px;
                color:#111827; background:#FAFAFA;
            }
            QDoubleSpinBox:focus {
                border-color:#1A3C6B; background:white;
            }
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button { width:0; }
        """)
        layout.addWidget(qty_lbl)
        layout.addWidget(self.qty_input)

        # ── Reason ───────────────────────────────────────────
        rsn_lbl = QLabel("Reason")
        rsn_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(ADJUSTMENT_REASONS)
        self.reason_combo.setFixedHeight(46)
        self.reason_combo.setStyleSheet("""
            QComboBox {
                border:1.5px solid #E5E7EB; border-radius:10px;
                padding:0 14px; font-size:13px;
                color:#111827; background:#FAFAFA;
            }
            QComboBox:focus { border-color:#1A3C6B; background:white; }
            QComboBox::drop-down { border:none; width:28px; }
            QComboBox QAbstractItemView {
                border:1px solid #E5E7EB; border-radius:8px;
                selection-background-color:#EFF6FF;
                selection-color:#1A3C6B; font-size:13px;
                padding:4px;
            }
        """)
        layout.addWidget(rsn_lbl)
        layout.addWidget(self.reason_combo)

        # ── Confirm button ───────────────────────────────────
        layout.addSpacing(4)
        self.confirm_btn = QPushButton("Confirm Adjustment")
        self.confirm_btn.setFixedHeight(48)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background:#1A3C6B; color:white;
                border:none; border-radius:10px;
                font-size:14px; font-weight:bold;
            }
            QPushButton:hover { background:#2E75B6; }
        """)
        self.confirm_btn.clicked.connect(self._confirm)
        layout.addWidget(self.confirm_btn)

    def _set_dir(self, d: str):
        self.direction = d
        self.add_btn.setChecked(d == "add")
        self.rem_btn.setChecked(d == "remove")
        self._restyle_toggle()

    def _restyle_toggle(self):
        active   = "background:white; border-radius:8px; border:none; font-size:13px; font-weight:bold;"
        inactive = "background:transparent; border:none; font-size:13px; color:#6B7280; font-weight:500;"
        self.add_btn.setStyleSheet(
            f"QPushButton {{ {active} color:#059669; }}"
            if self.add_btn.isChecked() else
            f"QPushButton {{ {inactive} }} QPushButton:hover {{ color:#374151; }}"
        )
        self.rem_btn.setStyleSheet(
            f"QPushButton {{ {active} color:#DC2626; }}"
            if self.rem_btn.isChecked() else
            f"QPushButton {{ {inactive} }} QPushButton:hover {{ color:#374151; }}"
        )

    def _confirm(self):
        self.result_qty       = self.qty_input.value()
        self.result_direction = self.direction
        self.result_reason    = self.reason_combo.currentText()
        self.accept()


# ── Movement Log ─────────────────────────────────────────────────

class MovementLog(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user     = user
        self.all_rows = []
        self.setStyleSheet("background:#F8FAFC;")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # Toolbar
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by product...")
        self.search.setFixedHeight(40)
        self.search.setMaximumWidth(260)
        self.search.setStyleSheet("""
            QLineEdit {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 14px; font-size:13px;
                background:white; color:#111827;
            }
            QLineEdit:focus { border-color:#1A3C6B; }
        """)
        self.search.textChanged.connect(self._filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types", "sale", "return",
            "adjustment_add", "adjustment_remove", "opening_stock"
        ])
        self.type_filter.setFixedHeight(40)
        self.type_filter.setFixedWidth(170)
        self.type_filter.setStyleSheet("""
            QComboBox {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 12px; font-size:13px;
                background:white; color:#111827;
            }
            QComboBox:focus { border-color:#1A3C6B; }
            QComboBox::drop-down { border:none; width:26px; }
            QComboBox QAbstractItemView {
                border:1px solid #E5E7EB;
                selection-background-color:#EFF6FF;
                selection-color:#1A3C6B;
            }
        """)
        self.type_filter.currentTextChanged.connect(self._filter)

        bar.addWidget(self.search)
        bar.addWidget(self.type_filter)
        bar.addStretch()
        layout.addLayout(bar)

        # Table container card
        table_card = QFrame()
        table_card.setStyleSheet("""
            QFrame {
                background:white;
                border-radius:12px;
                border:1px solid #E5E7EB;
            }
        """)
        table_card.setGraphicsEffect(card_shadow())
        card_layout = QVBoxLayout(table_card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date & Time", "Product", "Type",
            "Change", "Before", "After", "By"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setStyleSheet("""
            QTableWidget {
                background:white;
                border:none;
                font-size:12px;
            }
            QTableWidget::item {
                padding:0 14px;
                color:#374151;
                border-bottom:1px solid #F9FAFB;
            }
            QTableWidget::item:selected {
                background:#EFF6FF;
                color:#1A3C6B;
            }
            QHeaderView::section {
                background:white;
                color:#9CA3AF;
                font-size:11px;
                font-weight:bold;
                letter-spacing:0.5px;
                padding:12px 14px;
                border:none;
                border-bottom:1px solid #E5E7EB;
            }
            QScrollBar:vertical {
                width:5px; background:transparent;
            }
            QScrollBar::handle:vertical {
                background:#E5E7EB; border-radius:3px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height:0; }
        """)
        card_layout.addWidget(self.table)
        layout.addWidget(table_card)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-size:11px; color:#9CA3AF;")
        layout.addWidget(self.count_lbl)

    def showEvent(self, event):
        super().showEvent(event)
        self._load()

    def _load(self):
        try:
            from app.database import get_session
            from app.models.stock_movement import StockMovement
            from app.models.product import Product
            from app.models.user import User as UserModel
            with get_session() as session:
                rows = (
                    session.query(StockMovement, Product.name, UserModel.username)
                    .join(Product,    StockMovement.product_id == Product.id)
                    .join(UserModel,  StockMovement.user_id    == UserModel.id)
                    .order_by(StockMovement.created_at.desc())
                    .limit(500)
                    .all()
                )
                self.all_rows = [
                    {
                        "dt":      r.StockMovement.created_at.strftime("%d %b %Y  %H:%M"),
                        "product": r.name,
                        "type":    r.StockMovement.movement_type,
                        "change":  r.StockMovement.quantity_change,
                        "before":  r.StockMovement.stock_before,
                        "after":   r.StockMovement.stock_after,
                        "by":      r.username,
                    }
                    for r in rows
                ]
            self._filter()
        except Exception as e:
            logger.error("Movement log load error: %s", e)

    def _filter(self):
        q    = self.search.text().strip().lower()
        tsel = self.type_filter.currentText()
        out  = [r for r in self.all_rows
                if (not q or q in r["product"].lower())
                and (tsel == "All Types" or r["type"] == tsel)]
        self._render(out)

    def _render(self, rows):
        TYPE_META = {
            "sale":               ("Sale",         "#1A3C6B", "#EFF6FF"),
            "return":             ("Return",        "#059669", "#ECFDF5"),
            "adjustment_add":     ("Stock In",      "#059669", "#ECFDF5"),
            "adjustment_remove":  ("Stock Out",     "#DC2626", "#FEF2F2"),
            "opening_stock":      ("Opening",       "#6B7280", "#F3F4F6"),
            "dispatch":           ("Dispatch",      "#D97706", "#FFFBEB"),
        }
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setRowHeight(i, 46)
            lbl, fg, bg = TYPE_META.get(r["type"], (r["type"], "#374151", "white"))

            for j, (val, color) in enumerate([
                (r["dt"],             "#6B7280"),
                (r["product"],        "#111827"),
                (None,                None),
                (None,                None),
                (f"{r['before']:g}",  "#374151"),
                (f"{r['after']:g}",   "#374151"),
                (r["by"],             "#6B7280"),
            ]):
                if val is None:
                    continue
                it = QTableWidgetItem(val)
                it.setForeground(QColor(color))
                self.table.setItem(i, j, it)

            # Type badge
            ti = QTableWidgetItem(f"  {lbl}  ")
            ti.setForeground(QColor(fg))
            ti.setBackground(QColor(bg))
            ti.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.table.setItem(i, 2, ti)

            # Change
            sign = "+" if r["change"] >= 0 else ""
            ci   = QTableWidgetItem(f"{sign}{r['change']:g}")
            ci.setForeground(QColor("#059669" if r["change"] >= 0 else "#DC2626"))
            ci.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.table.setItem(i, 3, ci)

        self.count_lbl.setText(f"{len(rows)} records")


# ── Main Stock View ──────────────────────────────────────────────

class StockView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user     = user
        self.products = []
        self.setStyleSheet("background:#F8FAFC;")
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Tab bar ───────────────────────────────────────────
        tab_bar = QFrame()
        tab_bar.setFixedHeight(50)
        tab_bar.setStyleSheet("""
            QFrame {
                background:white;
                border-bottom:1px solid #E5E7EB;
            }
        """)
        tbl = QHBoxLayout(tab_bar)
        tbl.setContentsMargins(24, 0, 24, 0)
        tbl.setSpacing(0)

        self.t_levels = self._mk_tab("Stock Levels")
        self.t_log    = self._mk_tab("Movement Log")
        self.t_levels.setChecked(True)
        self.t_levels.clicked.connect(lambda: self._switch(0))
        self.t_log.clicked.connect(lambda: self._switch(1))

        self.stat_lbl = QLabel("")
        self.stat_lbl.setStyleSheet("font-size:12px; color:#9CA3AF;")

        tbl.addWidget(self.t_levels)
        tbl.addWidget(self.t_log)
        tbl.addStretch()
        tbl.addWidget(self.stat_lbl)
        root.addWidget(tab_bar)

        # ── Stack ─────────────────────────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.stack.addWidget(self._build_levels_page())
        self.log_widget = MovementLog(self.user)
        self.stack.addWidget(self.log_widget)

    def _mk_tab(self, text) -> QPushButton:
        b = QPushButton(text)
        b.setCheckable(True)
        b.setFixedHeight(50)
        b.setFixedWidth(148)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                background:transparent; color:#9CA3AF;
                border:none; border-bottom:2px solid transparent;
                font-size:13px; font-weight:600;
            }
            QPushButton:hover { color:#374151; }
            QPushButton:checked {
                color:#1A3C6B;
                border-bottom:2px solid #1A3C6B;
            }
        """)
        return b

    def _switch(self, idx: int):
        self.t_levels.setChecked(idx == 0)
        self.t_log.setChecked(idx == 1)
        self.stack.setCurrentIndex(idx)

    def _build_levels_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background:#F8FAFC;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(14)

        # Toolbar
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search product...")
        self.search.setFixedHeight(40)
        self.search.setMaximumWidth(280)
        self.search.setStyleSheet("""
            QLineEdit {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 14px; font-size:13px;
                background:white; color:#111827;
            }
            QLineEdit:focus { border-color:#1A3C6B; }
        """)
        self.search.textChanged.connect(self._filter)

        self.lv_filter = QComboBox()
        self.lv_filter.addItems(["All", "Low Stock", "Out of Stock", "In Stock"])
        self.lv_filter.setFixedHeight(40)
        self.lv_filter.setFixedWidth(146)
        self.lv_filter.setStyleSheet("""
            QComboBox {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 12px; font-size:13px;
                background:white; color:#111827;
            }
            QComboBox:focus { border-color:#1A3C6B; }
            QComboBox::drop-down { border:none; width:26px; }
            QComboBox QAbstractItemView {
                border:1px solid #E5E7EB;
                selection-background-color:#EFF6FF;
                selection-color:#1A3C6B;
            }
        """)
        self.lv_filter.currentTextChanged.connect(self._filter)

        bar.addWidget(self.search)
        bar.addWidget(self.lv_filter)
        bar.addStretch()
        layout.addLayout(bar)

        # List card
        list_card = QFrame()
        list_card.setStyleSheet("""
            QFrame {
                background:white;
                border-radius:12px;
                border:1px solid #E5E7EB;
            }
        """)
        list_card.setGraphicsEffect(card_shadow())
        card_layout = QVBoxLayout(list_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Column headers
        col_header = QFrame()
        col_header.setFixedHeight(38)
        col_header.setStyleSheet("background:#FAFAFA; border-radius:12px 12px 0 0; border-bottom:1px solid #F3F4F6;")
        chl = QHBoxLayout(col_header)
        chl.setContentsMargins(24, 0, 20, 0)
        for txt, stretch in [("Product", 1), ("", 0), ("Stock", 0), ("", 0), ("Status", 0), ("", 0)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size:11px; font-weight:bold; color:#9CA3AF; background:transparent; letter-spacing:0.5px;")
            if stretch:
                chl.addWidget(lbl, stretch)
            else:
                chl.addWidget(lbl)
                chl.addSpacing(16 if txt else 8)
        card_layout.addWidget(col_header)

        # Scroll area for rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollBar:vertical { width:4px; background:transparent; }
            QScrollBar::handle:vertical { background:#E5E7EB; border-radius:2px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height:0; }
        """)
        self.rows_widget = QWidget()
        self.rows_widget.setStyleSheet("background:transparent;")
        self.rows_vbox = QVBoxLayout(self.rows_widget)
        self.rows_vbox.setContentsMargins(0, 0, 0, 0)
        self.rows_vbox.setSpacing(0)
        self.rows_vbox.addStretch()
        scroll.setWidget(self.rows_widget)
        card_layout.addWidget(scroll)

        layout.addWidget(list_card)

        # Empty state
        self.empty_lbl = QLabel("No products match your filter.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("font-size:14px; color:#9CA3AF;")
        self.empty_lbl.hide()
        layout.addWidget(self.empty_lbl)

        return page

    def _load_products(self):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                self.products = [
                    {
                        "id":                  p.id,
                        "name":                p.name,
                        "category":            p.category,
                        "unit":                p.unit,
                        "stock":               p.stock,
                        "low_stock_threshold": p.low_stock_threshold,
                    }
                    for p in session.query(Product)
                    .filter_by(is_active=True)
                    .order_by(Product.name).all()
                ]
            total = len(self.products)
            low   = sum(1 for p in self.products if 0 < p["stock"] <= p["low_stock_threshold"])
            out   = sum(1 for p in self.products if p["stock"] <= 0)
            self.stat_lbl.setText(
                f"{total} products  ·  {low} low  ·  {out} out of stock"
            )
            self._filter()
        except Exception as e:
            logger.error("Stock load error: %s", e)

    def _filter(self):
        q   = self.search.text().strip().lower() if hasattr(self, 'search') else ""
        lv  = self.lv_filter.currentText() if hasattr(self, 'lv_filter') else "All"
        out = []
        for p in self.products:
            if q and q not in p["name"].lower():
                continue
            if lv == "Low Stock"    and not (0 < p["stock"] <= p["low_stock_threshold"]):
                continue
            if lv == "Out of Stock" and p["stock"] > 0:
                continue
            if lv == "In Stock"     and p["stock"] <= 0:
                continue
            out.append(p)
        self._render_rows(out)

    def _render_rows(self, products):
        while self.rows_vbox.count():
            item = self.rows_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not products:
            self.empty_lbl.show()
            self.rows_vbox.addStretch()
            return

        self.empty_lbl.hide()
        for p in products:
            row = StockRow(p, on_adjust=self._open_adjust)
            self.rows_vbox.addWidget(row)
            self.rows_vbox.addWidget(divider_line())
        self.rows_vbox.addStretch()

    def _open_adjust(self, product: dict):
        dlg = AdjustDialog(product, self.user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._apply(product, dlg.result_direction,
                        dlg.result_qty, dlg.result_reason)

    def _apply(self, product, direction, qty, reason):
        try:
            from app.database import get_session
            from app.models.product import Product
            from app.models.stock_movement import StockMovement

            mtype  = "adjustment_add" if direction == "add" else "adjustment_remove"
            change = qty if direction == "add" else -qty

            with get_session() as session:
                p = session.get(Product, product["id"])
                if not p:
                    return
                new_stock = p.stock + change
                if new_stock < 0:
                    self._toast("Cannot remove more than available stock.", error=True)
                    return
                before  = p.stock
                p.stock = new_stock
                session.add(StockMovement(
                    product_id=p.id,
                    user_id=self.user.id,
                    movement_type=mtype,
                    quantity_change=change,
                    stock_before=before,
                    stock_after=new_stock,
                    reason=reason,
                ))

            sign = "+" if direction == "add" else "−"
            self._toast(f"{product['name']}  {sign}{qty:g} {product['unit']}  ·  {reason}")
            self._load_products()

        except Exception as e:
            logger.error("Adjustment error: %s", e)
            self._toast(f"Error: {e}", error=True)

    def _toast(self, msg: str, error=False):
        bg    = "#DC2626" if error else "#1A3C6B"
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
        QTimer.singleShot(2600, toast.deleteLater)
