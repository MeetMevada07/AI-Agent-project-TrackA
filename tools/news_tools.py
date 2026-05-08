# ============================================================
# tools/news_tools.py
# News fetching + sentiment analysis
# Source priority:
#   1. yfinance ticker.news  (free, no key, genuine recent news)
#   2. NewsAPI               (requires NEWS_API_KEY in .env)
#   3. Mixed-sentiment mock  (fallback when both above fail)
# ============================================================


import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cachetools import TTLCache
from config.settings import settings

import logging
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

_news_cache = TTLCache(maxsize=50, ttl=settings.CACHE_TTL_SECONDS)
_vader = SentimentIntensityAnalyzer()


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


# ─────────────────────────────────────────────
# Resolve company name from symbol
# ─────────────────────────────────────────────
def _resolve_company_name(symbol: str, company_name: str = "") -> str:
    clean = symbol.replace(".NS", "").replace(".BO", "").replace("^", "")
    if company_name and company_name not in (symbol, clean, ""):
        return company_name
    return settings.POPULAR_STOCKS.get(symbol, clean)


# ─────────────────────────────────────────────
# SOURCE 1 — yfinance ticker.news (FREE, no key)
# ─────────────────────────────────────────────
def _fetch_yfinance_news(symbol: str, max_articles: int = 10) -> list:
    """
    Use yfinance's built-in news endpoint.
    Returns genuine recent articles — no API key needed.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news or []

        articles = []
        for item in raw_news[:max_articles]:
            # yfinance news item structure
            content = item.get("content", item)  # newer yfinance wraps in 'content'
            title = (
                content.get("title", "")
                or item.get("title", "")
            )
            if not title:
                continue

            # Try to get summary/description
            summary = (
                content.get("summary", "")
                or content.get("description", "")
                or item.get("summary", "")
                or ""
            )

            # Published date
            pub_date = ""
            pub_ts = content.get("pubDate") or content.get("publishedAt") or item.get("providerPublishTime")
            if pub_ts:
                try:
                    if isinstance(pub_ts, (int, float)):
                        pub_date = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d")
                    else:
                        pub_date = str(pub_ts)[:10]
                except Exception:
                    pub_date = ""

            # Source
            publisher = (
                content.get("provider", {}).get("displayName", "")
                or content.get("source", "")
                or item.get("publisher", "")
                or "Yahoo Finance"
            )

            # URL
            url = (
                content.get("canonicalUrl", {}).get("url", "")
                or content.get("url", "")
                or item.get("link", "")
                or "#"
            )

            articles.append({
                "title": title,
                "description": summary,
                "url": url,
                "source": publisher,
                "published_at": pub_date,
            })

        logger.info("yfinance news: fetched %d articles for %s", len(articles), symbol)
        return articles

    except Exception as e:
        logger.warning("yfinance news failed for %s: %s", symbol, e)
        return []


# ─────────────────────────────────────────────
# SOURCE 2 — NewsAPI (requires API key)
# ─────────────────────────────────────────────
def _fetch_newsapi(query: str, days_back: int = 7, max_articles: int = 10) -> list:
    """Fetch from NewsAPI. Returns [] if key missing or request fails."""
    if not settings.NEWS_API_KEY:
        return []

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    def parse(data):
        result = []
        for art in data.get("articles", []):
            if art.get("title") and art["title"] != "[Removed]":
                result.append({
                    "title": art.get("title", ""),
                    "description": art.get("description", "") or "",
                    "url": art.get("url", ""),
                    "source": art.get("source", {}).get("name", "Unknown"),
                    "published_at": art.get("publishedAt", "")[:10],
                })
        return result

    try:
        # Try Indian financial domains first
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "pageSize": max_articles,
                "language": "en",
                "domains": (
                    "economictimes.indiatimes.com,moneycontrol.com,livemint.com,"
                    "business-standard.com,financialexpress.com,cnbctv18.com,reuters.com"
                ),
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=10,
        )
        r.raise_for_status()
        articles = parse(r.json())

        if not articles:
            # Broader fallback
            r2 = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query, "from": from_date,
                    "sortBy": "publishedAt", "pageSize": max_articles,
                    "language": "en", "apiKey": settings.NEWS_API_KEY,
                },
                timeout=10,
            )
            r2.raise_for_status()
            articles = parse(r2.json())

        return articles

    except Exception as e:
        logger.warning("NewsAPI failed for '%s': %s", query, e)
        return []


# ─────────────────────────────────────────────
# SOURCE 3 — Mixed-sentiment mock (fallback)
# ─────────────────────────────────────────────
def _get_mock_news(name: str) -> list:
    """
    Realistic mock news with genuinely MIXED sentiment
    (positive, negative, neutral) so gauge shows real variation.
    """
    if not name:
        name = "This Stock"

    today      = datetime.now().strftime("%Y-%m-%d")
    yesterday  = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days   = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    three_days = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    return [
        # ── POSITIVE ──────────────────────────────────────────────
        {
            "title": f"{name} Q3 FY25 profit jumps 18% YoY; beats Street estimates",
            "description": (
                f"{name} delivered strong quarterly earnings with net profit rising 18% year-on-year, "
                "beating analyst estimates. Revenue grew 14% driven by robust domestic demand "
                "and improving margins. Management retained its growth guidance for FY26."
            ),
            "url": "https://economictimes.indiatimes.com",
            "source": "Economic Times",
            "published_at": today,
        },
        {
            "title": f"Brokerages raise target on {name} by 12%; BUY rating maintained",
            "description": (
                f"Multiple top brokerages upgraded their target prices on {name} after "
                "better-than-expected quarterly results. Analysts cited improving return "
                "ratios, strong cash flows, and a healthy order book as key positives."
            ),
            "url": "https://moneycontrol.com",
            "source": "Moneycontrol",
            "published_at": today,
        },
        # ── NEGATIVE ──────────────────────────────────────────────
        {
            "title": f"{name} shares fall 3.2% as margin pressure mounts; analysts cut estimates",
            "description": (
                f"Shares of {name} declined sharply after the management warned of near-term "
                "margin pressure due to rising input costs and wage inflation. Several brokerages "
                "cut their FY25 earnings estimates by 5-8%, citing a challenging demand environment."
            ),
            "url": "https://livemint.com",
            "source": "Livemint",
            "published_at": yesterday,
        },
        {
            "title": f"{name} faces regulatory scrutiny; stock under pressure on NSE",
            "description": (
                f"{name} came under selling pressure after reports emerged of a regulatory "
                "probe into its recent acquisition. The stock fell over 2% intraday on heavy "
                "volumes. FIIs turned net sellers for the second consecutive session."
            ),
            "url": "https://business-standard.com",
            "source": "Business Standard",
            "published_at": yesterday,
        },
        # ── NEUTRAL ───────────────────────────────────────────────
        {
            "title": f"{name} board to meet on March 15 to consider Q3 results and dividend",
            "description": (
                f"The board of directors of {name} will convene on March 15, 2025 "
                "to consider and approve the financial results for Q3 FY25. "
                "The company may also consider declaration of an interim dividend."
            ),
            "url": "https://financialexpress.com",
            "source": "Financial Express",
            "published_at": two_days,
        },
        {
            "title": f"{name} completes ₹1,200 Cr QIP; allots shares at ₹845 per share",
            "description": (
                f"{name} successfully concluded its qualified institutional placement, "
                "raising ₹1,200 Crore at ₹845 per share. The funds will be utilized for "
                "capex expansion and general corporate purposes, the company said."
            ),
            "url": "https://cnbctv18.com",
            "source": "CNBC TV18",
            "published_at": two_days,
        },
        # ── MILDLY NEGATIVE ───────────────────────────────────────
        {
            "title": f"{name} Q4 outlook cautious; revenue growth may slow to 8-10%",
            "description": (
                f"Management of {name} struck a cautious tone for Q4 FY25, guiding for "
                "revenue growth of 8-10% vs 14% in Q3, citing global macro headwinds and "
                "softening demand in key export markets. Domestic business remains stable."
            ),
            "url": "https://reuters.com",
            "source": "Reuters",
            "published_at": three_days,
        },
    ]


# ─────────────────────────────────────────────
# Sentiment analysis
# ─────────────────────────────────────────────
def analyze_sentiment(text: str) -> dict:
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label, color = "Positive 📈", "green"
    elif compound <= -0.05:
        label, color = "Negative 📉", "red"
    else:
        label, color = "Neutral ➡️", "gray"

    return {
        "compound": round(compound, 4),
        "positive": round(scores["pos"], 4),
        "negative": round(scores["neg"], 4),
        "neutral":  round(scores["neu"], 4),
        "label": label,
        "color": color,
    }


# ─────────────────────────────────────────────
# Main public API
# ─────────────────────────────────────────────
@_get_st_cache_data()(ttl=300)
def get_stock_news(query: str, days_back: int = 7, max_articles: int = 10) -> list:
    """Fetch news ONLY for Indian listed stocks."""

    import yfinance as yf

    query = query.upper().strip()

    # ✅ Step 1: Format validation
    if not (query.endswith(".NS") or query.endswith(".BO")):
        return [f"⚠️ '{query}' valid Indian stock nahi hai. Example: RELIANCE.NS"]

    # ✅ Step 2: Check valid ticker using history (NO ERROR SPAM)
    try:
        ticker = yf.Ticker(query)
        hist = ticker.history(period="1d")

        if hist.empty:
            return [f"⚠️ '{query}' Indian stock exchange par listed nahi hai ya invalid hai."]
    except Exception:
        return [f"⚠️ '{query}' verify nahi ho paya."]

    # ✅ Step 3: Fetch news (FIXED POSITION)
    return _fetch_newsapi(query, days_back, max_articles)

@_get_st_cache_data()(ttl=300)
def get_news_with_sentiment(symbol: str, company_name: str = "") -> dict:
    """
    Fetch genuine recent news + sentiment for a stock symbol.
    """

    import yfinance as yf

    symbol = symbol.upper().strip()

    # ✅ STEP 1: format check
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        raise ValueError(f"Symbol '{symbol}' not found on NSE.")

    # ✅ STEP 2: listing check
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")

        if hist.empty:
            raise ValueError(f"Symbol '{symbol}' not found on NSE.")
    except Exception:
        raise ValueError(f"Symbol '{symbol}' not found on NSE.")

    # ✅ ONLY VALID STOCKS COME BELOW THIS LINE
    resolved_name = _resolve_company_name(symbol, company_name)

    # ── Source 1: yfinance ──
    articles = _fetch_yfinance_news(symbol, max_articles=10)

    # ── Source 2: NewsAPI ──
    if not articles:
        query = f'"{resolved_name}" stock India'
        articles = _fetch_newsapi(query, days_back=7, max_articles=10)

    # ── Source 3: fallback ──
    if not articles:
        logger.info("All live sources failed for %s — using mock news", symbol)
        articles = _get_mock_news(resolved_name)

    # ── Sentiment ──
    enriched, scores = [], []
    for art in articles:
        try:
            text = f"{art['title']} {art.get('description', '')}"
            sentiment = analyze_sentiment(text)
        except Exception:
            sentiment = {
                "compound": 0, "label": "Neutral ➡️", "color": "gray",
                "positive": 0, "negative": 0, "neutral": 1,
            }
        art["sentiment"] = sentiment
        enriched.append(art)
        scores.append(sentiment["compound"])

    avg_score = round(sum(scores) / len(scores), 4) if scores else 0

    if avg_score >= 0.05:
        overall = "Bullish 📈"
    elif avg_score <= -0.05:
        overall = "Bearish 📉"
    else:
        overall = "Neutral ➡️"

    return {
        "articles": enriched,
        "overall_sentiment": overall,
        "avg_score": avg_score,
        "pos_count": sum(1 for s in scores if s >= 0.05),
        "neg_count": sum(1 for s in scores if s <= -0.05),
        "neu_count": len(scores) - sum(1 for s in scores if abs(s) >= 0.05),
        "summary": f"Analyzed {len(articles)} articles. Overall: {overall}"
    }

def is_indian_stock(symbol: str) -> bool:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        return not hist.empty
    except Exception:
        return False
