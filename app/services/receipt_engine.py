"""
app/services/receipt_engine.py
"""
import re, os, textwrap, logging
from typing import List

logger = logging.getLogger(__name__)

FONT_MONO_R = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
FONT_MONO_B = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
if not os.path.exists(FONT_MONO_R):
    FONT_MONO_R = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

PAPER_CHARS = 40
COL_QTY     = 4
COL_PRICE   = 9
COL_TOTAL   = 9
COL_ITEM    = PAPER_CHARS - COL_QTY - COL_PRICE - COL_TOTAL - 3
CURRENCY_SYM = "KES"

def _clean_name(name: str) -> str:
    if not name:
        return ""
    mojibake = {
        "ê":"e","ö":"o","ß":"ss","é":"e","è":"e","à":"a",
        "â":"a","î":"i","ô":"o","û":"u","ü":"u","ä":"a",
        "ï":"i","ç":"c","ñ":"n",
    }
    for bad, good in mojibake.items():
        name = name.replace(bad, good)
    name = re.sub(r"\s+\d+\.\d{2}$", "", name.strip())
    name = re.sub(r"\s+0{2,}$", "", name.strip())
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name

def _clean_items(items: list) -> list:
    return [
        {**item, "name": _clean_name(item.get("name", ""))}
        for item in items if item.get("name")
    ]

def _fmt_money(amount: float) -> str:
    return f"{amount:,.2f}"

def _layout_item_row(name, qty, unit_price, line_total) -> List[str]:
    qty_str   = f"{qty:g}x".rjust(COL_QTY)
    price_str = _fmt_money(unit_price).rjust(COL_PRICE)
    total_str = _fmt_money(line_total).rjust(COL_TOTAL)
    wrapped   = textwrap.wrap(name, width=COL_ITEM) or [""]
    lines = []
    for i, part in enumerate(wrapped):
        if i == 0:
            lines.append(f"{part.ljust(COL_ITEM)} {qty_str} {price_str} {total_str}")
        else:
            blank = " " * (COL_QTY + COL_PRICE + COL_TOTAL + 3)
            lines.append(f"{part.ljust(COL_ITEM)}{blank}")
    return lines

def _col_header() -> str:
    return (f"{'ITEM'.ljust(COL_ITEM)} {'QTY'.rjust(COL_QTY)}"
            f" {'PRICE'.rjust(COL_PRICE)} {'TOTAL'.rjust(COL_TOTAL)}")

def _rule(char="─") -> str:
    return char * PAPER_CHARS

def _centre(text: str) -> str:
    return text.center(PAPER_CHARS)

def _kv(label: str, value: str) -> str:
    label_w = 18
    val_w   = PAPER_CHARS - label_w
    return f"{label:<{label_w}}{value:>{val_w}}"

def build_receipt_lines(sale_data: dict) -> List[str]:
    d        = sale_data
    currency = d.get("currency", CURRENCY_SYM)
    items    = _clean_items(d.get("items", []))
    lines: List[str] = []

    biz = d.get("business_name", "MY BUSINESS").upper()
    lines.append(_centre(biz))
    for addr in d.get("address_lines", []):
        lines.append(_centre(addr))
    lines.append("")
    lines.append(_centre("RECEIPT"))
    lines.append(_rule())
    lines.append(_kv("Receipt No.", d.get("receipt_number", "—")))
    lines.append(_kv("Date",        d.get("date_str", "—")))
    lines.append(_kv("Cashier",     d.get("cashier_name", "—")))
    if d.get("payment_ref"):
        lines.append(_kv("Ref.", d["payment_ref"]))
    lines.append(_rule())
    lines.append(_col_header())
    lines.append(_rule("─"))

    for item in items:
        lines.extend(_layout_item_row(
            item.get("name",""), item.get("quantity",1),
            item.get("unit_price",0), item.get("line_total",0),
        ))

    lines.append(_rule())

    subtotal = d.get("subtotal", 0)
    discount = d.get("discount", 0)
    total    = d.get("total", 0)

    if discount > 0:
        lines.append(_kv("Subtotal:", f"{currency} {_fmt_money(subtotal)}"))
        lines.append(_kv("Discount:", f"- {currency} {_fmt_money(discount)}"))
        lines.append(_rule("─"))

    lines.append(f"**{_kv('TOTAL:', f'{currency} {_fmt_money(total)}')}")
    lines.append(_rule())
    lines.append(_kv("Payment:", d.get("payment_method","Cash").title()))
    if d.get("tendered") is not None:
        lines.append(_kv("Tendered:", f"{currency} {_fmt_money(d['tendered'])}"))
    if d.get("change") is not None and d["change"] >= 0:
        lines.append(_kv("Change:", f"{currency} {_fmt_money(d['change'])}"))

    footer = d.get("receipt_footer", "")
    if footer:
        lines.append("")
        lines.append(_rule("─"))
        lines.append("")
        for part in textwrap.wrap(footer, PAPER_CHARS):
            lines.append(_centre(part))
    lines.append("")
    return lines

def render_pdf(sale_data: dict, output_path: str) -> str:
    from reportlab.pdfbase         import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen          import canvas as pdfcanvas
    from reportlab.lib.units       import mm

    try:
        pdfmetrics.registerFont(TTFont("LMMono",      FONT_MONO_R))
        pdfmetrics.registerFont(TTFont("LMMono-Bold", FONT_MONO_B))
        FONT_R = "LMMono"
        FONT_B = "LMMono-Bold"
    except Exception:
        FONT_R = "Courier"
        FONT_B = "Courier-Bold"

    FONT_SIZE   = 8.5
    LINE_HEIGHT = FONT_SIZE * 1.35
    PAGE_W      = 72 * mm
    MARGIN_X    = 5 * mm
    MARGIN_Y    = 6 * mm

    lines  = build_receipt_lines(sale_data)
    PAGE_H = (len(lines) * LINE_HEIGHT) + (MARGIN_Y * 2) + 4 * mm

    c = pdfcanvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))
    y = PAGE_H - MARGIN_Y

    for line in lines:
        bold = line.startswith("**")
        text = line[2:] if bold else line
        c.setFont(FONT_B if bold else FONT_R, FONT_SIZE)
        c.drawString(MARGIN_X, y - FONT_SIZE, text)
        y -= LINE_HEIGHT

    c.save()
    return output_path

ESC = b"\x1b"
GS  = b"\x1d"
LF  = b"\x0a"
INIT        = ESC + b"@"
BOLD_ON     = ESC + b"\x45\x01"
BOLD_OFF    = ESC + b"\x45\x00"
PARTIAL_CUT = GS  + b"\x56\x42\x00"

def render_escpos(sale_data: dict) -> bytes:
    lines  = build_receipt_lines(sale_data)
    output = bytearray()
    output += INIT
    for line in lines:
        bold = line.startswith("**")
        text = line[2:] if bold else line
        if bold:
            output += BOLD_ON
        output += text.encode("ascii", errors="replace") + LF
        if bold:
            output += BOLD_OFF
    output += PARTIAL_CUT
    return bytes(output)

def send_to_printer(sale_data: dict, port: str = "auto") -> bool:
    raw = render_escpos(sale_data)
    if port == "auto":
        candidates = ["/dev/usb/lp0","/dev/usb/lp1","/dev/lp0","/dev/lp1"]
        port = next((p for p in candidates if os.path.exists(p)), None)
        if not port:
            return False
    try:
        with open(port, "wb") as f:
            f.write(raw)
        return True
    except Exception as e:
        logger.error("Printer error: %s", e)
        return False
