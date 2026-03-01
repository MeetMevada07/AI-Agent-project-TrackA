# ============================================================
# tools/stock_tools.py
# Financial data tools using yfinance — stock prices, indicators
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from cachetools import TTLCache, cached
from typing import Optional
from config.settings import settings

# In-memory cache: max 100 entries, 5-minute TTL
_cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL_SECONDS)


def _cache_key(*args):
    return str(args)


def get_stock_price(symbol: str) -> dict:
    """
    Fetch current stock price and basic info for an Indian stock.
    
    Args:
        symbol: Stock symbol e.g. 'RELIANCE.NS', 'TCS.NS'
    
    Returns:
        dict with price, change, volume, market cap etc.
    """
    key = f"price_{symbol}"
    if key in _cache:
        return _cache[key]

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Get latest 2 days to calculate change
        hist = ticker.history(period="2d")
        if hist.empty:
            return {"error": f"No data found for {symbol}. Check symbol format (e.g., RELIANCE.NS)"}

        current_price = float(hist["Close"].iloc[-1])
        prev_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100 if prev_price else 0

        result = {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "current_price": round(current_price, 2),
            "previous_close": round(prev_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "pb_ratio": info.get("priceToBook", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": "INR",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        }

        _cache[key] = result
        return result

    except Exception as e:
        return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}


def get_historical_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for charting and technical analysis.
    
    Args:
        symbol: Stock symbol
        period: Time period — '1mo', '3mo', '6mo', '1y', '2y', '5y'
    
    Returns:
        DataFrame with OHLCV columns
    """
    key = f"hist_{symbol}_{period}"
    if key in _cache:
        return _cache[key]

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            return pd.DataFrame()

        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].round(2)
        _cache[key] = df
        return df

    except Exception as e:
        return pd.DataFrame()


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to historical DataFrame.
    
    Indicators added:
    - SMA 20, SMA 50 (Simple Moving Averages)
    - EMA 20 (Exponential Moving Average)
    - RSI 14 (Relative Strength Index)
    - MACD + Signal + Histogram
    - Bollinger Bands (Upper, Lower)
    
    Args:
        df: OHLCV DataFrame from get_historical_data()
    
    Returns:
        DataFrame with all indicators appended
    """
    if df.empty:
        return df

    close = df["Close"]

    # ── Moving Averages ─────────────────────────────────────
    df["SMA_20"] = close.rolling(window=20).mean().round(2)
    df["SMA_50"] = close.rolling(window=50).mean().round(2)
    df["EMA_20"] = close.ewm(span=20, adjust=False).mean().round(2)

    # ── RSI ─────────────────────────────────────────────────
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = (100 - (100 / (1 + rs))).round(2)

    # ── MACD ────────────────────────────────────────────────
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = (ema12 - ema26).round(2)
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean().round(2)
    df["MACD_Hist"] = (df["MACD"] - df["MACD_Signal"]).round(2)

    # ── Bollinger Bands ──────────────────────────────────────
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["BB_Upper"] = (sma20 + 2 * std20).round(2)
    df["BB_Lower"] = (sma20 - 2 * std20).round(2)

    return df


def get_fundamental_analysis(symbol: str) -> dict:
    """
    Extract fundamental analysis metrics for Indian stocks.
    
    Covers: P/E, P/B, EPS, revenue growth, debt/equity,
    return on equity, current ratio, etc.
    """
    key = f"fundamental_{symbol}"
    if key in _cache:
        return _cache[key]

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        def safe_round(val, decimals=2):
            try:
                return round(float(val), decimals)
            except (TypeError, ValueError):
                return "N/A"

        result = {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            # Valuation
            "pe_ratio": safe_round(info.get("trailingPE")),
            "forward_pe": safe_round(info.get("forwardPE")),
            "pb_ratio": safe_round(info.get("priceToBook")),
            "ps_ratio": safe_round(info.get("priceToSalesTrailing12Months")),
            "ev_ebitda": safe_round(info.get("enterpriseToEbitda")),
            # Growth & Profitability
            "eps": safe_round(info.get("trailingEps")),
            "eps_growth": safe_round(info.get("earningsGrowth")),
            "revenue_growth": safe_round(info.get("revenueGrowth")),
            "profit_margins": safe_round(info.get("profitMargins")),
            "roe": safe_round(info.get("returnOnEquity")),
            "roa": safe_round(info.get("returnOnAssets")),
            # Financial Health
            "debt_to_equity": safe_round(info.get("debtToEquity")),
            "current_ratio": safe_round(info.get("currentRatio")),
            "quick_ratio": safe_round(info.get("quickRatio")),
            # Dividends
            "dividend_yield": safe_round(info.get("dividendYield")),
            "payout_ratio": safe_round(info.get("payoutRatio")),
            # Market
            "market_cap_cr": safe_round((info.get("marketCap") or 0) / 1e7),  # in Crores
            "beta": safe_round(info.get("beta")),
            "52_week_high": safe_round(info.get("fiftyTwoWeekHigh")),
            "52_week_low": safe_round(info.get("fiftyTwoWeekLow")),
        }

        _cache[key] = result
        return result

    except Exception as e:
        return {"error": f"Failed to fetch fundamentals for {symbol}: {str(e)}"}


def compare_stocks(symbols: list) -> pd.DataFrame:
    """
    Compare multiple Indian stocks side-by-side.
    
    Args:
        symbols: List of stock symbols e.g. ['TCS.NS', 'INFY.NS', 'WIPRO.NS']
    
    Returns:
        DataFrame comparing key metrics across stocks
    """
    data = []
    for symbol in symbols:
        price_data = get_stock_price(symbol)
        fund_data = get_fundamental_analysis(symbol)

        if "error" not in price_data:
            data.append({
                "Symbol": symbol,
                "Company": price_data.get("company_name", symbol)[:20],
                "Price (₹)": price_data.get("current_price"),
                "Change %": price_data.get("change_pct"),
                "P/E": fund_data.get("pe_ratio"),
                "P/B": fund_data.get("pb_ratio"),
                "ROE %": fund_data.get("roe"),
                "D/E": fund_data.get("debt_to_equity"),
                "Mkt Cap (Cr)": fund_data.get("market_cap_cr"),
                "Div Yield %": fund_data.get("dividend_yield"),
            })

    return pd.DataFrame(data) if data else pd.DataFrame()


def calculate_tax_implications(buy_price: float, sell_price: float,
                                quantity: int, holding_days: int) -> dict:
    """
    Calculate Indian capital gains tax (LTCG / STCG) as per Indian tax law.
    
    Rules (as of FY 2024-25):
    - STCG (< 12 months): 20% flat
    - LTCG (≥ 12 months): 12.5% on gains exceeding ₹1.25 lakh exemption
    
    Args:
        buy_price: Purchase price per share (₹)
        sell_price: Selling price per share (₹)
        quantity: Number of shares
        holding_days: Days between buy and sell
    
    Returns:
        dict with gain amount, tax type, tax payable
    """
    total_buy = buy_price * quantity
    total_sell = sell_price * quantity
    gross_gain = total_sell - total_buy
    gain_per_share = sell_price - buy_price

    if holding_days < 365:
        # Short-Term Capital Gain — 20%
        tax_rate = 0.20
        tax_type = "STCG (Short-Term Capital Gain)"
        tax_payable = max(gross_gain * tax_rate, 0)
        exemption = 0
    else:
        # Long-Term Capital Gain — 12.5% above ₹1.25 lakh exemption
        tax_rate = 0.125
        tax_type = "LTCG (Long-Term Capital Gain)"
        exemption = 125000  # ₹1.25 lakh
        taxable_gain = max(gross_gain - exemption, 0)
        tax_payable = taxable_gain * tax_rate

    return {
        "symbol_buy_price": buy_price,
        "sell_price": sell_price,
        "quantity": quantity,
        "total_investment": round(total_buy, 2),
        "total_proceeds": round(total_sell, 2),
        "gross_gain_loss": round(gross_gain, 2),
        "holding_days": holding_days,
        "tax_type": tax_type,
        "tax_rate_pct": tax_rate * 100,
        "ltcg_exemption": exemption,
        "tax_payable": round(tax_payable, 2),
        "net_gain_after_tax": round(gross_gain - tax_payable, 2),
        "return_pct": round((gross_gain / total_buy) * 100, 2) if total_buy else 0,
    }


def calculate_sip(monthly_amount: float, annual_return_pct: float,
                  years: int) -> dict:
    """
    Calculate SIP (Systematic Investment Plan) returns.
    
    Uses standard SIP formula:
    M = P × {[(1 + r)^n - 1] / r} × (1 + r)
    where r = monthly rate, n = number of months
    
    Args:
        monthly_amount: Monthly SIP amount in ₹
        annual_return_pct: Expected annual return (e.g., 12 for 12%)
        years: Investment duration in years
    
    Returns:
        dict with invested amount, estimated returns, wealth gained
    """
    r = annual_return_pct / 100 / 12  # Monthly rate
    n = years * 12  # Total months

    if r == 0:
        future_value = monthly_amount * n
    else:
        future_value = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)

    total_invested = monthly_amount * n
    wealth_gained = future_value - total_invested
    absolute_return = (wealth_gained / total_invested) * 100

    # Year-by-year breakdown
    yearly_data = []
    for year in range(1, years + 1):
        n_yr = year * 12
        if r == 0:
            fv_yr = monthly_amount * n_yr
        else:
            fv_yr = monthly_amount * (((1 + r) ** n_yr - 1) / r) * (1 + r)
        yearly_data.append({
            "year": year,
            "invested": round(monthly_amount * n_yr, 2),
            "value": round(fv_yr, 2),
        })

    return {
        "monthly_sip": monthly_amount,
        "annual_return_pct": annual_return_pct,
        "years": years,
        "total_invested": round(total_invested, 2),
        "estimated_returns": round(future_value, 2),
        "wealth_gained": round(wealth_gained, 2),
        "absolute_return_pct": round(absolute_return, 2),
        "yearly_breakdown": yearly_data,
    }
