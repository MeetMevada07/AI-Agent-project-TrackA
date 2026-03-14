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
    input_variables=["nifty_data", "sensex_data", "top_gainers", "top_losers", "news_headlines", "market_mood"],
    template="""You are FinSaarthi, an expert Indian financial market analyst.

Generate a concise, insightful Daily Market Brief for Indian investors based on this data:

📊 INDEX PERFORMANCE:
{nifty_data}
{sensex_data}

📈 TOP GAINERS TODAY:
{top_gainers}

📉 TOP LOSERS TODAY:
{top_losers}

🌡️ MARKET MOOD: {market_mood}

📰 KEY NEWS HEADLINES:
{news_headlines}

Write a professional market brief that covers:
1. **Market Overview** — How did the indices perform and why?
2. **Key Movers** — Notable gainers and losers with brief reasons
3. **Sentiment Analysis** — What is driving investor sentiment today?
4. **Key Takeaways** — 2-3 actionable insights for investors
5. **Watch List for Tomorrow** — What should investors monitor?

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
                           gainers: list, losers: list,
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

        gainers_str = "\n".join([
            f"• {g['company']} ({g['symbol']}): +{g['change_pct']:.2f}%"
            for g in gainers[:5]
        ]) or "No significant gainers today"

        losers_str = "\n".join([
            f"• {l['company']} ({l['symbol']}): {l['change_pct']:.2f}%"
            for l in losers[:5]
        ]) or "No significant losers today"

        response = chain.invoke({
            "nifty_data": nifty_str,
            "sensex_data": sensex_str,
            "top_gainers": gainers_str,
            "top_losers": losers_str,
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

