# 📈 FinSaarthi v2.0 — AI Indian Stock Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **AI-Powered Financial Intelligence for Indian Markets** — Professional-grade stock analysis dashboard with AI signals, market mood analysis, portfolio risk assessment, and automated market briefs.

![FinSaarthi Dashboard](https://via.placeholder.com/800x400/2563EB/FFFFFF?text=FinSaarthi+Dashboard+Screenshot)

## ✨ Features

### 🤖 AI Trading Signals
- **Buy/Hold/Sell Recommendations** with confidence percentages
- **Technical Analysis**: MA Crossover, RSI, MACD signals
- **Sentiment Analysis**: News-based market sentiment scoring
- **52-Week Position Analysis** with visual indicators

### 🌡️ Market Mood Indicator
- **Nifty + Sensex Movement Analysis**
- **Advance/Decline Ratio** tracking
- **News Sentiment Aggregation**
- **Bullish/Neutral/Bearish** percentage breakdown

### 📋 AI Daily Market Brief
- **One-click AI-generated summaries**
- **Top gainers/losers analysis**
- **Sector performance insights**
- **Key news highlights**

### 🛡️ Portfolio Risk Assessment
- **Risk Score (1-10)** with visual gauge
- **Volatility Analysis** and concentration metrics
- **Sector Diversification** scoring
- **Herfindahl Index** calculations

### 🔄 AI Stock Comparison
- **Multi-stock signal comparison**
- **AI narrative analysis** (strengths, weaknesses, outlook)
- **6-month normalized performance charts**

### ⭐ Smart Watchlist
- **AI signal indicators** per stock
- **Trend analysis** (Bullish/Bearish)
- **Confidence scoring** and alerts

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- API Keys (NewsAPI, LLM provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/finsaarthi.git
   cd finsaarthi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

### Environment Variables (.env)
```env
# LLM Provider Configuration
LLM_PROVIDER=groq          # Options: groq, openai, gemini
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# News API
NEWS_API_KEY=your_newsapi_key_here

# Database
DATABASE_PATH=data/finance_agent.db
```

### Supported LLM Providers
- **Groq** (Recommended) - Fast inference with Llama models
- **OpenAI** - GPT-4/3.5-turbo
- **Google Gemini** - Latest Gemini models

## 🏗️ Project Structure

```
finsaarthi/
├── 📁 app.py                 # Main Streamlit application
├── 📁 config/
│   └── settings.py           # Configuration & API management
├── 📁 agents/
│   ├── financial_agent.py    # LangChain AI agent logic
│   └── market_brief.py       # Market brief & comparison AI
├── 📁 tools/
│   ├── stock_tools.py        # yfinance data fetching & analysis
│   ├── news_tools.py         # NewsAPI integration & sentiment
│   └── ai_signals.py         # AI trading signals & indicators
├── 📁 ui/
│   └── charts.py             # Plotly chart components
├── 📁 database/
│   └── db_manager.py         # SQLite database operations
├── 📁 data/                  # Local data storage
├── 📁 llm.py                 # LLM provider setup
├── 📁 prompts.py             # LangChain prompt templates
├── 📁 utils.py               # Utility functions & helpers
├── 📁 requirements.txt       # Python dependencies
├── 📁 .env.example          # Environment template
└── 📁 README.md             # Project documentation
```

## 🎨 UI/UX Design

- **🎨 Design System**: Bloomberg/Zerodha-inspired dark fintech theme
- **🎯 Color Palette**: Primary `#2563EB` · Success `#22C55E` · Warning `#F59E0B` · Danger `#EF4444`
- **📊 Charts**: Interactive Plotly visualizations
- **📱 Responsive**: Optimized for desktop and tablet
- **✨ Animations**: Smooth transitions and hover effects

## 📦 Deployment

### Streamlit Cloud (Recommended)
1. Push to GitHub repository
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add environment secrets in Streamlit Cloud settings
5. Deploy!

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t finsaarthi .
docker run -p 8501:8501 finsaarthi
```

### Local Development
```bash
# Run with custom port
streamlit run app.py --server.port=8501

# Run in headless mode
streamlit run app.py --server.headless=true
```

## 🔍 Usage Examples

### Basic Stock Analysis
```python
from tools.stock_tools import get_stock_price, get_fundamental_analysis

# Get current price
price = get_stock_price("RELIANCE.NS")

# Get fundamental analysis
fundamentals = get_fundamental_analysis("RELIANCE.NS")
```

### AI Trading Signals
```python
from tools.ai_signals import get_trading_signal

# Get AI signal for a stock
signal = get_trading_signal("TCS.NS")
print(f"Signal: {signal['signal']} (Confidence: {signal['confidence']}%)")
```

### Market Mood Analysis
```python
from tools.ai_signals import get_market_mood

# Get current market sentiment
mood = get_market_mood()
print(f"Market Mood: {mood['mood']} ({mood['bullish_pct']}%)")
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 .
black .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Educational Purpose Only**

This application is for educational and informational purposes only. It is not intended to provide financial advice, recommendations, or endorsements. All investment decisions should be made after consulting with qualified financial advisors. The developers and contributors are not responsible for any financial losses incurred through the use of this application.

**Not SEBI Registered**: This is not a SEBI-registered investment advisor or financial planning service.

## 🙏 Acknowledgments

- **Streamlit** - For the amazing web app framework
- **LangChain** - For LLM orchestration
- **yfinance** - For stock data
- **Plotly** - For interactive charts
- **VADER** - For sentiment analysis
- **NewsAPI** - For financial news

## 📞 Support

- 📧 **Email**: support@finsaarthi.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/finsaarthi/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/finsaarthi/discussions)

---

**Made with ❤️ for Indian investors**
