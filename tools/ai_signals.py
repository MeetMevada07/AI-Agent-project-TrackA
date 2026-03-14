# ============================================================
# tools/ai_signals.py
# AI-powered signals: Buy/Hold/Sell, Market Mood, Portfolio Risk
# ============================================================

import logging
import numpy as np
import pandas as pd
from cachetools import TTLCache
from tools.stock_tools import (
    get_historical_data, calculate_technical_indicators,
    get_stock_price, get_fundamental_analysis,
)
from tools.news_tools import get_news_with_sentiment

logger = logging.getLogger(__name__)

_signal_cache = TTLCache(maxsize=100, ttl=300)


def _get_st_cache_data():
    """Lazy import so this module works outside Streamlit too."""
    try:
        import streamlit as st
        return st.cache_data
    except ImportError:
        def _noop(ttl=None):
            def decorator(fn):
                return fn
            return decorator
        return _noop


# ─────────────────────────────────────────────────────────────
# BUY / HOLD / SELL SIGNAL ENGINE
# ─────────────────────────────────────────────────────────────

@_get_st_cache_data()(ttl=300)
def get_trading_signal(symbol: str) -> dict:
    """
    Generate a Buy / Hold / Sell signal with confidence score.

    Signal is based on:
    1. MA Crossover (SMA20 vs SMA50)
    2. RSI (Relative Strength Index)
    3. MACD crossover
    4. News sentiment
    5. Price vs 52-week levels

    Returns:
        dict with signal, confidence (0-100), score_breakdown, reasoning.
        Returns dict with 'error' key on failure — never raises.
    """
    cache_key = f"signal_{symbol}"
    if cache_key in _signal_cache:
        return _signal_cache[cache_key]

    try:
        df = get_historical_data(symbol, period="6mo")
        if df.empty:
            return {"error": "No historical data available"}

        df = calculate_technical_indicators(df.copy())
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        price_data = get_stock_price(symbol)
        company_name = price_data.get("company_name", symbol) if "error" not in price_data else symbol

        scores = {}
        reasons = []

        # ── 1. MA Crossover ──────────────────────────────────
        sma20 = float(last.get("SMA_20") or 0)
        sma50 = float(last.get("SMA_50") or 0)
        prev_sma20 = float(prev.get("SMA_20") or 0)
        prev_sma50 = float(prev.get("SMA_50") or 0)
        current_price = float(last["Close"])

        if sma20 > 0 and sma50 > 0:
            if sma20 > sma50 and prev_sma20 <= prev_sma50:
                scores["ma_crossover"] = 25  # Golden cross — strong buy signal
                reasons.append("🟢 Golden Cross: SMA20 crossed above SMA50 — bullish signal")
            elif sma20 > sma50:
                scores["ma_crossover"] = 15  # Uptrend
                reasons.append("🟢 Price above SMA50 — uptrend intact")
            elif sma20 < sma50 and prev_sma20 >= prev_sma50:
                scores["ma_crossover"] = -25  # Death cross — strong sell
                reasons.append("🔴 Death Cross: SMA20 crossed below SMA50 — bearish signal")
            else:
                scores["ma_crossover"] = -10  # Downtrend
                reasons.append("🔴 SMA20 below SMA50 — downtrend in progress")
        else:
            scores["ma_crossover"] = 0

        # ── 2. RSI Signal ────────────────────────────────────
        rsi = float(last.get("RSI") or 50)
        if rsi < 30:
            scores["rsi"] = 20  # Oversold — potential buy
            reasons.append(f"🟢 RSI = {rsi:.1f} — Oversold, potential reversal upward")
        elif rsi < 45:
            scores["rsi"] = 10  # Mild bullish
            reasons.append(f"🟡 RSI = {rsi:.1f} — Mild bullish territory")
        elif rsi > 70:
            scores["rsi"] = -20  # Overbought — sell signal
            reasons.append(f"🔴 RSI = {rsi:.1f} — Overbought, risk of pullback")
        elif rsi > 60:
            scores["rsi"] = -5  # Slightly overbought
            reasons.append(f"🟡 RSI = {rsi:.1f} — Approaching overbought zone")
        else:
            scores["rsi"] = 5  # Neutral
            reasons.append(f"⚪ RSI = {rsi:.1f} — Neutral zone (30–70)")

        # ── 3. MACD ──────────────────────────────────────────
        macd = float(last.get("MACD") or 0)
        macd_signal = float(last.get("MACD_Signal") or 0)
        prev_macd = float(prev.get("MACD") or 0)
        prev_macd_signal = float(prev.get("MACD_Signal") or 0)

        if macd > macd_signal and prev_macd <= prev_macd_signal:
            scores["macd"] = 20  # Bullish crossover
            reasons.append("🟢 MACD bullish crossover — momentum building")
        elif macd > macd_signal:
            scores["macd"] = 10
            reasons.append("🟢 MACD above signal line — bullish momentum")
        elif macd < macd_signal and prev_macd >= prev_macd_signal:
            scores["macd"] = -20  # Bearish crossover
            reasons.append("🔴 MACD bearish crossover — momentum fading")
        else:
            scores["macd"] = -10
            reasons.append("🔴 MACD below signal line — bearish momentum")

        # ── 4. News Sentiment ────────────────────────────────
        try:
            news = get_news_with_sentiment(symbol, company_name)
            sentiment_score = news.get("avg_score", 0)
            if sentiment_score > 0.2:
                scores["sentiment"] = 15
                reasons.append(f"🟢 News sentiment strongly positive (score: {sentiment_score:.2f})")
            elif sentiment_score > 0.05:
                scores["sentiment"] = 8
                reasons.append(f"🟢 News sentiment mildly positive (score: {sentiment_score:.2f})")
            elif sentiment_score < -0.2:
                scores["sentiment"] = -15
                reasons.append(f"🔴 News sentiment strongly negative (score: {sentiment_score:.2f})")
            elif sentiment_score < -0.05:
                scores["sentiment"] = -8
                reasons.append(f"🔴 News sentiment mildly negative (score: {sentiment_score:.2f})")
            else:
                scores["sentiment"] = 0
                reasons.append(f"⚪ News sentiment neutral (score: {sentiment_score:.2f})")
        except Exception:
            scores["sentiment"] = 0

        # ── 5. 52-Week Position ──────────────────────────────
        if "error" not in price_data:
            high_52w = price_data.get("52_week_high")
            low_52w = price_data.get("52_week_low")
            if high_52w and low_52w and isinstance(high_52w, (int, float)):
                range_52w = high_52w - low_52w
                if range_52w > 0:
                    position_pct = (current_price - low_52w) / range_52w
                    if position_pct < 0.25:
                        scores["position"] = 15
                        reasons.append(f"🟢 Near 52-week low — potential value zone ({position_pct:.0%} of range)")
                    elif position_pct > 0.85:
                        scores["position"] = -10
                        reasons.append(f"🔴 Near 52-week high — caution zone ({position_pct:.0%} of range)")
                    else:
                        scores["position"] = 5
                        reasons.append(f"⚪ Mid-range position ({position_pct:.0%} of 52-week range)")
                    scores["position"] = scores.get("position", 0)

        # ── Compute Total Signal ─────────────────────────────
        total_raw = sum(scores.values())
        # Map to 0-100 confidence, centered at 50 = Hold
        # Max possible raw: ~95, Min: ~-90
        confidence_raw = (total_raw + 90) / 185 * 100
        confidence = max(5, min(95, confidence_raw))

        if total_raw >= 25:
            signal = "BUY"
            signal_color = "#22C55E"
            signal_emoji = "🟢"
        elif total_raw <= -20:
            signal = "SELL"
            signal_color = "#EF4444"
            signal_emoji = "🔴"
        else:
            signal = "HOLD"
            signal_color = "#F59E0B"
            signal_emoji = "🟡"

        result = {
            "symbol": symbol,
            "company_name": company_name,
            "signal": signal,
            "signal_color": signal_color,
            "signal_emoji": signal_emoji,
            "confidence": round(confidence),
            "raw_score": total_raw,
            "score_breakdown": scores,
            "reasons": reasons,
            "rsi": round(rsi, 1),
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "current_price": round(current_price, 2),
        }

        _signal_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error("get_trading_signal(%s) failed: %s", symbol, e, exc_info=True)
        return {"error": f"Signal calculation temporarily unavailable for {symbol}."}


# ─────────────────────────────────────────────────────────────
# MARKET MOOD INDICATOR
# ─────────────────────────────────────────────────────────────

@_get_st_cache_data()(ttl=300)
def get_market_mood() -> dict:
    """
    Calculate overall Indian market mood from:
    - Nifty 50 movement
    - Sector index movement
    - News sentiment on top stocks
    - Advance-decline ratio (proxy via top stocks)

    Returns:
        dict with mood label, scores, and percentages.
        Returns a safe neutral fallback dict on any failure.
    """
    cache_key = "market_mood"
    if cache_key in _signal_cache:
        return _signal_cache[cache_key]

    try:
        mood_scores = []
        details = []

        # ── Nifty 50 movement ────────────────────────────────
        nifty_data = get_stock_price("^NSEI")
        if "error" not in nifty_data:
            nifty_chg = nifty_data.get("change_pct", 0)
            if nifty_chg > 1.0:
                mood_scores.append(85)
            elif nifty_chg > 0.3:
                mood_scores.append(65)
            elif nifty_chg > -0.3:
                mood_scores.append(50)
            elif nifty_chg > -1.0:
                mood_scores.append(35)
            else:
                mood_scores.append(15)
            details.append({"label": "Nifty 50", "change": nifty_chg, "price": nifty_data.get("current_price")})

        # ── Sensex movement ──────────────────────────────────
        sensex_data = get_stock_price("^BSESN")
        if "error" not in sensex_data:
            sensex_chg = sensex_data.get("change_pct", 0)
            if sensex_chg > 0:
                mood_scores.append(60)
            else:
                mood_scores.append(40)
            details.append({"label": "Sensex", "change": sensex_chg, "price": sensex_data.get("current_price")})

        # ── Sample top stocks ────────────────────────────────
        sample_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
        gainers = 0
        losers = 0
        for sym in sample_stocks:
            p = get_stock_price(sym)
            if "error" not in p:
                if p.get("change_pct", 0) > 0:
                    gainers += 1
                else:
                    losers += 1

        total_stocks = gainers + losers
        if total_stocks > 0:
            advance_ratio = gainers / total_stocks
            mood_scores.append(advance_ratio * 100)

        # ── News sentiment on market ─────────────────────────
        try:
            market_news = get_news_with_sentiment("NIFTY", "Indian stock market Nifty")
            sentiment = market_news.get("avg_score", 0)
            sentiment_mood = (sentiment + 1) / 2 * 100  # normalize -1..1 → 0..100
            mood_scores.append(sentiment_mood)
        except Exception:
            pass

        # ── Aggregate mood ───────────────────────────────────
        if mood_scores:
            avg_mood = sum(mood_scores) / len(mood_scores)
        else:
            avg_mood = 50  # Default neutral

        bullish_pct = min(100, max(0, avg_mood))
        bearish_pct = min(100, max(0, (100 - avg_mood) * 0.6))
        neutral_pct = max(0, 100 - bullish_pct - bearish_pct)

        # Normalize to 100%
        total = bullish_pct + bearish_pct + neutral_pct
        if total > 0:
            bullish_pct = round(bullish_pct / total * 100)
            bearish_pct = round(bearish_pct / total * 100)
            neutral_pct = 100 - bullish_pct - bearish_pct

        if avg_mood >= 65:
            mood_label = "Bullish 🐂"
            mood_color = "#22C55E"
        elif avg_mood >= 45:
            mood_label = "Neutral ➡️"
            mood_color = "#F59E0B"
        else:
            mood_label = "Bearish 🐻"
            mood_color = "#EF4444"

        result = {
            "mood_label": mood_label,
            "mood_color": mood_color,
            "mood_score": round(avg_mood),
            "bullish_pct": bullish_pct,
            "neutral_pct": neutral_pct,
            "bearish_pct": bearish_pct,
            "nifty_data": nifty_data if "error" not in nifty_data else {},
            "sensex_data": sensex_data if "error" not in sensex_data else {},
            "gainers": gainers,
            "losers": losers,
            "details": details,
        }

        _signal_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error("get_market_mood() failed: %s", e, exc_info=True)
        return {
            "mood_label": "Neutral ➡️",
            "mood_color": "#F59E0B",
            "mood_score": 50,
            "bullish_pct": 40,
            "neutral_pct": 35,
            "bearish_pct": 25,
            "gainers": 0,
            "losers": 0,
            "nifty_data": {},
            "sensex_data": {},
            "details": [],
            "error": "Market mood data temporarily unavailable.",
        }


# ─────────────────────────────────────────────────────────────
# PORTFOLIO RISK SCORE
# ─────────────────────────────────────────────────────────────

def calculate_portfolio_risk(holdings: list, current_prices: dict) -> dict:
    """
    Calculate portfolio risk score on a scale of 1–10.

    Risk factors:
    1. Volatility (beta proxy from 30-day returns std dev)
    2. Concentration (Herfindahl index)
    3. Sector diversification
    4. Number of holdings
    5. Individual stock risk signals

    Returns:
        dict with risk_score (1–10), risk_label, risk_color, breakdown
    """
    if not holdings:
        return {"error": "No holdings found"}

    try:
        risk_components = {}
        volatilities = []
        weights = []
        sectors = {}
        total_value = 0

        for h in holdings:
            symbol = h["symbol"]
            qty = h["quantity"]
            price = current_prices.get(symbol, h["buy_price"])
            value = price * qty
            total_value += value

        if total_value == 0:
            return {"error": "Portfolio value is zero"}

        for h in holdings:
            symbol = h["symbol"]
            qty = h["quantity"]
            price = current_prices.get(symbol, h["buy_price"])
            value = price * qty
            weight = value / total_value
            weights.append(weight)

            # Volatility from 30-day returns
            try:
                df = get_historical_data(symbol, period="3mo")
                if not df.empty:
                    returns = df["Close"].pct_change().dropna()
                    vol = returns.std() * np.sqrt(252) * 100  # annualized %
                    volatilities.append((vol, weight))
                else:
                    volatilities.append((25, weight))  # default 25% vol
            except Exception:
                volatilities.append((25, weight))

            # Sector info
            try:
                fund = get_fundamental_analysis(symbol)
                sector = fund.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + weight
            except Exception:
                sectors["Unknown"] = sectors.get("Unknown", 0) + weight

        # ── 1. Weighted Volatility Risk (0–10) ───────────────
        if volatilities:
            weighted_vol = sum(v * w for v, w in volatilities)
            vol_risk = min(10, weighted_vol / 5)  # 50% annual vol = 10
        else:
            vol_risk = 5
        risk_components["volatility"] = round(vol_risk, 2)

        # ── 2. Concentration Risk (Herfindahl Index) ─────────
        hhi = sum(w ** 2 for w in weights)  # 0.01 (diversified) to 1.0 (all in one)
        concentration_risk = hhi * 10  # scale 0–10
        risk_components["concentration"] = round(concentration_risk, 2)

        # ── 3. Sector Diversification ────────────────────────
        n_sectors = len([s for s in sectors if s != "Unknown"])
        if n_sectors >= 5:
            sector_risk = 1
        elif n_sectors >= 3:
            sector_risk = 3
        elif n_sectors >= 2:
            sector_risk = 5
        else:
            sector_risk = 8
        risk_components["sector_diversification"] = sector_risk

        # ── 4. Holdings Count Risk ───────────────────────────
        n = len(holdings)
        if n >= 10:
            count_risk = 1
        elif n >= 6:
            count_risk = 3
        elif n >= 3:
            count_risk = 5
        else:
            count_risk = 8
        risk_components["holdings_count"] = count_risk

        # ── Aggregate Risk Score ─────────────────────────────
        weights_risk = {
            "volatility": 0.40,
            "concentration": 0.30,
            "sector_diversification": 0.20,
            "holdings_count": 0.10,
        }
        risk_score = sum(risk_components[k] * weights_risk[k] for k in weights_risk)
        risk_score = round(min(10, max(1, risk_score)), 1)

        # Labels
        if risk_score <= 3:
            risk_label = "Low Risk"
            risk_color = "#22C55E"
            risk_description = "Well-diversified portfolio with stable stocks."
        elif risk_score <= 6:
            risk_label = "Moderate Risk"
            risk_color = "#F59E0B"
            risk_description = "Balanced mix of growth and stability."
        elif risk_score <= 8:
            risk_label = "High Risk"
            risk_color = "#EF4444"
            risk_description = "Concentrated or volatile holdings. Consider diversifying."
        else:
            risk_label = "Very High Risk"
            risk_color = "#DC2626"
            risk_description = "Extremely concentrated or highly volatile portfolio."

        return {
            "risk_score": risk_score,
            "risk_label": risk_label,
            "risk_color": risk_color,
            "risk_description": risk_description,
            "breakdown": risk_components,
            "sectors": sectors,
            "weighted_volatility": round(weighted_vol if volatilities else 25, 1),
            "n_holdings": len(holdings),
            "n_sectors": len(sectors),
        }

    except Exception as e:
        return {"error": f"Risk calculation failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────
# TOP MOVERS
# ─────────────────────────────────────────────────────────────

@_get_st_cache_data()(ttl=300)
def get_top_movers() -> dict:
    """
    Get top gainers and losers from popular Indian stocks.

    Returns:
        dict with gainers and losers lists.
        Returns empty lists on failure — never raises.
    """
    cache_key = "top_movers"
    if cache_key in _signal_cache:
        return _signal_cache[cache_key]

    from config.settings import settings
    stocks_to_check = list(settings.POPULAR_STOCKS.keys())

    movers = []
    for symbol in stocks_to_check:
        try:
            data = get_stock_price(symbol)
            if "error" not in data:
                movers.append({
                    "symbol": symbol.replace(".NS", ""),
                    "full_symbol": symbol,
                    "company": data.get("company_name", symbol)[:22],
                    "price": data.get("current_price", 0),
                    "change_pct": data.get("change_pct", 0),
                    "change": data.get("change", 0),
                })
        except Exception as e:
            logger.warning("get_top_movers: skipping %s — %s", symbol, e)

    movers.sort(key=lambda x: x["change_pct"], reverse=True)
    gainers = [m for m in movers if m["change_pct"] > 0][:5]
    losers = [m for m in movers if m["change_pct"] < 0][-5:]
    losers.reverse()

    result = {"gainers": gainers, "losers": losers, "all": movers}
    _signal_cache[cache_key] = result
    return result
