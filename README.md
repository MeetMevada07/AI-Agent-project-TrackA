# 📈 FinSaarthi — Indian Stock Market AI Financial Agent

> **Track A — Production-Ready Financial Analysis Application**  
> Built with LangChain + Streamlit + yfinance | Supports NSE/BSE Indian Stocks

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.2.11-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat** | Conversational AI with memory — ask anything about Indian markets |
| 📊 **Stock Analysis** | Full technical + fundamental analysis with interactive charts |
| 🔄 **Stock Comparison** | Side-by-side comparison of up to 5 Indian stocks |
| 📰 **News Sentiment** | VADER-powered sentiment analysis on latest stock news |
| 💼 **Portfolio Tracker** | Track holdings with live P&L, stored in SQLite |
| ⭐ **Watchlist** | Save and monitor stocks with live price updates |
| 🧮 **Calculators** | SIP calculator + LTCG/STCG tax calculator |
| 📥 **PDF Export** | Download analysis reports as PDF |

---

## 🏗️ Architecture

```
indian_finance_agent/
├── app.py                    # Streamlit entry point (main UI)
├── llm.py                    # LLM setup (Gemini / OpenAI)
├── prompts.py                # All LangChain prompt templates
├── utils.py                  # Utilities (PDF export, INR format, market status)
├── requirements.txt          # Pinned dependencies
├── .env.example              # Environment variable template
│
├── config/
│   └── settings.py           # Centralized configuration
│
├── tools/
│   ├── stock_tools.py        # yfinance: prices, technicals, fundamentals
│   └── news_tools.py         # NewsAPI + VADER sentiment analysis
│
├── agents/
│   └── financial_agent.py    # LangChain agent with memory
│
├── database/
│   └── db_manager.py         # SQLite: watchlist + portfolio
│
├── ui/
│   └── charts.py             # Plotly chart builders
│
└── data/
    └── finance_agent.db      # SQLite database (auto-created)
```

---

## 🚀 Quick Start

### Step 1 — Clone & Setup Environment

```bash
# Clone the repository
git clone url
cd AI-Agent-project-TrackA

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt

# Download TextBlob corpora
python -m textblob.download_corpora
```

### Step 3 — Configure API Keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your keys:
nano .env   # or use any text editor
```

Fill in your `.env` file:x

```env
# Choose your LLM provider
LLM_PROVIDER=gemini          # 'gemini' or 'openai'

# For Gemini (FREE tier — recommended):
# Get key at: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_key_here

# For OpenAI (paid):
# Get key at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_key_here

# For news (FREE tier — 100 req/day):
# Get key at: https://newsapi.org/register
NEWS_API_KEY=your_newsapi_key_here
```

### Step 4 — Run the App

```bash
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

---

## 🇮🇳 Indian Stock Symbols Guide

| Exchange | Suffix | Example |
|----------|--------|---------|
| NSE (National Stock Exchange) | `.NS` | `RELIANCE.NS` |
| BSE (Bombay Stock Exchange) | `.BO` | `RELIANCE.BO` |

### Popular NSE Stocks to Try:
```
RELIANCE.NS    Reliance Industries (Energy/Retail/Telecom)
TCS.NS         Tata Consultancy Services (IT)
INFY.NS        Infosys (IT)
HDFCBANK.NS    HDFC Bank (Banking)
ICICIBANK.NS   ICICI Bank (Banking)
SBIN.NS        State Bank of India (PSU Banking)
WIPRO.NS       Wipro (IT)
BAJFINANCE.NS  Bajaj Finance (NBFC)
BHARTIARTL.NS  Bharti Airtel (Telecom)
LT.NS          Larsen & Toubro (Infrastructure)
```

---

## 💡 Usage Examples

### AI Chat Queries:
- *"Analyze TCS stock for long-term investment"*
- *"Compare Reliance vs HDFC Bank fundamentals"*
- *"Explain what RSI of 75 means for Infosys"*
- *"What is the LTCG tax on ₹2 lakh profit from Wipro shares?"*
- *"Should I start a SIP in Nifty 50 index fund?"*

### Stock Analysis:
1. Enter symbol: `TCS.NS`
2. Select period: `1y`
3. Enable SMA 20/50 overlays
4. Click **Analyze**
5. View price, technicals, fundamentals, and AI report

---

## 📊 Technical Indicators Explained

| Indicator | What it tells you |
|-----------|-------------------|
| **SMA 20/50** | Short and medium-term trend direction |
| **EMA 20** | Momentum-weighted moving average |
| **RSI (14)** | Overbought (>70) or Oversold (<30) |
| **MACD** | Trend direction and momentum changes |
| **Bollinger Bands** | Volatility and price breakout zones |

---

## 🏛️ Indian Tax Rules Implemented

| Tax | Holding Period | Rate | Exemption |
|-----|----------------|------|-----------|
| STCG | < 12 months | 20% | None |
| LTCG | ≥ 12 months | 12.5% | ₹1,25,000/year |

---

## ☁️ Deployment on Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add secrets in Streamlit Cloud dashboard:
   ```
   GOOGLE_API_KEY = "your_key"
   LLM_PROVIDER = "gemini"
   NEWS_API_KEY = "your_key"
   ```
5. Deploy! ✅

---

## ⚠️ Disclaimer

This application is for **educational and informational purposes only**. It does not constitute financial advice. Past performance of stocks does not guarantee future returns. Please consult a SEBI-registered investment advisor before making investment decisions.

---

## 📄 License

MIT License — Free to use, modify, and distribute.
