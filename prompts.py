# ============================================================
# prompts.py
# All LangChain prompt templates for the financial agent
# ============================================================

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# ── System Persona ────────────────────────────────────────────

FINANCIAL_AGENT_SYSTEM = """You are FinSaarthi 🇮🇳, an expert AI financial analyst specializing in Indian stock markets (NSE/BSE).

Your expertise covers:
- Indian equity markets (Nifty 50, Sensex, mid-cap, small-cap)
- Fundamental analysis (P/E, P/B, ROE, debt ratios)
- Technical analysis (RSI, MACD, Bollinger Bands, moving averages)
- Indian taxation (LTCG, STCG, dividend taxation)
- Mutual funds and SIP investing
- Indian macro-economics and RBI monetary policy

Communication style:
- Use ₹ (INR) for all prices and values
- Quote amounts in Lakhs (₹1,00,000) and Crores (₹1,00,00,000)
- Be concise, data-driven, and clear
- Always mention that this is NOT financial advice; users should consult a SEBI-registered advisor
- Reference Indian market context (SEBI regulations, circuit breakers, T+1 settlement)

When given financial data, provide:
1. Clear interpretation of the numbers
2. Comparison to sector/index benchmarks where relevant
3. Key risks and opportunities
4. Brief buy/hold/watch commentary (NOT a buy/sell recommendation)

Remember: NSE stocks end in .NS, BSE stocks end in .BO"""


# ── Chat Prompt (with memory) ─────────────────────────────────

def get_chat_prompt() -> ChatPromptTemplate:
    """
    Conversational prompt with memory for multi-turn chat.
    
    Includes:
    - System persona
    - Chat history placeholder (for ConversationBufferMemory)
    - Human message
    """
    return ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_AGENT_SYSTEM),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])


# ── Stock Analysis Prompt ─────────────────────────────────────

def get_stock_analysis_prompt() -> ChatPromptTemplate:
    """
    Structured prompt for comprehensive stock analysis.
    Takes stock data and news sentiment as context.
    """
    return ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_AGENT_SYSTEM),
        ("human", """Analyze the following Indian stock data and provide a comprehensive report:

**Stock Symbol:** {symbol}
**Company:** {company_name}

**Current Price Data:**
{price_data}

**Fundamental Metrics:**
{fundamental_data}

**Technical Indicators (latest values):**
{technical_data}

**News Sentiment:**
{news_sentiment}

Please provide:
1. **Executive Summary** (2-3 sentences)
2. **Fundamental Health** (valuation, profitability, debt)
3. **Technical Picture** (trend, momentum, support/resistance zones)
4. **News & Sentiment** (key themes from recent news)
5. **Risk Factors** (3 bullet points)
6. **Outlook** (short-term and medium-term view)

Use ₹ for prices and crores for market cap. Keep it professional and data-driven.
Remind the user this is educational analysis, not SEBI-registered financial advice."""),
    ])


# ── Comparison Prompt ─────────────────────────────────────────

def get_comparison_prompt() -> ChatPromptTemplate:
    """Prompt for comparing multiple stocks."""
    return ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_AGENT_SYSTEM),
        ("human", """Compare the following Indian stocks and help me understand which looks more attractive:

**Comparison Data:**
{comparison_data}

**Sector Context:** {sector}

Please provide:
1. **Quick Comparison Table** (mental model of strengths/weaknesses)
2. **Valuation Winner** (which stock is cheaper relative to earnings/book)
3. **Quality Winner** (ROE, margins, debt)
4. **Momentum Winner** (price performance, technical trend)
5. **Final Take** (which you'd want to research further and why)

Be direct and opinionated while clarifying this is not a buy recommendation."""),
    ])


# ── Portfolio Analysis Prompt ─────────────────────────────────

def get_portfolio_prompt() -> ChatPromptTemplate:
    """Prompt for portfolio analysis and suggestions."""
    return ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_AGENT_SYSTEM),
        ("human", """Analyze this investment portfolio:

**Holdings:**
{portfolio_data}

**Total Invested:** ₹{total_invested}
**Current Value:** ₹{current_value}
**Overall P&L:** ₹{pnl} ({pnl_pct}%)

Please provide:
1. **Portfolio Health Check** (diversification, concentration risk)
2. **Top Performers & Laggards**
3. **Sector Allocation** (is it balanced?)
4. **Tax Efficiency Tips** (LTCG/STCG implications)
5. **Suggestions** (rebalancing ideas, not financial advice)

Use Indian market context and ₹ amounts throughout."""),
    ])


# ── News Summary Prompt ───────────────────────────────────────

def get_news_summary_prompt() -> ChatPromptTemplate:
    """Prompt for summarizing news and extracting market themes."""
    return ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_AGENT_SYSTEM),
        ("human", """Summarize these recent news articles about {company_name} ({symbol}) 
and extract key investment themes:

**Articles:**
{articles}

**Overall Sentiment Score:** {sentiment_score} ({sentiment_label})

Provide:
1. **Key Themes** (what's driving sentiment — 3 bullet points)
2. **Potential Impact** on stock price (positive/negative catalysts)
3. **Watch Points** (what investors should monitor)

Keep it to 150 words maximum. Use market-relevant language."""),
    ])
