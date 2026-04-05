"""
app/views/receipt_preview.py
-----------------------------
Receipt preview — clean invoice-style layout.
Matches the minimal invoice template design language.
"""
import logging
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from app.config import CONFIG
from app.utils.theme import Th

logger   = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")


class ReceiptPreview(QDialog):
    def __init__(self, sale_data: dict, parent=None):
        super().__init__(parent)
        self.sale_data = sale_data
        self.setModal(True)
        self.setWindowTitle("Receipt Preview")
        self.setFixedWidth(560)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        shell = QFrame()
        shell.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 14px;
                border: none;
            }
        """)
        sh = Th.shadow_lg()
        shell.setGraphicsEffect(sh)

        sl = QVBoxLayout(shell)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # ── Header ───────────────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet(f"""
            QFrame {{
                background: {Th.PRIMARY};
                border-radius: 14px 14px 0 0;
            }}
        """)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(20, 0, 16, 0)

        title = QLabel("Receipt Preview")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: 600;")
        hint = QLabel("exactly as it will print")
        hint.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px;")

        close = QPushButton("✕")
        close.setFixedSize(28, 28)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white; border: none;
                border-radius: 7px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.25); }
        """)
        close.clicked.connect(self.reject)
        hl.addWidget(title)
        hl.addSpacing(10)
        hl.addWidget(hint)
        hl.addStretch()
        hl.addWidget(close)
        sl.addWidget(hdr)

        # ── Scroll ───────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setFixedHeight(520)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {Th.INK_50}; border: none; }}
            {Th.SCROLLBAR}
        """)

        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {Th.INK_50};")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 28, 0, 28)
        wl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        wl.addWidget(
            self._build_receipt(),
            alignment=Qt.AlignmentFlag.AlignHCenter
        )
        scroll.setWidget(wrapper)
        sl.addWidget(scroll)

        # ── Action bar ────────────────────────────────────────
        act = QFrame()
        act.setFixedHeight(68)
        act.setStyleSheet("""
            QFrame {
                background: white;
                border-top: 1px solid #F1F5F9;
                border-radius: 0 0 14px 14px;
            }
        """)
        al = QHBoxLayout(act)
        al.setContentsMargins(20, 0, 20, 0)
        al.setSpacing(10)

        close_btn = Th.btn_secondary("Close", h=42, w=90)
        close_btn.clicked.connect(self.reject)

        pdf_btn = Th.btn_primary("Save PDF", h=42, w=120)
        pdf_btn.clicked.connect(self._save_pdf)

        print_btn = Th.btn_success("Print", h=42, w=100)
        print_btn.clicked.connect(self._print)

        al.addWidget(close_btn)
        al.addStretch()
        al.addWidget(pdf_btn)
        al.addWidget(print_btn)
        sl.addWidget(act)

        outer.addWidget(shell)

    # ── Receipt document ─────────────────────────────────────

    def _build_receipt(self) -> QFrame:
        d = self.sale_data

        receipt = QFrame()
        receipt.setFixedWidth(320)
        receipt.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 2px;
            }
        """)
        sh = Th.shadow(24, 4, 14)
        receipt.setGraphicsEffect(sh)

        lo = QVBoxLayout(receipt)
        lo.setContentsMargins(24, 28, 24, 28)
        lo.setSpacing(0)

        def mono(text, size=10, bold=False,
                 color=Th.INK_900, center=False, italic=False):
            l = QLabel(text)
            f = QFont("Courier New", size)
            f.setBold(bold)
            f.setItalic(italic)
            l.setFont(f)
            l.setStyleSheet(
                f"color:{color}; background:transparent;"
            )
            if center:
                l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setWordWrap(True)
            return l

        def rule():
            f = QFrame()
            f.setFrameShape(QFrame.Shape.HLine)
            f.setFixedHeight(1)
            f.setStyleSheet(f"background:{Th.DIVIDER}; border:none;")
            return f

        def spacer(h=8):
            f = QWidget()
            f.setFixedHeight(h)
            f.setStyleSheet("background:transparent;")
            return f

        def row(left, right, left_size=10, right_size=10,
                right_bold=False, right_color=None, left_color=None):
            w  = QWidget()
            w.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(w)
            rl.setContentsMargins(0, 2, 0, 2)

            ll = QLabel(left)
            ll.setFont(QFont("Courier New", left_size))
            ll.setStyleSheet(
                f"color:{left_color or Th.INK_500}; background:transparent;"
            )

            rv = QLabel(right)
            rf = QFont("Courier New", right_size)
            rf.setBold(right_bold)
            rv.setFont(rf)
            rv.setStyleSheet(
                f"color:{right_color or Th.INK_900}; background:transparent;"
            )
            rv.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            rl.addWidget(ll)
            rl.addStretch()
            rl.addWidget(rv)
            return w

        # ── Business name ─────────────────────────────────────
        biz_name = d.get("business_name", "My Business").upper()
        bname = QLabel(biz_name)
        bname.setFont(QFont("Courier New", 15, QFont.Weight.Bold))
        bname.setStyleSheet(
            f"color:{Th.INK_900}; background:transparent; letter-spacing:2px;"
        )
        bname.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(bname)
        lo.addWidget(spacer(4))
        lo.addWidget(mono(
            "RECEIPT", 9, False, Th.INK_300, center=True
        ))
        lo.addWidget(spacer(16))
        lo.addWidget(rule())
        lo.addWidget(spacer(12))

        # ── Meta ──────────────────────────────────────────────
        lo.addWidget(row("RECEIPT NO.", d.get("receipt_number", "—"),
                         left_size=9, right_size=9,
                         left_color=Th.INK_300, right_color=Th.INK_700))
        lo.addWidget(row("DATE",        d.get("date_str", "—"),
                         left_size=9, right_size=9,
                         left_color=Th.INK_300, right_color=Th.INK_700))
        lo.addWidget(row("CASHIER",     d.get("cashier_name", "—"),
                         left_size=9, right_size=9,
                         left_color=Th.INK_300, right_color=Th.INK_700))
        lo.addWidget(spacer(12))
        lo.addWidget(rule())
        lo.addWidget(spacer(12))

        # ── Column headers ────────────────────────────────────
        col_hdr = QWidget()
        col_hdr.setStyleSheet("background:transparent;")
        ch = QHBoxLayout(col_hdr)
        ch.setContentsMargins(0, 0, 0, 0)

        for txt, stretch, align in [
            ("ITEM",      2, Qt.AlignmentFlag.AlignLeft),
            ("QTY",       0, Qt.AlignmentFlag.AlignCenter),
            ("PRICE",     0, Qt.AlignmentFlag.AlignRight),
            ("TOTAL",     0, Qt.AlignmentFlag.AlignRight),
        ]:
            l = QLabel(txt)
            l.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{Th.INK_300}; background:transparent; letter-spacing:0.5px;")
            l.setAlignment(align)
            if stretch:
                ch.addWidget(l, stretch)
            else:
                if txt == "QTY":
                    l.setFixedWidth(32)
                else:
                    l.setFixedWidth(70)
                ch.addWidget(l)

        lo.addWidget(col_hdr)
        lo.addWidget(spacer(6))

        # ── Items ─────────────────────────────────────────────
        for i, item in enumerate(d.get("items", [])):
            item_row = QWidget()
            item_row.setStyleSheet(
                f"background: {'#FAFBFC' if i % 2 == 0 else 'transparent'};"
                " border-radius: 4px;"
            )
            ir = QHBoxLayout(item_row)
            ir.setContentsMargins(0, 4, 0, 4)

            name_lbl = QLabel(item["name"])
            name_lbl.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            name_lbl.setStyleSheet(
                f"color:{Th.INK_900}; background:transparent;"
            )
            name_lbl.setWordWrap(True)

            qty_lbl = QLabel(f"{item['quantity']:g}")
            qty_lbl.setFixedWidth(32)
            qty_lbl.setFont(QFont("Courier New", 9))
            qty_lbl.setStyleSheet(
                f"color:{Th.INK_500}; background:transparent;"
            )
            qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            price_lbl = QLabel(f"{item['unit_price']:,.2f}")
            price_lbl.setFixedWidth(70)
            price_lbl.setFont(QFont("Courier New", 9))
            price_lbl.setStyleSheet(
                f"color:{Th.INK_500}; background:transparent;"
            )
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

            total_lbl = QLabel(f"{item['line_total']:,.2f}")
            total_lbl.setFixedWidth(70)
            total_lbl.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            total_lbl.setStyleSheet(
                f"color:{Th.INK_900}; background:transparent;"
            )
            total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

            ir.addWidget(name_lbl, 2)
            ir.addWidget(qty_lbl)
            ir.addWidget(price_lbl)
            ir.addWidget(total_lbl)
            lo.addWidget(item_row)

        lo.addWidget(spacer(10))
        lo.addWidget(rule())
        lo.addWidget(spacer(10))

        # ── Totals ────────────────────────────────────────────
        if d.get("discount", 0) > 0:
            lo.addWidget(row(
                "Subtotal", f"{CURRENCY} {d.get('subtotal',0):,.2f}",
                left_size=9, right_size=9
            ))
            lo.addWidget(row(
                "Discount", f"- {CURRENCY} {d['discount']:,.2f}",
                left_size=9, right_size=9,
                right_color=Th.DANGER
            ))
            lo.addWidget(spacer(6))

        # Grand total row
        total_row = QWidget()
        total_row.setStyleSheet("background:transparent;")
        tr = QHBoxLayout(total_row)
        tr.setContentsMargins(0, 6, 0, 6)

        tl_label = QLabel("TOTAL")
        tl_label.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        tl_label.setStyleSheet(
            f"color:{Th.INK_900}; background:transparent; letter-spacing:1px;"
        )

        tl_value = QLabel(f"{CURRENCY} {d.get('total',0):,.2f}")
        tl_value.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        tl_value.setStyleSheet(
            f"color:{Th.PRIMARY}; background:transparent;"
        )
        tl_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        tr.addWidget(tl_label)
        tr.addStretch()
        tr.addWidget(tl_value)
        lo.addWidget(total_row)
        lo.addWidget(spacer(10))
        lo.addWidget(rule())
        lo.addWidget(spacer(10))

        # ── Payment block ─────────────────────────────────────
        lo.addWidget(row(
            "Payment Method",
            d.get("payment_method", "Cash").title(),
            left_size=9, right_size=9
        ))
        if d.get("payment_ref"):
            lo.addWidget(row(
                "Reference", d["payment_ref"],
                left_size=9, right_size=9
            ))
        if d.get("tendered") is not None:
            lo.addWidget(row(
                "Tendered",
                f"{CURRENCY} {d['tendered']:,.2f}",
                left_size=9, right_size=9
            ))
        if d.get("change") is not None and d["change"] >= 0:
            lo.addWidget(row(
                "Change",
                f"{CURRENCY} {d['change']:,.2f}",
                left_size=9, right_size=10,
                right_bold=True,
                right_color=Th.SUCCESS
            ))

        # ── Footer ────────────────────────────────────────────
        footer = d.get("receipt_footer", "")
        if footer:
            lo.addWidget(spacer(16))
            lo.addWidget(rule())
            lo.addWidget(spacer(12))

            ft = QLabel(footer)
            ft.setFont(QFont("Courier New", 9))
            ft.setStyleSheet(
                f"color:{Th.INK_300}; background:transparent;"
            )
            ft.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ft.setWordWrap(True)
            lo.addWidget(ft)

        lo.addWidget(spacer(8))
        return receipt

    # ── PDF export ───────────────────────────────────────────

    def _save_pdf(self):
        d    = self.sale_data
        name = f"receipt_{d.get('receipt_number','unknown')}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt PDF", name, "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer,
                HRFlowable, Table, TableStyle
            )
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
            from reportlab.lib import colors

            W   = 72 * mm
            doc = SimpleDocTemplate(
                path,
                pagesize=(W, 999 * mm),
                leftMargin=6*mm, rightMargin=6*mm,
                topMargin=8*mm,  bottomMargin=8*mm
            )

            C   = ParagraphStyle("C",  fontSize=7,  alignment=TA_CENTER, leading=10, fontName="Courier")
            CT  = ParagraphStyle("CT", fontSize=12, alignment=TA_CENTER, leading=16, fontName="Courier-Bold")
            CS  = ParagraphStyle("CS", fontSize=8,  alignment=TA_CENTER, leading=10, fontName="Courier", textColor=colors.HexColor("#94A3B8"))
            N   = ParagraphStyle("N",  fontSize=8,  leading=11, fontName="Courier")
            NB  = ParagraphStyle("NB", fontSize=8,  leading=11, fontName="Courier-Bold")
            HR  = lambda: HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#E2E8F0"), spaceAfter=3, spaceBefore=3)
            SP  = lambda h=3: Spacer(1, h*mm)
            BIZ = d.get("business_name","My Business").upper()

            def meta_row(label, value):
                t = Table(
                    [[label, value]],
                    colWidths=[28*mm, 32*mm]
                )
                t.setStyle(TableStyle([
                    ('FONTNAME',  (0,0),(0,0), "Courier"),
                    ('FONTNAME',  (1,0),(1,0), "Courier"),
                    ('FONTSIZE',  (0,0),(-1,-1), 7),
                    ('TEXTCOLOR', (0,0),(0,0), colors.HexColor("#94A3B8")),
                    ('ALIGN',     (1,0),(1,0), "RIGHT"),
                    ('TOPPADDING',(0,0),(-1,-1), 1),
                    ('BOTTOMPADDING',(0,0),(-1,-1), 1),
                ]))
                return t

            story = [
                Paragraph(BIZ, CT),
                SP(1),
                Paragraph("RECEIPT", CS),
                SP(4), HR(), SP(2),
                meta_row("RECEIPT NO.", d.get("receipt_number","—")),
                meta_row("DATE",        d.get("date_str","—")),
                meta_row("CASHIER",     d.get("cashier_name","—")),
                SP(3), HR(), SP(2),
            ]

            # Column headers
            col_hdr = Table(
                [["ITEM", "QTY", "PRICE", "TOTAL"]],
                colWidths=[26*mm, 8*mm, 16*mm, 16*mm]
            )
            col_hdr.setStyle(TableStyle([
                ('FONTNAME',     (0,0),(-1,-1), "Courier-Bold"),
                ('FONTSIZE',     (0,0),(-1,-1), 7),
                ('TEXTCOLOR',    (0,0),(-1,-1), colors.HexColor("#94A3B8")),
                ('ALIGN',        (1,0),(3,0), "RIGHT"),
                ('BOTTOMPADDING',(0,0),(-1,-1), 4),
                ('TOPPADDING',   (0,0),(-1,-1), 0),
            ]))
            story.append(col_hdr)

            # Items
            rows = []
            for i, item in enumerate(d.get("items",[])):
                rows.append([
                    item["name"],
                    f"{item['quantity']:g}",
                    f"{item['unit_price']:,.2f}",
                    f"{item['line_total']:,.2f}",
                ])
            if rows:
                items_tbl = Table(rows, colWidths=[26*mm, 8*mm, 16*mm, 16*mm])
                items_tbl.setStyle(TableStyle([
                    ('FONTNAME',        (0,0),(0,-1), "Courier-Bold"),
                    ('FONTNAME',        (1,0),(-1,-1), "Courier"),
                    ('FONTSIZE',        (0,0),(-1,-1), 8),
                    ('ALIGN',           (1,0),(3,-1), "RIGHT"),
                    ('ROWBACKGROUNDS',  (0,0),(-1,-1),
                     [colors.HexColor("#FAFBFC"), colors.white]),
                    ('TOPPADDING',      (0,0),(-1,-1), 3),
                    ('BOTTOMPADDING',   (0,0),(-1,-1), 3),
                ]))
                story.append(items_tbl)

            story += [SP(3), HR(), SP(2)]

            if d.get("discount",0) > 0:
                story.append(meta_row("Subtotal", f"{CURRENCY} {d.get('subtotal',0):,.2f}"))
                story.append(meta_row("Discount", f"- {CURRENCY} {d['discount']:,.2f}"))
                story.append(SP(2))

            # Total
            total_tbl = Table(
                [["TOTAL", f"{CURRENCY} {d.get('total',0):,.2f}"]],
                colWidths=[28*mm, 32*mm]
            )
            total_tbl.setStyle(TableStyle([
                ('FONTNAME',     (0,0),(-1,-1), "Courier-Bold"),
                ('FONTSIZE',     (0,0),(-1,-1), 11),
                ('TEXTCOLOR',    (1,0),(1,0), colors.HexColor("#1B3F6E")),
                ('ALIGN',        (1,0),(1,0), "RIGHT"),
                ('TOPPADDING',   (0,0),(-1,-1), 4),
                ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ]))
            story += [total_tbl, SP(3), HR(), SP(2)]

            story.append(meta_row("Payment Method", d.get("payment_method","Cash").title()))
            if d.get("payment_ref"):
                story.append(meta_row("Reference", d["payment_ref"]))
            if d.get("tendered") is not None:
                story.append(meta_row("Tendered", f"{CURRENCY} {d['tendered']:,.2f}"))
            if d.get("change") is not None and d["change"] >= 0:
                story.append(meta_row("Change", f"{CURRENCY} {d['change']:,.2f}"))

            footer = d.get("receipt_footer","")
            if footer:
                story += [SP(5), HR(), SP(3), Paragraph(footer, C)]

            doc.build(story)
            self._toast(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            logger.error("PDF error: %s", e)
            self._toast(f"Failed: {e}", error=True)

    def _print(self):
        self._toast("Configure printer port in Settings, then retry.")

    def _toast(self, msg, error=False):
        bg = Th.DANGER if error else Th.SUCCESS
        t  = QLabel(f"  {'✕' if error else '✓'}  {msg}", self)
        t.setStyleSheet(f"""
            background:{bg}; color:white; border-radius:8px;
            padding:10px 16px; font-size:12px; font-weight:600;
        """)
        t.adjustSize()
        t.move((self.width() - t.width()) // 2, self.height() - 56)
        t.show(); t.raise_()
        QTimer.singleShot(2800, t.deleteLater)
