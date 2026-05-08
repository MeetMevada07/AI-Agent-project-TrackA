# ============================================================
# agents/market_brief.py
# AI Daily Market Brief Generator
# ============================================================

import logging
import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


MARKET_BRIEF_PROMPT = PromptTemplate(
    input_variables=["nifty_data", "sensex_data", "sector_performance", "market_breadth", "news_headlines", "market_mood"],
    template="""You are FinSaarthi, an expert Indian financial market analyst.

Generate a concise, insightful Daily Market Brief for Indian investors based on this data:

📊 INDEX PERFORMANCE:
{nifty_data}
{sensex_data}

🏭 SECTOR PERFORMANCE TODAY:
{sector_performance}

📊 MARKET BREADTH:
{market_breadth}

🌡️ MARKET MOOD: {market_mood}

📰 KEY NEWS HEADLINES:
{news_headlines}

Write a professional market brief that covers:
1. **Market Overview** — How did the indices perform and why?
2. **Sector Spotlight** — Which sectors led or lagged and why?
3. **Market Breadth Analysis** — How broad was today's move?
4. **Sentiment Analysis** — What is driving investor sentiment today?
5. **Key Takeaways** — 2-3 actionable insights for investors

Keep it concise (under 400 words), use simple language suitable for retail investors.
Use ₹ symbol for prices. Be specific with numbers.
Format with clear sections using markdown headers.
"""
)

STOCK_COMPARISON_PROMPT = PromptTemplate(
    input_variables=["symbols", "comparison_data", "signals"],
    template="""You are FinSaarthi, an expert Indian stock analyst.

Compare these stocks for an Indian retail investor:
Stocks: {symbols}

Comparison Data:
{comparison_data}

AI Signals:
{signals}

Provide a structured comparison covering:

## 📊 Head-to-Head Summary
Brief overview of each stock's position

## 💪 Strengths & Weaknesses  
For each stock, list 2 strengths and 1 weakness

## 📰 Sentiment & Momentum
Current market sentiment and technical momentum for each

## 🎯 Investment Outlook
Which stock looks most attractive for:
- Short-term traders (1-3 months)
- Long-term investors (1-3 years)
- Dividend seekers

## ⚠️ Key Risks
What risks should investors be aware of?

Keep it concise and data-driven. Avoid generic advice.
"""
)


def generate_market_brief(llm, nifty_data: dict, sensex_data: dict,
                           sector_data: list, breadth_data: dict,
                           news_headlines: str, mood: str) -> str:
    """Generate AI market brief using LLM."""
    try:
        chain = LLMChain(llm=llm, prompt=MARKET_BRIEF_PROMPT, verbose=False)

        nifty_str = (
            f"Nifty 50: {nifty_data.get('current_price', 'N/A')} "
            f"({nifty_data.get('change_pct', 0):+.2f}%)"
            if nifty_data else "Nifty 50: Data unavailable"
        )
        sensex_str = (
            f"Sensex: {sensex_data.get('current_price', 'N/A')} "
            f"({sensex_data.get('change_pct', 0):+.2f}%)"
            if sensex_data else "Sensex: Data unavailable"
        )

        sector_str = "\n".join([
            f"• {s['sector']}: {s['avg_change']:+.2f}% (avg of {len(s['stocks'])} stocks)"
            for s in sector_data
        ]) if sector_data else "Sector data unavailable"

        adv  = breadth_data.get("advance", 0)
        dec  = breadth_data.get("decline", 0)
        adr  = breadth_data.get("ad_ratio", 1.0)
        blbl = breadth_data.get("breadth_label", "Mixed")
        avch = breadth_data.get("avg_change", 0)
        breadth_str = (
            f"{blbl} | Advancing: {adv}, Declining: {dec}, "
            f"A/D Ratio: {adr:.2f}, Avg Change: {avch:+.2f}%"
        )

        response = chain.invoke({
            "nifty_data": nifty_str,
            "sensex_data": sensex_str,
            "sector_performance": sector_str,
            "market_breadth": breadth_str,
            "news_headlines": news_headlines or "No news data available",
            "market_mood": mood,
        })
        return response["text"]

    except Exception as e:
        logger.error("generate_market_brief failed: %s", e, exc_info=True)
        return (
            "⚠️ Market brief generation encountered an issue. "
            "Please check your LLM API key and internet connection, then try again."
        )


def generate_comparison_summary(llm, symbols: list, comparison_data: str, signals: list) -> str:
    """Generate AI stock comparison summary."""
    try:
        chain = LLMChain(llm=llm, prompt=STOCK_COMPARISON_PROMPT, verbose=False)

        signals_str = "\n".join([
            f"• {s.get('symbol', '')}: {s.get('signal', 'N/A')} "
            f"(Confidence: {s.get('confidence', 0)}%)"
            for s in signals if "error" not in s
        ])

        response = chain.invoke({
            "symbols": ", ".join(symbols),
            "comparison_data": comparison_data,
            "signals": signals_str or "Signal data unavailable",
        })
        return response["text"]

    except Exception as e:
        logger.error("generate_comparison_summary failed: %s", e, exc_info=True)
        return (
            "⚠️ AI comparison summary is temporarily unavailable. "
            "Please check your LLM API key and try again."
        )
