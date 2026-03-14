# ============================================================
# utils.py
# Utility functions: market status, symbol validation, PDF export
# ============================================================

import re
import io
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from config.settings import settings


# ── Market Status ─────────────────────────────────────────────

def is_market_open() -> dict:
    """
    Check if Indian stock market (NSE/BSE) is currently open.
    
    Market hours: Monday–Friday, 9:15 AM – 3:30 PM IST
    Excluding public holidays (simplified check)
    
    Returns:
        dict with is_open, status_message, current_time_ist
    """
    ist = ZoneInfo(settings.MARKET_TIMEZONE)
    now = datetime.now(ist)

    current_time = now.time()
    is_weekday = now.weekday() < 5  # Monday=0, Friday=4
    market_open = datetime.strptime("09:15", "%H:%M").time()
    market_close = datetime.strptime("15:30", "%H:%M").time()

    is_open = (is_weekday and
               market_open <= current_time <= market_close)

    if not is_weekday:
        msg = f"🔴 Market CLOSED — Weekend ({now.strftime('%A')})"
    elif current_time < market_open:
        msg = f"🟡 Pre-market — Opens at 9:15 AM IST"
    elif current_time > market_close:
        msg = f"🔴 Market CLOSED — Post-market (closed at 3:30 PM)"
    else:
        msg = f"🟢 Market OPEN — Closes at 3:30 PM IST"

    return {
        "is_open": is_open,
        "status": msg,
        "current_time_ist": now.strftime("%I:%M %p IST, %a %d %b %Y"),
    }


# ── Symbol Validation ─────────────────────────────────────────

def validate_symbol(symbol: str) -> tuple[bool, str]:
    """
    Validate and normalize an Indian stock symbol.

    Rules:
    * Accept only NSE (.NS) or BSE (.BO) suffixes when provided.
    * If no suffix is given, default to NSE and verify the ticker exists.
    * Popular stocks configured in settings are always allowed.
    * Any other suffix or format is rejected.

    Args:
        symbol: Raw user input e.g. 'reliance', 'TCS', 'RELIANCE.NS'

    Returns:
        (is_valid: bool, normalized_symbol: str)
    """
    if not symbol or not isinstance(symbol, str):
        return False, "Empty symbol"

    symbol = symbol.strip().upper().replace(" ", "")

    # if user explicitly specified a suffix
    if "." in symbol:
        parts = symbol.split(".")
        if len(parts) != 2:
            return False, f"Invalid symbol format: {symbol}"
        base, suffix = parts
        suffix = suffix.upper()
        if suffix not in ("NS", "BO"):
            return False, "Only NSE (.NS) or BSE (.BO) symbols are supported."
        # basic pattern check on base
        if not re.match(r"^[A-Z0-9\-&]+$", base):
            return False, f"Invalid symbol format: {symbol}"
        normalized = f"{base}.{suffix}"
        return True, normalized

    # without suffix: look in popular stocks first
    for key in settings.POPULAR_STOCKS:
        base = key.split(".")[0]
        if base == symbol:
            return True, key

    # allow generic alphanumeric names but verify they exist on NSE
    if re.match(r"^[A-Z0-9\-&]+$", symbol):
        candidate = f"{symbol}.NS"
        # perform a quick existence check using yfinance via get_stock_price
        try:
            from tools.stock_tools import get_stock_price
            info = get_stock_price(candidate)
            if info.get("error"):
                return False, f"Symbol '{symbol}' not found on NSE."
        except Exception:
            # if price check fails for some reason, assume invalid
            return False, f"Symbol '{symbol}' not found"
        return True, candidate

    return False, f"Invalid symbol format: {symbol}"


def format_inr(amount: float, compact: bool = False) -> str:
    """
    Format a number in Indian Rupee notation.
    
    Args:
        amount: Numeric amount
        compact: Use Lakhs/Crores notation if True
    
    Returns:
        Formatted string e.g. '₹1,23,456.78' or '₹12.3 Cr'
    """
    if amount is None or amount == "N/A":
        return "N/A"

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "N/A"

    if compact:
        if abs(amount) >= 1e7:
            return f"₹{amount/1e7:.2f} Cr"
        elif abs(amount) >= 1e5:
            return f"₹{amount/1e5:.2f} L"
        else:
            return f"₹{amount:,.2f}"

    # Indian number formatting (2,2,3 grouping)
    is_negative = amount < 0
    amount = abs(amount)
    integer_part = int(amount)
    decimal_part = round(amount - integer_part, 2)

    # Convert to Indian format
    s = str(integer_part)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = [rest[max(0, i-2):i] for i in range(len(rest), 0, -2)][::-1]
        s = ",".join(groups) + "," + last3

    decimal_str = f"{decimal_part:.2f}"[1:]  # '.XX'
    result = f"{'−' if is_negative else ''}₹{s}{decimal_str}"
    return result


def get_color_for_change(value: float) -> str:
    """Return green/red/gray color string based on positive/negative value."""
    if value > 0:
        return "green"
    elif value < 0:
        return "red"
    return "gray"


# ── PDF Export ────────────────────────────────────────────────

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch


from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime


from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from datetime import datetime


def export_analysis_to_pdf(symbol, company_name,
                           price_data, fundamental_data,
                           ai_analysis):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=30,
    )

    elements = []
    styles = getSampleStyleSheet()

    # ================= TITLE STYLING =================
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#0d47a1"),  # Deep Blue
        alignment=1,
        spaceAfter=4
    )

    symbol_style = ParagraphStyle(
        'SymbolStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#666666"),
        alignment=1,
        spaceAfter=10
    )

    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#1a237e"),
        spaceAfter=6
    )

    normal_style = styles["Normal"]

    # ================= TITLE =================
    elements.append(Paragraph(company_name, company_style))
    elements.append(Paragraph(f"({symbol})", symbol_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}",
        styles["Italic"]
    ))
    elements.append(Spacer(1, 20))

    # ================= PRICE SECTION =================
    elements.append(Paragraph("Current Market Snapshot", section_style))
    elements.append(Spacer(1, 8))

    def safe_rs(val):
        if val in [None, "N/A"]:
            return "N/A"
        return f"Rs {val}"

    price_items = [
        ["Current Price", safe_rs(price_data.get('current_price'))],
        ["Change",
         f"{safe_rs(price_data.get('change'))} "
         f"({price_data.get('change_pct', 0):.2f}%)"],
        ["52 Week High", safe_rs(price_data.get('52_week_high'))],
        ["52 Week Low", safe_rs(price_data.get('52_week_low'))],
        ["Market Cap",
         f"{safe_rs(fundamental_data.get('market_cap_cr'))} Cr"],
    ]

    price_table = Table(price_items, colWidths=[2.8 * inch, 3.2 * inch])
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [colors.whitesmoke, colors.white]),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    elements.append(price_table)
    elements.append(Spacer(1, 25))

    # ================= FUNDAMENTALS =================
    elements.append(Paragraph("Fundamental Overview", section_style))
    elements.append(Spacer(1, 8))

    fund_items = [
        ["P/E Ratio", fundamental_data.get("pe_ratio", "N/A")],
        ["P/B Ratio", fundamental_data.get("pb_ratio", "N/A")],
        ["ROE", fundamental_data.get("roe", "N/A")],
        ["Debt/Equity", fundamental_data.get("debt_to_equity", "N/A")],
        ["EPS", fundamental_data.get("eps", "N/A")],
        ["Dividend Yield", fundamental_data.get("dividend_yield", "N/A")],
    ]

    fund_table = Table(fund_items, colWidths=[2.8 * inch, 3.2 * inch])
    fund_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [colors.whitesmoke, colors.white]),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    elements.append(fund_table)
    elements.append(Spacer(1, 25))

    # ================= AI ANALYSIS =================
    elements.append(Paragraph("AI Investment Analysis", section_style))
    elements.append(Spacer(1, 8))

    clean_text = ai_analysis.replace("₹", "Rs")
    clean_text = clean_text.replace("**", "")
    clean_text = clean_text.replace("•", "-")

    for line in clean_text.split("\n"):
        if line.strip():
            elements.append(Paragraph(line, normal_style))
            elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 30))

    # ================= DISCLAIMER =================
    elements.append(Paragraph(
        "<b>Disclaimer:</b> This report is for educational purposes only. "
        "Not SEBI-registered financial advice.",
        styles["Italic"]
    ))

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()
