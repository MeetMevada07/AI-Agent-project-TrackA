# ============================================================
# tools/stock_tools.py
# Financial data tools using yfinance — stock prices, indicators
# ============================================================

import logging
import yfinance as yf
import pandas as pd
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from cachetools import TTLCache
from typing import Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

_cache = TTLCache(maxsize=200, ttl=settings.CACHE_TTL_SECONDS)


def _get_st_cache_data():
    try:
        import streamlit as st
        def st_cache_wrapper(**kwargs):
            kwargs["show_spinner"] = False
            return st.cache_data(**kwargs)
        return st_cache_wrapper
    except ImportError:
        def _noop(**kwargs):
            def decorator(fn):
                return fn
            return decorator
        return _noop


# -------------------------------------------------------------
# Helper: Retry wrapper for yfinance
# -------------------------------------------------------------
def fetch_with_retry(symbol, retries=2):
    """Fast retry — no sleep, yfinance batch where possible."""
    periods = ["5d", "1mo"]
    for i in range(retries):
        for period in periods:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty:
                    return ticker, hist
            except Exception:
                pass
    return None, pd.DataFrame()


def batch_fetch_prices(symbols: List[str]) -> dict:
    """
    Fetch prices for multiple symbols in parallel using ThreadPoolExecutor.
    Returns dict: {symbol -> price_dict_or_error_dict}
    """
    results = {}
    # Check cache first
    to_fetch = []
    for sym in symbols:
        key = f"price_{sym}"
        if key in _cache:
            results[sym] = _cache[key]
        else:
            to_fetch.append(sym)

    if not to_fetch:
        return results

    # Try yfinance bulk download first (much faster for multiple symbols)
    try:
        bulk = yf.download(
            to_fetch,
            period="5d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

        for sym in to_fetch:
            try:
                if len(to_fetch) == 1:
                    hist = bulk
                else:
                    hist = bulk[sym] if sym in bulk.columns.get_level_values(0) else pd.DataFrame()

                if hist is None or hist.empty:
                    results[sym] = {"error": f"No data for {sym}"}
                    continue

                hist = hist.dropna(how="all")
                if hist.empty:
                    results[sym] = {"error": f"No data for {sym}"}
                    continue

                close_col = "Close" if "Close" in hist.columns else hist.columns[-1]
                current_price = float(hist[close_col].iloc[-1])
                prev_price = float(hist[close_col].iloc[-2]) if len(hist) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100 if prev_price else 0

                # fast_info for 52w data
                try:
                    ticker = yf.Ticker(sym)
                    fast = ticker.fast_info
                    week_high = getattr(fast, "year_high", "N/A")
                    week_low  = getattr(fast, "year_low", "N/A")
                    market_cap = getattr(fast, "market_cap", "N/A")
                except Exception:
                    week_high = week_low = market_cap = "N/A"

                try:
                    info = yf.Ticker(sym).info
                    company_name = info.get("longName") or info.get("shortName") or sym
                    pe_ratio = info.get("trailingPE") or info.get("forwardPE") or "N/A"
                    if isinstance(pe_ratio, float):
                        pe_ratio = round(pe_ratio, 2)
                except Exception:
                    company_name = sym
                    pe_ratio = "N/A"

                vol_col = "Volume" if "Volume" in hist.columns else None
                volume = int(hist[vol_col].iloc[-1]) if vol_col else 0

                entry = {
                    "symbol": sym,
                    "company_name": company_name,
                    "current_price": round(current_price, 2),
                    "previous_close": round(prev_price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": volume,
                    "market_cap": market_cap,
                    "52_week_high": round(week_high, 2) if isinstance(week_high, float) else week_high,
                    "52_week_low":  round(week_low, 2)  if isinstance(week_low, float) else week_low,
                    "year_high": week_high,
                    "year_low": week_low,
                    "pe_ratio": pe_ratio,
                    "currency": "INR",
                    "timestamp": now_str,
                }
                _cache[f"price_{sym}"] = entry
                results[sym] = entry
            except Exception as e:
                results[sym] = {"error": str(e)}

    except Exception:
        # Fallback: parallel individual fetches
        with ThreadPoolExecutor(max_workers=8) as ex:
            future_map = {ex.submit(get_stock_price, sym): sym for sym in to_fetch}
            for future in as_completed(future_map):
                sym = future_map[future]
                try:
                    results[sym] = future.result()
                except Exception as e:
                    results[sym] = {"error": str(e)}

    return results


# -------------------------------------------------------------
# STOCK PRICE
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=300)
def get_stock_price(symbol: str) -> dict:

    key = f"price_{symbol}"
    if key in _cache:
        return _cache[key]

    try:

        ticker, hist = fetch_with_retry(symbol)

        if hist.empty:
            return {
                "error": f"No price data found for '{symbol}'."
            }

        try:
            fast = ticker.fast_info
            market_cap = getattr(fast, "market_cap", "N/A")
            week_high = getattr(fast, "year_high", "N/A")
            week_low  = getattr(fast, "year_low", "N/A")
        except:
            market_cap = "N/A"
            week_high  = "N/A"
            week_low   = "N/A"

        try:
            info = ticker.info
            company_name = info.get("longName") or info.get("shortName") or symbol
            pe_ratio = info.get("trailingPE") or info.get("forwardPE") or "N/A"
            if isinstance(pe_ratio, float):
                pe_ratio = round(pe_ratio, 2)
        except:
            company_name = symbol
            pe_ratio = "N/A"

        current_price = float(hist["Close"].iloc[-1])
        prev_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price

        change = current_price - prev_price
        change_pct = (change / prev_price) * 100 if prev_price else 0

        result = {
            "symbol": symbol,
            "company_name": company_name,
            "current_price": round(current_price, 2),
            "previous_close": round(prev_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "market_cap": market_cap,
            "52_week_high": round(week_high, 2) if isinstance(week_high, float) else week_high,
            "52_week_low":  round(week_low, 2)  if isinstance(week_low, float)  else week_low,
            "year_high": week_high,
            "year_low": week_low,
            "pe_ratio": pe_ratio,
            "currency": "INR",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        }

        _cache[key] = result
        return result

    except Exception as e:

        logger.error("get_stock_price(%s) failed: %s", symbol, e)

        return {
            "error": f"Unable to fetch data for {symbol}"
        }




# -------------------------------------------------------------
# HISTORICAL DATA
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=300)
def get_historical_data(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:

    key = f"hist_{symbol}_{period}_{interval}"
    if key in _cache:
        return _cache[key]

    try:

        ticker = yf.Ticker(symbol)

        df = ticker.history(period=period, interval=interval)

        if df.empty:
            return pd.DataFrame()

        df.index = pd.to_datetime(df.index)

        df = df[["Open", "High", "Low", "Close", "Volume"]]

        df = df.round(2)

        _cache[key] = df

        return df

    except Exception as e:

        logger.error("get_historical_data failed %s", e)

        return pd.DataFrame()


# -------------------------------------------------------------
# TECHNICAL INDICATORS
# -------------------------------------------------------------
def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    close = df["Close"]

    df["SMA_20"] = close.rolling(20).mean()
    df["SMA_50"] = close.rolling(50).mean()

    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()

    df["BB_Upper"] = sma20 + 2 * std20
    df["BB_Lower"] = sma20 - 2 * std20

    return df.round(2)


# -------------------------------------------------------------
# FUNDAMENTAL ANALYSIS
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=600)
def get_fundamental_analysis(symbol: str) -> dict:

    key = f"fundamental_{symbol}"

    if key in _cache:
        return _cache[key]

    try:

        ticker = yf.Ticker(symbol)

        # ticker.info has full fundamental data (fast_info is too limited)
        try:
            info = ticker.info
        except Exception:
            info = {}

        def safe_val(key_name, default="N/A"):
            """Safely get a value from info dict, return default if None/missing."""
            val = info.get(key_name, default)
            if val is None or val == "" or val == 0 and key_name not in ("beta",):
                return default
            return val

        def fmt_pct(val):
            """Convert decimal to percentage float, e.g. 0.15 -> 0.15 (kept as float for UI formatting)."""
            if isinstance(val, (int, float)):
                return round(float(val), 4)
            return "N/A"

        def fmt_round(val, decimals=2):
            if isinstance(val, (int, float)):
                return round(float(val), decimals)
            return "N/A"

        # Market cap in Crores (INR)
        market_cap_raw = info.get("marketCap", None)
        market_cap_cr = "N/A"
        if market_cap_raw and isinstance(market_cap_raw, (int, float)) and market_cap_raw > 0:
            market_cap_cr = f"₹{market_cap_raw / 1e7:,.0f} Cr"

        # P/E Ratio - try trailingPE first, then forwardPE
        pe = info.get("trailingPE") or info.get("forwardPE")
        pe_ratio = fmt_round(pe) if pe else "N/A"

        # P/B Ratio
        pb = info.get("priceToBook")
        pb_ratio = fmt_round(pb) if pb else "N/A"

        # EPS (Trailing twelve months)
        eps_raw = info.get("trailingEps") or info.get("forwardEps")
        eps = fmt_round(eps_raw) if eps_raw else "N/A"

        # ROE and ROA (yfinance gives these as decimals e.g. 0.15 = 15%)
        roe_raw = info.get("returnOnEquity")
        roa_raw = info.get("returnOnAssets")
        roe = fmt_pct(roe_raw) if roe_raw is not None else "N/A"
        roa = fmt_pct(roa_raw) if roa_raw is not None else "N/A"

        # Debt to Equity
        de_raw = info.get("debtToEquity")
        debt_to_equity = fmt_round(de_raw) if de_raw is not None else "N/A"

        # Dividend Yield
        div_raw = info.get("dividendYield")
        div_yield = fmt_pct(div_raw) if div_raw is not None else "N/A"

        # Beta
        beta_raw = info.get("beta")
        beta = fmt_round(beta_raw) if beta_raw is not None else "N/A"

        result = {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "eps": eps,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
            "div_yield": div_yield,
            "market_cap": market_cap_raw if market_cap_raw else "N/A",
            "market_cap_cr": market_cap_cr,
            "beta": beta,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
        }

        _cache[key] = result
        return result

    except Exception as e:

        logger.error("get_fundamental_analysis failed %s", e)

        return {
            "error": "Unable to fetch fundamentals"
        }


# -------------------------------------------------------------
# COMPARE STOCKS
# -------------------------------------------------------------
def compare_stocks(symbols: list) -> pd.DataFrame:

    data = []

    for symbol in symbols:

        price = get_stock_price(symbol)

        if "error" not in price:

            data.append({
                "Symbol": symbol,
                "Price": price["current_price"],
                "Change %": price["change_pct"]
            })

    return pd.DataFrame(data)


# -------------------------------------------------------------
# SIP CALCULATOR
# -------------------------------------------------------------
def calculate_sip(monthly_amount: float, annual_return_pct: float, years: int):

    r = annual_return_pct / 100 / 12
    n = years * 12

    if r == 0:
        future_value = monthly_amount * n
    else:
        future_value = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)

    total_invested = monthly_amount * n
    wealth_gained = future_value - total_invested
    absolute_return_pct = (wealth_gained / total_invested) * 100 if total_invested else 0

    yearly_data = []

    for year in range(1, years + 1):
        months = year * 12
        if r == 0:
            value = monthly_amount * months
        else:
            value = monthly_amount * (((1 + r) ** months - 1) / r) * (1 + r)

        yearly_data.append({
            "year": year,
            "invested": monthly_amount * months,
            "value": value
        })

    return {
        "total_invested": round(total_invested, 2),
        "estimated_returns": round(future_value, 2),
        "wealth_gained": round(wealth_gained, 2),
        "absolute_return_pct": round(absolute_return_pct, 2),
        "yearly_breakdown": yearly_data
    }

def calculate_tax_implications(buy_price: float, sell_price: float,
                                quantity: int, holding_days: int) -> dict:

    total_buy = buy_price * quantity
    total_sell = sell_price * quantity
    gross_gain = total_sell - total_buy

    # return percentage
    return_pct = (gross_gain / total_buy) * 100 if total_buy else 0

    if holding_days < 365:

        tax_rate = 0.20
        tax_type = "STCG (Short Term Capital Gain)"
        tax = max(gross_gain * tax_rate, 0)
        exemption = 0

    else:

        tax_rate = 0.125
        tax_type = "LTCG (Long Term Capital Gain)"

        exemption = 125000
        taxable_gain = max(gross_gain - exemption, 0)
        tax = taxable_gain * tax_rate

    return {
        "buy_price": buy_price,
        "sell_price": sell_price,
        "quantity": quantity,

        "total_investment": round(total_buy, 2),
        "total_proceeds": round(total_sell, 2),

        "gross_gain_loss": round(gross_gain, 2),
        "return_pct": round(return_pct, 2),

        "holding_days": holding_days,
        "tax_type": tax_type,
        "tax_rate_pct": tax_rate * 100,
        "ltcg_exemption": exemption,

        "tax_payable": round(tax, 2),
        "net_gain_after_tax": round(gross_gain - tax, 2)
    }
