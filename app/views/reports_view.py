"""
app/views/reports_view.py
--------------------------
Reports — daily, monthly, inventory.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGraphicsDropShadowEffect, QDateEdit, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QColor, QFont
from app.config import CONFIG

logger   = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")


def card_shadow():
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(12)
    s.setOffset(0, 1)
    s.setColor(QColor(0, 0, 0, 12))
    return s


def tab_btn(text, width=140):
    b = QPushButton(text)
    b.setCheckable(True)
    b.setFixedHeight(50)
    b.setFixedWidth(width)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet("""
        QPushButton {
            background:transparent; color:#9CA3AF;
            border:none; border-bottom:2px solid transparent;
            font-size:13px; font-weight:600;
        }
        QPushButton:hover   { color:#374151; }
        QPushButton:checked { color:#1A3C6B; border-bottom:2px solid #1A3C6B; }
    """)
    return b


def stat_card(title, value, sub="", color="#1A3C6B", bg="#EFF6FF") -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background:{bg};
            border-radius:12px;
            border:1px solid #E5E7EB;
        }}
    """)
    card.setGraphicsEffect(card_shadow())
    card.setFixedHeight(96)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 14, 20, 14)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"font-size:11px; font-weight:bold; color:#9CA3AF; "
                             f"letter-spacing:0.5px; background:transparent;")

    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"font-size:22px; font-weight:bold; "
                           f"color:{color}; background:transparent;")

    sub_lbl = QLabel(sub)
    sub_lbl.setStyleSheet("font-size:11px; color:#9CA3AF; background:transparent;")

    layout.addWidget(title_lbl)
    layout.addWidget(val_lbl)
    if sub:
        layout.addWidget(sub_lbl)
    return card


def table_card(headers, col_stretch_idx=None, amount_cols=None) -> tuple:
    """Returns (card_frame, table_widget)."""
    card = QFrame()
    card.setStyleSheet("""
        QFrame { background:white; border-radius:12px; border:1px solid #E5E7EB; }
    """)
    card.setGraphicsEffect(card_shadow())
    cl = QVBoxLayout(card)
    cl.setContentsMargins(0, 0, 0, 0)

    tbl = QTableWidget()
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    if col_stretch_idx is not None:
        tbl.horizontalHeader().setSectionResizeMode(
            col_stretch_idx, QHeaderView.ResizeMode.Stretch
        )
    # Fix amount columns so they never wrap
    if amount_cols:
        for col in amount_cols:
            tbl.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            tbl.setColumnWidth(col, 130)
    tbl.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
    tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(False)
    tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    tbl.setFrameShape(QFrame.Shape.NoFrame)
    tbl.setAlternatingRowColors(False)
    tbl.setStyleSheet("""
        QTableWidget {
            background:white; border:none; font-size:12px;
        }
        QTableWidget::item {
            padding:0 14px; color:#374151;
            border-bottom:1px solid #F9FAFB;
        }
        QTableWidget::item:selected {
            background:#EFF6FF; color:#1A3C6B;
        }
        QHeaderView::section {
            background:white; color:#9CA3AF;
            font-size:11px; font-weight:bold;
            letter-spacing:0.5px;
            padding:12px 14px;
            border:none; border-bottom:1px solid #E5E7EB;
        }
        QScrollBar:vertical { width:4px; background:transparent; }
        QScrollBar::handle:vertical { background:#E5E7EB; border-radius:2px; }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical { height:0; }
    """)
    cl.addWidget(tbl)
    return card, tbl


def cell(text, color="#374151", bold=False, align=Qt.AlignmentFlag.AlignLeft):
    it = QTableWidgetItem(text)
    it.setForeground(QColor(color))
    if bold:
        it.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    it.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
    return it


# ── Daily Report ─────────────────────────────────────────────────

class DailyReport(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet("background:#F8FAFC;")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)

        date_lbl = QLabel("Date")
        date_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(40)
        self.date_edit.setFixedWidth(160)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                border:1.5px solid #E5E7EB; border-radius:9px;
                padding:0 12px; font-size:13px;
                background:white; color:#111827;
            }
            QDateEdit:focus { border-color:#1A3C6B; }
            QDateEdit::drop-down { border:none; width:26px; }
        """)

        load_btn = QPushButton("Load Report")
        load_btn.setFixedHeight(40)
        load_btn.setFixedWidth(120)
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.setStyleSheet("""
            QPushButton {
                background:#1A3C6B; color:white;
                border:none; border-radius:9px;
                font-size:13px; font-weight:bold;
            }
            QPushButton:hover { background:#2E75B6; }
        """)
        load_btn.clicked.connect(self._load)

        bar.addWidget(date_lbl)
        bar.addWidget(self.date_edit)
        bar.addWidget(load_btn)
        bar.addStretch()

        dl_btn = QPushButton("⬇  Download PDF")
        dl_btn.setFixedHeight(40); dl_btn.setFixedWidth(140)
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet("""
            QPushButton { background:#F3F4F6; color:#374151; border:none;
                border-radius:9px; font-size:12px; font-weight:bold; }
            QPushButton:hover { background:#E5E7EB; }
        """)
        dl_btn.clicked.connect(self._download_pdf)
        bar.addWidget(dl_btn)
        layout.addLayout(bar)

        # Stat cards row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)
        self.s_revenue  = stat_card("TOTAL REVENUE",      f"{CURRENCY} 0.00")
        self.s_txns     = stat_card("TRANSACTIONS",       "0",
                                    color="#059669", bg="#ECFDF5")
        self.s_returns  = stat_card("RETURNS",            f"{CURRENCY} 0.00",
                                    color="#DC2626", bg="#FEF2F2")
        self.s_net      = stat_card("NET REVENUE",        f"{CURRENCY} 0.00",
                                    color="#1A3C6B", bg="#EFF6FF")
        for s in (self.s_revenue, self.s_txns, self.s_returns, self.s_net):
            self.stats_row.addWidget(s)
        layout.addLayout(self.stats_row)

        # Scroll area for tables
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
        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        # Sales breakdown table
        sec1 = QLabel("Sales Transactions")
        sec1.setStyleSheet("font-size:13px; font-weight:bold; color:#374151;")
        inner_layout.addWidget(sec1)

        self.txn_card, self.txn_table = table_card(
            ["Receipt No.", "Time", "Items", "Payment", "Cashier", "Total"],
            col_stretch_idx=0, amount_cols=[5]
        )
        self.txn_table.setFixedHeight(220)
        inner_layout.addWidget(self.txn_card)

        # By category
        sec2 = QLabel("Revenue by Category")
        sec2.setStyleSheet("font-size:13px; font-weight:bold; color:#374151;")
        inner_layout.addWidget(sec2)

        self.cat_card, self.cat_table = table_card(
            ["Category", "Items Sold", "Revenue"],
            col_stretch_idx=0, amount_cols=[2]
        )
        self.cat_table.setFixedHeight(180)
        inner_layout.addWidget(self.cat_card)

        # By cashier
        sec3 = QLabel("Performance by Staff")
        sec3.setStyleSheet("font-size:13px; font-weight:bold; color:#374151;")
        inner_layout.addWidget(sec3)

        self.staff_card, self.staff_table = table_card(
            ["Staff Member", "Transactions", "Revenue"],
            col_stretch_idx=0, amount_cols=[2]
        )
        self.staff_table.setFixedHeight(160)
        inner_layout.addWidget(self.staff_card)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _load(self):
        date = self.date_edit.date().toPyDate()
        try:
            from app.database import get_session
            from app.models.sale import Sale, SaleItem
            from app.models.return_transaction import ReturnTransaction
            from app.models.user import User as UserModel
            from app.models.product import Product
            import sqlalchemy as sa

            with get_session() as session:
                sales = (
                    session.query(Sale)
                    .filter(sa.func.date(Sale.created_at) == date)
                    .filter(Sale.status == "completed")
                    .all()
                )

                total_revenue = sum(s.total for s in sales)
                total_txns    = len(sales)

                returns = (
                    session.query(ReturnTransaction)
                    .filter(sa.func.date(ReturnTransaction.created_at) == date)
                    .all()
                )
                total_returns = sum(r.refund_amount for r in returns)
                net_revenue   = total_revenue - total_returns

                # Update stat cards
                self._update_stat(self.s_revenue, f"{CURRENCY} {total_revenue:,.2f}")
                self._update_stat(self.s_txns,    str(total_txns))
                self._update_stat(self.s_returns,  f"{CURRENCY} {total_returns:,.2f}")
                self._update_stat(self.s_net,      f"{CURRENCY} {net_revenue:,.2f}")

                # Transactions table
                self.txn_table.setRowCount(len(sales))
                for i, s in enumerate(sales):
                    self.txn_table.setRowHeight(i, 44)
                    cashier = session.get(UserModel, s.cashier_id)
                    items_count = sum(it.quantity for it in s.items)
                    for j, (val, color, bold) in enumerate([
                        (s.receipt_number,             "#1A3C6B", True),
                        (s.created_at.strftime("%H:%M"), "#6B7280", False),
                        (f"{items_count:g}",            "#374151", False),
                        (s.payment_method.title(),      "#374151", False),
                        (cashier.full_name if cashier else "—", "#374151", False),
                        (f"{CURRENCY} {s.total:,.2f}", "#059669", True),
                    ]):
                        self.txn_table.setItem(i, j, cell(val, color, bold))

                # Category breakdown
                cat_map = {}
                for s in sales:
                    for it in s.items:
                        prod = session.get(Product, it.product_id)
                        cat  = prod.category if prod else "Unknown"
                        if cat not in cat_map:
                            cat_map[cat] = {"qty": 0, "revenue": 0}
                        cat_map[cat]["qty"]     += it.quantity
                        cat_map[cat]["revenue"] += it.line_total

                sorted_cats = sorted(cat_map.items(), key=lambda x: -x[1]["revenue"])
                self.cat_table.setRowCount(len(sorted_cats))
                for i, (cat, data) in enumerate(sorted_cats):
                    self.cat_table.setRowHeight(i, 44)
                    self.cat_table.setItem(i, 0, cell(cat, "#374151", True))
                    self.cat_table.setItem(i, 1, cell(f"{data['qty']:g}", "#374151"))
                    self.cat_table.setItem(i, 2, cell(f"{CURRENCY} {data['revenue']:,.2f}", "#059669", True))

                # Staff breakdown
                staff_map = {}
                for s in sales:
                    cashier = session.get(UserModel, s.cashier_id)
                    name = cashier.full_name if cashier else "Unknown"
                    if name not in staff_map:
                        staff_map[name] = {"txns": 0, "revenue": 0}
                    staff_map[name]["txns"]    += 1
                    staff_map[name]["revenue"] += s.total

                sorted_staff = sorted(staff_map.items(), key=lambda x: -x[1]["revenue"])
                self.staff_table.setRowCount(len(sorted_staff))
                for i, (name, data) in enumerate(sorted_staff):
                    self.staff_table.setRowHeight(i, 44)
                    self.staff_table.setItem(i, 0, cell(name, "#374151", True))
                    self.staff_table.setItem(i, 1, cell(str(data["txns"]), "#374151"))
                    self.staff_table.setItem(i, 2, cell(f"{CURRENCY} {data['revenue']:,.2f}", "#059669", True))

        except Exception as e:
            logger.error("Daily report error: %s", e)

    def _update_stat(self, card: QFrame, value: str):
        for child in card.findChildren(QLabel):
            if child.styleSheet() and "22px" in child.styleSheet():
                child.setText(value)
                break


    def _download_pdf(self):
        date = self.date_edit.date().toPyDate()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Daily Report",
            f"daily_report_{date}.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            )
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
            from reportlab.lib import colors
            from app.database import get_session
            from app.models.sale import Sale, SaleItem
            from app.models.setting import Setting
            import sqlalchemy as sa

            with get_session() as session:
                settings = {s.key: s.value for s in session.query(Setting).all()}
                sales = (
                    session.query(Sale)
                    .filter(sa.func.date(Sale.created_at) == date, Sale.status == "completed")
                    .all()
                )
                total_rev  = sum(s.total for s in sales)
                total_txns = len(sales)

                biz = settings.get("business_name", "My Business")

            doc = SimpleDocTemplate(path, pagesize=A4,
                leftMargin=15*mm, rightMargin=15*mm,
                topMargin=15*mm, bottomMargin=15*mm)

            H1 = ParagraphStyle("H1", fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=20)
            H2 = ParagraphStyle("H2", fontSize=11, fontName="Helvetica-Bold", leading=14)
            N  = ParagraphStyle("N",  fontSize=9,  leading=12)
            story = [
                Paragraph(biz.upper(), H1),
                Paragraph(f"Daily Sales Report — {date.strftime('%d %B %Y')}", ParagraphStyle("sub", fontSize=10, alignment=TA_CENTER, textColor=colors.grey, leading=14)),
                Spacer(1, 6*mm),
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1A3C6B")),
                Spacer(1, 4*mm),
            ]

            # Summary table
            summary = Table(
                [["Total Revenue", "Transactions", "Avg per Sale"],
                 [f"KES {total_rev:,.2f}", str(total_txns),
                  f"KES {(total_rev/total_txns if total_txns else 0):,.2f}"]],
                colWidths=[60*mm, 50*mm, 60*mm]
            )
            summary.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,0), colors.HexColor("#1A3C6B")),
                ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
                ('FONTNAME',     (0,0), (-1,0), "Helvetica-Bold"),
                ('FONTSIZE',     (0,0), (-1,-1), 10),
                ('FONTNAME',     (0,1), (-1,1), "Helvetica-Bold"),
                ('FONTSIZE',     (0,1), (-1,1), 12),
                ('ALIGN',        (0,0), (-1,-1), "CENTER"),
                ('VALIGN',       (0,0), (-1,-1), "MIDDLE"),
                ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.HexColor("#EFF6FF")]),
                ('TOPPADDING',   (0,0), (-1,-1), 8),
                ('BOTTOMPADDING',(0,0), (-1,-1), 8),
                ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ]))
            story += [summary, Spacer(1, 6*mm)]

            # Transactions table
            story.append(Paragraph("Transactions", H2))
            story.append(Spacer(1, 2*mm))

            with get_session() as session:
                from app.models.user import User as UModel
                sales2 = (
                    session.query(Sale)
                    .filter(sa.func.date(Sale.created_at) == date, Sale.status=="completed")
                    .all()
                )
                rows = [["Receipt #", "Time", "Payment", "Cashier", "Total"]]
                for s in sales2:
                    u = session.get(UModel, s.cashier_id)
                    rows.append([
                        s.receipt_number,
                        s.created_at.strftime("%H:%M"),
                        s.payment_method.title(),
                        u.full_name if u else "—",
                        f"KES {s.total:,.2f}",
                    ])

            txn_tbl = Table(rows, colWidths=[45*mm, 20*mm, 30*mm, 45*mm, 35*mm])
            txn_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), colors.HexColor("#F3F4F6")),
                ('FONTNAME',      (0,0), (-1,0), "Helvetica-Bold"),
                ('FONTSIZE',      (0,0), (-1,-1), 9),
                ('ALIGN',         (4,0), (4,-1), "RIGHT"),
                ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, colors.HexColor("#FAFAFA")]),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
            ]))
            story.append(txn_tbl)
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph(
                f"Generated: {__import__('datetime').datetime.now().strftime('%d %b %Y %H:%M')}",
                ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)
            ))

            doc.build(story)

            from PyQt6.QtWidgets import QFileDialog
            # toast
            import os
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import QTimer
            toast = QLabel(f"  ✓  Saved: {os.path.basename(path)}", self)
            toast.setStyleSheet("background:#059669; color:white; border-radius:9px; padding:12px 20px; font-size:13px; font-weight:bold;")
            toast.adjustSize(); toast.setFixedHeight(44)
            toast.move((self.width()-toast.width())//2, self.height()-70)
            toast.show(); toast.raise_()
            QTimer.singleShot(2800, toast.deleteLater)

        except Exception as e:
            logger.error("Daily PDF error: %s", e)


# ── Monthly Report ────────────────────────────────────────────────

class MonthlyReport(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet("background:#F8FAFC;")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ])
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.month_combo.setFixedHeight(40)
        self.month_combo.setFixedWidth(140)
        self.month_combo.setStyleSheet("""
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

        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        self.year_combo.addItems([str(y) for y in range(current_year, current_year - 5, -1)])
        self.year_combo.setFixedHeight(40)
        self.year_combo.setFixedWidth(100)
        self.year_combo.setStyleSheet(self.month_combo.styleSheet())

        load_btn = QPushButton("Load Report")
        load_btn.setFixedHeight(40)
        load_btn.setFixedWidth(120)
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.setStyleSheet("""
            QPushButton {
                background:#1A3C6B; color:white;
                border:none; border-radius:9px;
                font-size:13px; font-weight:bold;
            }
            QPushButton:hover { background:#2E75B6; }
        """)
        load_btn.clicked.connect(self._load)

        bar.addWidget(QLabel("Month"))
        bar.addWidget(self.month_combo)
        bar.addWidget(self.year_combo)
        bar.addWidget(load_btn)
        bar.addStretch()
        for lbl in bar.parentWidget().findChildren(QLabel) if bar.parentWidget() else []:
            lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#374151;")
        layout.addLayout(bar)

        # Stat cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self.s_revenue = stat_card("MONTHLY REVENUE",    f"{CURRENCY} 0.00")
        self.s_txns    = stat_card("TOTAL TRANSACTIONS", "0",
                                   color="#059669", bg="#ECFDF5")
        self.s_avg     = stat_card("AVG DAILY REVENUE",  f"{CURRENCY} 0.00",
                                   color="#D97706", bg="#FFFBEB")
        self.s_top     = stat_card("TOP DAY REVENUE",    f"{CURRENCY} 0.00",
                                   color="#7C3AED", bg="#F5F3FF")
        for s in (self.s_revenue, self.s_txns, self.s_avg, self.s_top):
            stats_row.addWidget(s)
        layout.addLayout(stats_row)

        # Scroll
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
        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(16)

        sec1 = QLabel("Day-by-Day Breakdown")
        sec1.setStyleSheet("font-size:13px; font-weight:bold; color:#374151;")
        il.addWidget(sec1)

        self.daily_card, self.daily_table = table_card(
            ["Date", "Transactions", "Revenue", "Returns", "Net"],
            col_stretch_idx=0, amount_cols=[2,3,4]
        )
        self.daily_table.setFixedHeight(280)
        il.addWidget(self.daily_card)

        sec2 = QLabel("Top Products This Month")
        sec2.setStyleSheet("font-size:13px; font-weight:bold; color:#374151;")
        il.addWidget(sec2)

        self.top_card, self.top_table = table_card(
            ["Product", "Category", "Qty Sold", "Revenue"],
            col_stretch_idx=0, amount_cols=[3]
        )
        self.top_table.setFixedHeight(200)
        il.addWidget(self.top_card)
        il.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _load(self):
        month = self.month_combo.currentIndex() + 1
        year  = int(self.year_combo.currentText())
        try:
            from app.database import get_session
            from app.models.sale import Sale, SaleItem
            from app.models.return_transaction import ReturnTransaction
            from app.models.product import Product
            import sqlalchemy as sa
            from collections import defaultdict
            import calendar

            with get_session() as session:
                sales = (
                    session.query(Sale)
                    .filter(
                        sa.extract("year",  Sale.created_at) == year,
                        sa.extract("month", Sale.created_at) == month,
                        Sale.status == "completed"
                    ).all()
                )

                returns = (
                    session.query(ReturnTransaction)
                    .filter(
                        sa.extract("year",  ReturnTransaction.created_at) == year,
                        sa.extract("month", ReturnTransaction.created_at) == month,
                    ).all()
                )

                total_rev  = sum(s.total for s in sales)
                total_txns = len(sales)
                days_in_mo = calendar.monthrange(year, month)[1]
                avg_daily  = total_rev / days_in_mo if days_in_mo else 0

                # Day map
                day_rev = defaultdict(float)
                day_txn = defaultdict(int)
                for s in sales:
                    d = s.created_at.day
                    day_rev[d] += s.total
                    day_txn[d] += 1

                day_ret = defaultdict(float)
                for r in returns:
                    day_ret[r.created_at.day] += r.refund_amount

                top_day_rev = max(day_rev.values(), default=0)

                self._update_stat(self.s_revenue, f"{CURRENCY} {total_rev:,.2f}")
                self._update_stat(self.s_txns,    str(total_txns))
                self._update_stat(self.s_avg,     f"{CURRENCY} {avg_daily:,.2f}")
                self._update_stat(self.s_top,     f"{CURRENCY} {top_day_rev:,.2f}")

                # Day-by-day table
                self.daily_table.setRowCount(days_in_mo)
                month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                               "Jul","Aug","Sep","Oct","Nov","Dec"]
                for d in range(1, days_in_mo + 1):
                    self.daily_table.setRowHeight(d - 1, 44)
                    rev = day_rev.get(d, 0)
                    ret = day_ret.get(d, 0)
                    net = rev - ret
                    self.daily_table.setItem(d-1, 0, cell(f"{d:02d} {month_names[month-1]} {year}", "#374151", True))
                    self.daily_table.setItem(d-1, 1, cell(str(day_txn.get(d, 0)), "#374151"))
                    self.daily_table.setItem(d-1, 2, cell(f"{CURRENCY} {rev:,.2f}", "#059669" if rev else "#9CA3AF"))
                    self.daily_table.setItem(d-1, 3, cell(f"{CURRENCY} {ret:,.2f}", "#DC2626" if ret else "#9CA3AF"))
                    self.daily_table.setItem(d-1, 4, cell(f"{CURRENCY} {net:,.2f}", "#1A3C6B", True))

                # Top products
                prod_map = defaultdict(lambda: {"cat": "", "qty": 0, "rev": 0})
                for s in sales:
                    for it in s.items:
                        prod = session.get(Product, it.product_id)
                        name = it.product_name
                        cat  = prod.category if prod else "—"
                        prod_map[name]["cat"]  = cat
                        prod_map[name]["qty"] += it.quantity
                        prod_map[name]["rev"] += it.line_total

                top_prods = sorted(prod_map.items(), key=lambda x: -x[1]["rev"])[:15]
                self.top_table.setRowCount(len(top_prods))
                for i, (name, data) in enumerate(top_prods):
                    self.top_table.setRowHeight(i, 44)
                    self.top_table.setItem(i, 0, cell(name, "#374151", True))
                    self.top_table.setItem(i, 1, cell(data["cat"], "#6B7280"))
                    self.top_table.setItem(i, 2, cell(f"{data['qty']:g}", "#374151"))
                    self.top_table.setItem(i, 3, cell(f"{CURRENCY} {data['rev']:,.2f}", "#059669", True))

        except Exception as e:
            logger.error("Monthly report error: %s", e)

    def _update_stat(self, card, value):
        for child in card.findChildren(QLabel):
            if child.styleSheet() and "22px" in child.styleSheet():
                child.setText(value)
                break


# ── Inventory Report ──────────────────────────────────────────────

class InventoryReport(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet("background:#F8FAFC;")
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.search = QComboBox()
        self.search = __import__('PyQt6.QtWidgets', fromlist=['QLineEdit']).QLineEdit()
        self.search.setPlaceholderText("Search product...")
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

        self.lv_filter = QComboBox()
        self.lv_filter.addItems(["All", "Low Stock", "Out of Stock", "In Stock"])
        self.lv_filter.setFixedHeight(40)
        self.lv_filter.setFixedWidth(140)
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

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setFixedWidth(100)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background:#F3F4F6; color:#374151;
                border:none; border-radius:9px;
                font-size:13px; font-weight:bold;
            }
            QPushButton:hover { background:#E5E7EB; }
        """)
        refresh_btn.clicked.connect(self._load)

        bar.addWidget(self.search)
        bar.addWidget(self.lv_filter)
        bar.addWidget(refresh_btn)
        bar.addStretch()
        layout.addLayout(bar)

        # Stat cards
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.s_total   = stat_card("TOTAL PRODUCTS",    "0")
        self.s_low     = stat_card("LOW STOCK",         "0",
                                   color="#D97706", bg="#FFFBEB")
        self.s_out     = stat_card("OUT OF STOCK",      "0",
                                   color="#DC2626", bg="#FEF2F2")
        self.s_value   = stat_card("STOCK VALUE (COST)", f"{CURRENCY} 0.00",
                                   color="#7C3AED", bg="#F5F3FF")
        for s in (self.s_total, self.s_low, self.s_out, self.s_value):
            stats.addWidget(s)
        layout.addLayout(stats)

        # Table
        self.inv_card, self.inv_table = table_card(
            ["Product", "Category", "Unit", "Stock", "Threshold", "Status", "Price"],
            col_stretch_idx=0, amount_cols=[6]
        )
        layout.addWidget(self.inv_card)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-size:11px; color:#9CA3AF;")
        layout.addWidget(self.count_lbl)

        self.all_products = []

    def _load(self):
        try:
            from app.database import get_session
            from app.models.product import Product
            with get_session() as session:
                prods = session.query(Product).filter_by(is_active=True).order_by(Product.name).all()
                self.all_products = [
                    {
                        "name":      p.name,
                        "category":  p.category,
                        "unit":      p.unit,
                        "stock":     p.stock,
                        "threshold": p.low_stock_threshold,
                        "price":     p.price,
                    }
                    for p in prods
                ]

            total = len(self.all_products)
            low   = sum(1 for p in self.all_products if 0 < p["stock"] <= p["threshold"])
            out   = sum(1 for p in self.all_products if p["stock"] <= 0)
            val   = sum(p["stock"] * p["price"] for p in self.all_products)

            self._update_stat(self.s_total, str(total))
            self._update_stat(self.s_low,   str(low))
            self._update_stat(self.s_out,   str(out))
            self._update_stat(self.s_value, f"{CURRENCY} {val:,.2f}")
            self._filter()

        except Exception as e:
            logger.error("Inventory report error: %s", e)

    def _filter(self):
        q  = self.search.text().strip().lower()
        lv = self.lv_filter.currentText()
        out = []
        for p in self.all_products:
            if q and q not in p["name"].lower():
                continue
            if lv == "Low Stock"    and not (0 < p["stock"] <= p["threshold"]):
                continue
            if lv == "Out of Stock" and p["stock"] > 0:
                continue
            if lv == "In Stock"     and p["stock"] <= 0:
                continue
            out.append(p)
        self._render(out)

    def _render(self, products):
        STATUS = {
            "out":  ("Out of Stock", "#DC2626", "#FEF2F2"),
            "low":  ("Low Stock",    "#D97706", "#FFFBEB"),
            "ok":   ("In Stock",     "#059669", "#ECFDF5"),
        }
        self.inv_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.inv_table.setRowHeight(i, 46)
            out_of = p["stock"] <= 0
            low    = not out_of and p["stock"] <= p["threshold"]
            sk     = "out" if out_of else ("low" if low else "ok")
            slbl, sfg, _ = STATUS[sk]
            stock_color = "#DC2626" if out_of else ("#D97706" if low else "#059669")

            self.inv_table.setItem(i, 0, cell(p["name"],            "#111827", True))
            self.inv_table.setItem(i, 1, cell(p["category"],        "#6B7280"))
            self.inv_table.setItem(i, 2, cell(p["unit"],            "#6B7280"))
            self.inv_table.setItem(i, 3, cell(f"{p['stock']:g}",    stock_color, True))
            self.inv_table.setItem(i, 4, cell(f"{p['threshold']:g}","#9CA3AF"))
            st = QTableWidgetItem(slbl)
            st.setForeground(QColor(sfg))
            st.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.inv_table.setItem(i, 5, st)
            self.inv_table.setItem(i, 6, cell(f"{CURRENCY} {p['price']:,.2f}", "#1A3C6B", True))

        self.count_lbl.setText(f"{len(products)} products")

    def _update_stat(self, card, value):
        for child in card.findChildren(QLabel):
            if child.styleSheet() and "22px" in child.styleSheet():
                child.setText(value)
                break


# ── Main Reports View ─────────────────────────────────────────────

class ReportsView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet("background:#F8FAFC;")
        self._build()

    def _build(self):
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

        self.t_daily = tab_btn("Daily Report")
        self.t_month = tab_btn("Monthly Report", 160)
        self.t_inv   = tab_btn("Inventory",  120)
        self.t_daily.setChecked(True)
        self.t_daily.clicked.connect(lambda: self._switch(0))
        self.t_month.clicked.connect(lambda: self._switch(1))
        self.t_inv.clicked.connect(lambda: self._switch(2))

        tbl.addWidget(self.t_daily)
        tbl.addWidget(self.t_month)
        tbl.addWidget(self.t_inv)
        tbl.addStretch()
        root.addWidget(tab_bar)

        self.stack = QStackedWidget()
        self.stack.addWidget(DailyReport(self.user))
        self.stack.addWidget(MonthlyReport(self.user))
        self.stack.addWidget(InventoryReport(self.user))
        root.addWidget(self.stack)

    def _switch(self, idx):
        self.t_daily.setChecked(idx == 0)
        self.t_month.setChecked(idx == 1)
        self.t_inv.setChecked(idx == 2)
        self.stack.setCurrentIndex(idx)
