"""
app/utils/theme.py
------------------
PosFlow Design System — all colors, typography, spacing, and
reusable widget factories in one place.

Import from any view:
    from app.utils.theme import Theme, Th
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFrame,
    QGraphicsDropShadowEffect, QComboBox, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class Theme:
    # ── Palette ──────────────────────────────────────────────
    PRIMARY       = "#1B3F6E"
    PRIMARY_HOVER = "#2563A8"
    PRIMARY_LIGHT = "#EBF2FB"
    PRIMARY_DIM   = "#6B8FBF"

    SUCCESS       = "#059669"
    SUCCESS_LIGHT = "#ECFDF5"
    DANGER        = "#DC2626"
    DANGER_LIGHT  = "#FEF2F2"
    WARNING       = "#D97706"
    WARNING_LIGHT = "#FFFBEB"
    PURPLE        = "#7C3AED"
    PURPLE_LIGHT  = "#F5F3FF"

    # ── Neutrals ─────────────────────────────────────────────
    INK_900  = "#0F172A"
    INK_700  = "#334155"
    INK_500  = "#64748B"
    INK_300  = "#94A3B8"
    INK_100  = "#F1F5F9"
    INK_50   = "#F8FAFC"
    WHITE    = "#FFFFFF"
    DIVIDER  = "#F1F5F9"

    # ── Typography ───────────────────────────────────────────
    FONT       = "Inter, Segoe UI, Arial"
    FONT_MONO  = "JetBrains Mono, Courier New, monospace"

    # ── Shadows ──────────────────────────────────────────────
    @staticmethod
    def shadow(blur=16, dy=2, alpha=10):
        s = QGraphicsDropShadowEffect()
        s.setBlurRadius(blur)
        s.setOffset(0, dy)
        s.setColor(QColor(15, 23, 42, alpha))
        return s

    @staticmethod
    def shadow_lg():
        return Theme.shadow(32, 6, 18)

    # ── Buttons ──────────────────────────────────────────────
    @staticmethod
    def btn_primary(text, h=44, w=None, fs=13) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(h)
        if w:
            b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: {fs}px;
                font-weight: 600;
                padding: 0 20px;
                letter-spacing: 0.2px;
            }}
            QPushButton:hover   {{ background: {Theme.PRIMARY_HOVER}; }}
            QPushButton:pressed {{ background: #163260; }}
            QPushButton:disabled{{
                background: {Theme.INK_100};
                color: {Theme.INK_300};
            }}
        """)
        return b

    @staticmethod
    def btn_secondary(text, h=44, w=None, fs=13) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(h)
        if w:
            b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.INK_100};
                color: {Theme.INK_700};
                border: none;
                border-radius: 8px;
                font-size: {fs}px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: #E2E8F0; }}
            QPushButton:disabled {{ color: {Theme.INK_300}; }}
        """)
        return b

    @staticmethod
    def btn_success(text, h=44, w=None, fs=13) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(h)
        if w:
            b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.SUCCESS};
                color: white; border: none;
                border-radius: 8px;
                font-size: {fs}px; font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background: #047857; }}
            QPushButton:disabled {{ background: {Theme.INK_100}; color: {Theme.INK_300}; }}
        """)
        return b

    @staticmethod
    def btn_danger(text, h=36, w=None, fs=12) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(h)
        if w:
            b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.DANGER_LIGHT};
                color: {Theme.DANGER};
                border: none; border-radius: 7px;
                font-size: {fs}px; font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background: #FEE2E2; }}
        """)
        return b

    @staticmethod
    def btn_ghost(text, color=None, h=36, w=None, fs=12) -> QPushButton:
        c = color or Theme.PRIMARY
        b = QPushButton(text)
        b.setFixedHeight(h)
        if w:
            b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c};
                border: 1.5px solid {c};
                border-radius: 7px;
                font-size: {fs}px; font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background: {Theme.PRIMARY_LIGHT}; }}
        """)
        return b

    # ── Inputs ───────────────────────────────────────────────
    @staticmethod
    def input_style(fs=13) -> str:
        return f"""
            QLineEdit {{
                background: {Theme.INK_50};
                border: 1.5px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 14px;
                font-size: {fs}px;
                color: {Theme.INK_900};
            }}
            QLineEdit:focus {{
                border-color: {Theme.PRIMARY};
                background: white;
            }}
            QLineEdit:read-only {{
                background: {Theme.INK_100};
                color: {Theme.INK_300};
            }}
        """

    @staticmethod
    def combo_style(fs=13) -> str:
        return f"""
            QComboBox {{
                background: {Theme.INK_50};
                border: 1.5px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 14px;
                font-size: {fs}px;
                color: {Theme.INK_900};
            }}
            QComboBox:focus {{ border-color: {Theme.PRIMARY}; background: white; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                border: 1px solid #E2E8F0;
                background: white;
                selection-background-color: {Theme.PRIMARY_LIGHT};
                selection-color: {Theme.PRIMARY};
                font-size: {fs}px;
                padding: 4px;
                outline: none;
            }}
        """

    @staticmethod
    def spin_style(fs=13) -> str:
        return f"""
            QDoubleSpinBox, QSpinBox {{
                background: {Theme.INK_50};
                border: 1.5px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 14px;
                font-size: {fs}px;
                color: {Theme.INK_900};
            }}
            QDoubleSpinBox:focus, QSpinBox:focus {{
                border-color: {Theme.PRIMARY};
                background: white;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QSpinBox::up-button,       QSpinBox::down-button {{ width: 0; }}
        """

    # ── Labels ───────────────────────────────────────────────
    @staticmethod
    def label(text, size=13, bold=False,
              color=None, center=False) -> QLabel:
        c = color or Theme.INK_700
        l = QLabel(text)
        l.setStyleSheet(
            f"font-size:{size}px; font-weight:{'700' if bold else '400'};"
            f" color:{c}; background:transparent;"
        )
        if center:
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return l

    @staticmethod
    def field_label(text) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{Theme.INK_300};"
            " letter-spacing:0.6px; text-transform:uppercase;"
            " background:transparent;"
        )
        return l

    # ── Pill badges ──────────────────────────────────────────
    @staticmethod
    def pill(text, fg, bg, fs=11) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            f"color:{fg}; background:{bg};"
            f" border-radius:20px; padding:3px 10px;"
            f" font-size:{fs}px; font-weight:600;"
        )
        l.setFixedHeight(22)
        return l

    @staticmethod
    def pill_success(text="In Stock"):
        return Theme.pill(text, Theme.SUCCESS, Theme.SUCCESS_LIGHT)

    @staticmethod
    def pill_warning(text="Low Stock"):
        return Theme.pill(text, Theme.WARNING, Theme.WARNING_LIGHT)

    @staticmethod
    def pill_danger(text="Out of Stock"):
        return Theme.pill(text, Theme.DANGER, Theme.DANGER_LIGHT)

    @staticmethod
    def pill_primary(text):
        return Theme.pill(text, Theme.PRIMARY, Theme.PRIMARY_LIGHT)

    @staticmethod
    def pill_muted(text):
        return Theme.pill(text, Theme.INK_500, Theme.INK_100)

    # ── Divider ──────────────────────────────────────────────
    @staticmethod
    def divider() -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background:{Theme.DIVIDER}; border:none;")
        return f

    # ── Scroll bar CSS ───────────────────────────────────────
    SCROLLBAR = """
        QScrollBar:vertical {
            width: 4px; background: transparent; margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1; border-radius: 2px; min-height: 30px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { height: 4px; background: transparent; }
        QScrollBar::handle:horizontal {
            background: #CBD5E1; border-radius: 2px;
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal { width: 0; }
    """

    # ── Tab button ───────────────────────────────────────────
    @staticmethod
    def tab_btn(text, w=140) -> QPushButton:
        b = QPushButton(text)
        b.setCheckable(True)
        b.setFixedHeight(48)
        b.setFixedWidth(w)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.INK_300};
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover   {{ color: {Theme.INK_700}; }}
            QPushButton:checked {{
                color: {Theme.PRIMARY};
                border-bottom: 2px solid {Theme.PRIMARY};
            }}
        """)
        return b

    # ── Global app stylesheet ────────────────────────────────
    APP_STYLE = f"""
        QWidget {{
            font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
        }}
        QToolTip {{
            background: {INK_900};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 12px;
        }}
    """


# Convenience alias
Th = Theme
