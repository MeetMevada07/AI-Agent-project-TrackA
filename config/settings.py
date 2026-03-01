# ============================================================
# config/settings.py
# Centralized configuration management
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings class — reads from .env file."""

    # --- LLM ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # or "gemini"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL_OPENAI: str = "gpt-3.5-turbo"
    LLM_MODEL_GEMINI: str = "gemini-pro"

    LLM_TEMPERATURE: float = 0.3

    # --- News ---
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # --- Alpha Vantage ---
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")

    # --- Database ---
    DB_PATH: str = "data/finance_agent.db"

    # --- Cache ---
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # --- Indian Market ---
    MARKET_TIMEZONE: str = "Asia/Kolkata"
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 15
    MARKET_CLOSE_HOUR: int = 15
    MARKET_CLOSE_MINUTE: int = 30

    # Popular Indian stocks with display names
    POPULAR_STOCKS: dict = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "WIPRO.NS": "Wipro",
        "SBIN.NS": "State Bank of India",
        "BAJFINANCE.NS": "Bajaj Finance",
        "BHARTIARTL.NS": "Bharti Airtel",
        "HINDUNILVR.NS": "Hindustan Unilever",
        "LT.NS": "Larsen & Toubro",
        "KOTAKBANK.NS": "Kotak Mahindra Bank",
        "ASIANPAINT.NS": "Asian Paints",
        "TITAN.NS": "Titan Company",
        "ULTRACEMCO.NS": "UltraTech Cement",
    }

    # Indian market sectors
    SECTORS: dict = {
        "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
        "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
        "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
        "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS"],
    }


settings = Settings()
