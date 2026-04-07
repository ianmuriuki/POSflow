"""
app/views/receipt_preview.py
"""
import logging, os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QFontMetrics
from app.config import CONFIG
from app.utils.theme import Th
from app.services.receipt_engine import build_receipt_lines, render_pdf, send_to_printer

logger   = logging.getLogger(__name__)
CURRENCY = CONFIG.get("currency", "KES")


class ReceiptPreview(QDialog):
    PAPER_WIDTH_PX = 310
    CHAR_FONT_SIZE = 9
    LINE_H         = 15

    def __init__(self, sale_data: dict, parent=None):
        super().__init__(parent)
        self.sale_data = sale_data
        self.setModal(True)
        self.setWindowTitle("Receipt Preview")
        self.setFixedWidth(500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        shell = QFrame()
        shell.setStyleSheet("QFrame { background:white; border-radius:14px; border:none; }")
        shell.setGraphicsEffect(Th.shadow_lg())

        sl = QVBoxLayout(shell)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(50)
        hdr.setStyleSheet(f"QFrame {{ background:{Th.PRIMARY}; border-radius:14px 14px 0 0; }}")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(18, 0, 14, 0)
        title = QLabel("Receipt Preview")
        title.setStyleSheet("color:white; font-size:14px; font-weight:700;")
        sub = QLabel("exactly as it will print")
        sub.setStyleSheet("color:rgba(255,255,255,0.45); font-size:11px;")
        close = QPushButton("✕")
        close.setFixedSize(28, 28)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,0.15); color:white;
                border:none; border-radius:7px; font-size:12px; }
            QPushButton:hover { background:rgba(255,255,255,0.25); }
        """)
        close.clicked.connect(self.reject)
        hl.addWidget(title); hl.addSpacing(10); hl.addWidget(sub)
        hl.addStretch(); hl.addWidget(close)
        sl.addWidget(hdr)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setFixedHeight(520)
        scroll.setStyleSheet(f"QScrollArea {{ background:{Th.INK_50}; border:none; }}{Th.SCROLLBAR}")

        wrapper = QWidget()
        wrapper.setStyleSheet(f"background:{Th.INK_50};")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 24, 0, 24)
        wl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        wl.addWidget(self._build_paper(), alignment=Qt.AlignmentFlag.AlignHCenter)
        scroll.setWidget(wrapper)
        sl.addWidget(scroll)

        # Actions
        act = QFrame()
        act.setFixedHeight(66)
        act.setStyleSheet("QFrame { background:white; border-top:1px solid #F1F5F9; border-radius:0 0 14px 14px; }")
        al = QHBoxLayout(act)
        al.setContentsMargins(18, 0, 18, 0)
        al.setSpacing(10)

        close_btn = Th.btn_secondary("Close", h=42, w=90)
        close_btn.clicked.connect(self.reject)
        pdf_btn = Th.btn_primary("💾  Save PDF", h=42, w=130)
        pdf_btn.clicked.connect(self._save_pdf)
        print_btn = Th.btn_success("🖨  Print", h=42, w=110)
        print_btn.clicked.connect(self._print)

        al.addWidget(close_btn); al.addStretch()
        al.addWidget(pdf_btn); al.addWidget(print_btn)
        sl.addWidget(act)

        outer.addWidget(shell)

    def _build_paper(self) -> QFrame:
        lines = build_receipt_lines(self.sale_data)

        paper = QFrame()
        paper.setFixedWidth(self.PAPER_WIDTH_PX)
        paper.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 2px;
            }
        """)
        paper.setGraphicsEffect(Th.shadow(22, 4, 16))

        lo = QVBoxLayout(paper)
        lo.setContentsMargins(14, 18, 14, 22)
        lo.setSpacing(0)

        FONT_R = QFont("Liberation Mono", self.CHAR_FONT_SIZE)
        FONT_B = QFont("Liberation Mono", self.CHAR_FONT_SIZE)
        FONT_B.setBold(True)

        for line in lines:
            bold = line.startswith("**")
            text = line[2:] if bold else line

            if text.strip() == "":
                sp = QWidget()
                sp.setFixedHeight(5)
                sp.setStyleSheet("background:transparent;")
                lo.addWidget(sp)
                continue

            lbl = QLabel(text)
            lbl.setFont(FONT_B if bold else FONT_R)
            lbl.setWordWrap(False)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

            is_rule = text.strip() and set(text.strip()) <= {"─","═","-","="}
            if bold:
                lbl.setStyleSheet(f"color:{Th.INK_900}; background:transparent; letter-spacing:0.3px;")
            elif is_rule:
                lbl.setStyleSheet(f"color:{Th.INK_300}; background:transparent;")
            else:
                lbl.setStyleSheet(f"color:{Th.INK_700}; background:transparent;")

            lo.addWidget(lbl)

        return paper

    def _save_pdf(self):
        d    = self.sale_data
        name = f"receipt_{d.get('receipt_number','unknown')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save Receipt PDF", name, "PDF (*.pdf)")
        if not path:
            return
        try:
            render_pdf(self.sale_data, path)
            self._toast(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            logger.error("PDF error: %s", e)
            self._toast(f"Failed: {e}", error=True)

    def _print(self):
        try:
            from app.database import get_session
            from app.models.setting import Setting
            with get_session() as session:
                s    = session.get(Setting, "printer_port")
                port = s.value if s else "auto"
            ok = send_to_printer(self.sale_data, port)
            if ok:
                self._toast("Sent to printer.")
            else:
                self._toast("Printer not found. Check port in Settings.", error=True)
        except Exception as e:
            self._toast(f"Print error: {e}", error=True)

    def _toast(self, msg: str, error=False):
        bg = Th.DANGER if error else Th.SUCCESS
        t  = QLabel(f"  {'✕' if error else '✓'}  {msg}", self)
        t.setStyleSheet(f"background:{bg}; color:white; border-radius:8px; padding:10px 16px; font-size:12px; font-weight:600;")
        t.adjustSize()
        t.move((self.width() - t.width()) // 2, self.height() - 56)
        t.show(); t.raise_()
        QTimer.singleShot(2800, t.deleteLater)
