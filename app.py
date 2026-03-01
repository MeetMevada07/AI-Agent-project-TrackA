# ============================================================
# app.py
# FinSaarthi 🇮🇳 — Indian Stock Market Financial Agent
# Main Streamlit entry point
#
# Run: streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import time
import os

# ── Page Config (must be first Streamlit call) ────────────────
st.set_page_config(
    page_title="FinSaarthi — Indian Stock Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after page config) ───────────────────────────────
from config.settings import settings
from database.db_manager import (
    initialize_database, add_to_watchlist, remove_from_watchlist,
    get_watchlist, add_to_portfolio, get_portfolio, remove_from_portfolio,
)
from tools.stock_tools import (
    get_stock_price, get_historical_data, calculate_sip,
    calculate_tax_implications,
)
from tools.news_tools import get_news_with_sentiment
from agents.financial_agent import FinancialAgent
from ui.charts import (
    create_candlestick_chart, create_comparison_chart,
    create_sentiment_gauge, create_portfolio_pie, create_sip_chart,
    create_macd_chart,
)
from utils import is_market_open, validate_symbol, format_inr, export_analysis_to_pdf

# ── Database Init ─────────────────────────────────────────────
initialize_database()
os.makedirs("data", exist_ok=True)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0e1117; }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Positive/negative colors */
    .positive { color: #26a69a !important; }
    .negative { color: #ef5350 !important; }
    
    /* Card style */
    .finance-card {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #0d47a1, #1976d2);
        padding: 8px 16px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        font-size: 16px;
        margin: 12px 0;
    }
    
    /* Hide streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat messages */
    .chat-message {
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
    }
    .user-message { background: #1a237e; text-align: right; }
    .ai-message { background: #1b5e20; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_error" not in st.session_state:
    st.session_state.agent_error = None


def get_agent() -> FinancialAgent:
    """Get or initialize the financial agent (cached in session)."""
    if st.session_state.agent is None:
        try:
            st.session_state.agent = FinancialAgent()
            st.session_state.agent_error = None
        except Exception as e:
            st.session_state.agent_error = str(e)
    return st.session_state.agent


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 28px; margin: 0;'>📈 FinSaarthi</h1>
        <p style='color: #888; font-size: 12px;'>Indian Stock Market AI Agent</p>
    </div>
    """, unsafe_allow_html=True)

    # Market Status
    market_info = is_market_open()
    st.info(f"{market_info['status']}\n\n{market_info['current_time_ist']}")

    st.divider()

    # Navigation
    page = st.radio(
        "Navigate",
        options=[
            "🤖 AI Chat",
            "📊 Stock Analysis",
            "🔄 Compare Stocks",
            "📰 News & Sentiment",
            "💼 Portfolio Tracker",
            "⭐ Watchlist",
            "🧮 Calculators",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Quick Stock Picker
    st.markdown("**⚡ Quick Stocks**")
    popular_cols = st.columns(2)
    quick_symbols = list(settings.POPULAR_STOCKS.keys())[:8]

    for i, sym in enumerate(quick_symbols):
        col = popular_cols[i % 2]
        short = sym.replace(".NS", "")
        if col.button(short, key=f"quick_{sym}", width="stretch"):
            st.session_state["selected_symbol"] = sym
            st.rerun()

    st.divider()

    # API Status
    st.markdown("**⚙️ Configuration**")
    llm_ok = bool(settings.GROQ_API_KEY or settings.OPENAI_API_KEY)
    news_ok = bool(settings.NEWS_API_KEY)

    st.markdown(
     f"LLM: {'✅' if llm_ok else '❌ Set in .env'} `{settings.LLM_PROVIDER.upper()}`\n\n"
     f"News: {'✅' if news_ok else '⚠️ Mock data'} `NEWSAPI`"
 )


# ══════════════════════════════════════════════════════════════
# PAGE: AI CHAT
# ══════════════════════════════════════════════════════════════

if page == "🤖 AI Chat":
    st.markdown('<div class="section-header">🤖 FinSaarthi AI Chat</div>',
                unsafe_allow_html=True)
    st.caption("Ask anything about Indian stocks, markets, investing, and personal finance")

    # Show error if LLM not configured
    if st.session_state.agent_error:
        st.error(f"⚠️ LLM Not Configured: {st.session_state.agent_error}\n\n"
                 "Please set your API key in `.env` file.")

    # Chat history display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="📈"):
                    st.write(msg["content"])

    # Quick question buttons
    st.markdown("**💡 Try these questions:**")
    col1, col2, col3 = st.columns(3)
    quick_qs = [
        ("TCS Analysis", "Give me a quick analysis of TCS.NS stock"),
        ("Compare IT stocks", "Compare TCS vs Infosys vs Wipro for long-term investment"),
        ("Nifty outlook", "What's the current outlook for Nifty 50?"),
        ("HDFC Bank", "What are the key fundamentals of HDFC Bank?"),
        ("SIP advice", "I want to start a SIP of ₹5000/month. What should I know?"),
        ("LTCG rules", "Explain LTCG and STCG tax rules for stocks in India"),
    ]
    for i, (label, question) in enumerate(quick_qs):
        col = [col1, col2, col3][i % 3]
        if col.button(label, key=f"qq_{i}", width="stretch"):
            st.session_state["prefill_question"] = question
            st.rerun()

    # Chat input
    prefill = st.session_state.pop("prefill_question", "")
    user_input = st.chat_input("Ask about stocks, investing, or Indian markets...",
                               key="chat_input")

    if user_input or prefill:
        question = user_input or prefill
        st.session_state.chat_history.append({"role": "user", "content": question})

        agent = get_agent()
        if agent:
            with st.spinner("FinSaarthi is thinking... 🤔"):
                response = agent.chat(question)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "⚠️ Please configure your LLM API key in the `.env` file to use AI chat."
            })
        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History", width="stretch"):
            st.session_state.chat_history = []
            if st.session_state.agent:
                st.session_state.agent.clear_memory()
            st.rerun()


# ══════════════════════════════════════════════════════════════
# PAGE: STOCK ANALYSIS
# ══════════════════════════════════════════════════════════════

elif page == "📊 Stock Analysis":
    st.markdown('<div class="section-header">📊 Stock Analysis</div>',
                unsafe_allow_html=True)

    # Symbol input
    col_input, col_period, col_btn = st.columns([3, 2, 1])
    default_symbol = st.session_state.get("selected_symbol", "RELIANCE.NS")

    with col_input:
        symbol_raw = st.text_input(
            "Stock Symbol",
            value=default_symbol,
            placeholder="e.g., RELIANCE.NS, TCS.NS, INFY.NS",
            help="NSE stocks: add .NS suffix | BSE stocks: add .BO suffix",
        )
    with col_period:
        period = st.selectbox(
            "Chart Period",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=2,
            format_func=lambda x: {
                "1mo": "1 Month", "3mo": "3 Months", "6mo": "6 Months",
                "1y": "1 Year", "2y": "2 Years", "5y": "5 Years"
            }[x],
        )
    with col_btn:
        analyze_btn = st.button("🔍 Analyze", width="stretch", type="primary")

    # Chart overlays
    col_sma, col_bb, col_macd = st.columns(3)
    show_sma = col_sma.checkbox("SMA 20/50", value=True)
    show_bb = col_bb.checkbox("Bollinger Bands", value=False)
    show_macd = col_macd.checkbox("Show MACD", value=False)

    # Validate symbol
    is_valid, normalized_symbol = validate_symbol(symbol_raw)
    if not is_valid:
        st.error(f"❌ Invalid symbol: {symbol_raw}. Try formats like RELIANCE.NS or TCS.NS")
    elif analyze_btn or st.session_state.get("auto_analyze_symbol") == normalized_symbol:

        st.session_state["auto_analyze_symbol"] = normalized_symbol
        st.session_state["selected_symbol"] = normalized_symbol

        with st.spinner(f"⏳ Fetching data for {normalized_symbol}..."):
            # Quick price data (fast)
            price_data = get_stock_price(normalized_symbol)

        if "error" in price_data:
            st.error(f"❌ {price_data['error']}")
        else:
            company_name = price_data.get("company_name", normalized_symbol)

            # ── Price Cards ──────────────────────────────────
            st.markdown(f"### {company_name}")
            m1, m2, m3, m4, m5 = st.columns(5)

            price = price_data["current_price"]
            change = price_data["change"]
            change_pct = price_data["change_pct"]
            delta_color = "normal" if change >= 0 else "inverse"

            m1.metric("💰 Price", f"₹{price:,.2f}",
                      f"{'+' if change >= 0 else ''}{change:.2f} ({change_pct:+.2f}%)")
            m2.metric("📉 Prev Close", f"₹{price_data['previous_close']:,.2f}")
            m3.metric("📊 52W High", f"₹{price_data.get('52_week_high', 'N/A')}")
            m4.metric("📊 52W Low", f"₹{price_data.get('52_week_low', 'N/A')}")
            m5.metric("P/E Ratio", str(price_data.get("pe_ratio", "N/A")))

            # ── Candlestick Chart ────────────────────────────
            with st.spinner("Loading chart..."):
                df = get_historical_data(normalized_symbol, period=period)
                if not df.empty:
                    fig = create_candlestick_chart(df, normalized_symbol, show_sma, show_bb)
                    st.plotly_chart(fig, width="stretch")

                    if show_macd:
                        macd_fig = create_macd_chart(df, normalized_symbol)
                        st.plotly_chart(macd_fig, width="stretch")

            # ── Fundamentals ─────────────────────────────────
            with st.expander("📋 Fundamental Metrics", expanded=True):
                from tools.stock_tools import get_fundamental_analysis
                fund_data = get_fundamental_analysis(normalized_symbol)

                if "error" not in fund_data:
                    fc1, fc2, fc3 = st.columns(3)

                    with fc1:
                        st.markdown("**📊 Valuation**")
                        st.write(f"P/E Ratio: `{fund_data.get('pe_ratio', 'N/A')}`")
                        st.write(f"P/B Ratio: `{fund_data.get('pb_ratio', 'N/A')}`")
                        st.write(f"EV/EBITDA: `{fund_data.get('ev_ebitda', 'N/A')}`")
                        st.write(f"EPS: `₹{fund_data.get('eps', 'N/A')}`")

                    with fc2:
                        st.markdown("**💪 Profitability**")
                        roe = fund_data.get('roe', 'N/A')
                        roa = fund_data.get('roa', 'N/A')
                        margins = fund_data.get('profit_margins', 'N/A')
                        st.write(f"ROE: `{f'{roe:.1%}' if isinstance(roe, float) else roe}`")
                        st.write(f"ROA: `{f'{roa:.1%}' if isinstance(roa, float) else roa}`")
                        st.write(f"Net Margin: `{f'{margins:.1%}' if isinstance(margins, float) else margins}`")
                        st.write(f"Revenue Growth: `{fund_data.get('revenue_growth', 'N/A')}`")

                    with fc3:
                        st.markdown("**🏦 Financial Health**")
                        st.write(f"D/E Ratio: `{fund_data.get('debt_to_equity', 'N/A')}`")
                        st.write(f"Current Ratio: `{fund_data.get('current_ratio', 'N/A')}`")
                        st.write(f"Div Yield: `{fund_data.get('dividend_yield', 'N/A')}`")
                        mktcap = fund_data.get('market_cap_cr', 'N/A')
                        st.write(f"Mkt Cap: `₹{f'{mktcap:,.0f} Cr' if isinstance(mktcap, float) else mktcap}`")

            # ── AI Analysis ──────────────────────────────────
            with st.expander("🤖 AI Analysis Report", expanded=False):
                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    with st.spinner("🤖 AI is analyzing..."):
                        result = agent.analyze_stock(normalized_symbol)
                    if "error" not in result:
                        st.markdown(result["ai_analysis"])

                        # PDF Download
                        pdf_bytes = export_analysis_to_pdf(
                            normalized_symbol, company_name,
                            price_data, result.get("fundamental_data", {}),
                            result["ai_analysis"]
                        )
                        st.download_button(
                            "📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"{normalized_symbol}_analysis.pdf",
                            mime="application/pdf",
                        )
                    else:
                        st.error(result["error"])
                else:
                    st.info("Configure LLM API key for AI analysis.")

            # ── Add to Watchlist ─────────────────────────────
            if st.button(f"⭐ Add {normalized_symbol} to Watchlist"):
                result = add_to_watchlist(normalized_symbol, company_name)
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.warning(result["message"])


# ══════════════════════════════════════════════════════════════
# PAGE: COMPARE STOCKS
# ══════════════════════════════════════════════════════════════

elif page == "🔄 Compare Stocks":
    st.markdown('<div class="section-header">🔄 Compare Stocks</div>',
                unsafe_allow_html=True)

    # Sector quick-select
    st.markdown("**Quick sector comparison:**")
    sector_cols = st.columns(len(settings.SECTORS))
    selected_sector_symbols = []

    for i, (sector_name, syms) in enumerate(settings.SECTORS.items()):
        if sector_cols[i].button(sector_name, width="stretch"):
            st.session_state["compare_symbols"] = ", ".join(syms[:3])
            st.rerun()

    # Manual input
    default_compare = st.session_state.get("compare_symbols", "TCS.NS, INFY.NS, WIPRO.NS")
    symbols_input = st.text_input(
        "Enter stock symbols (comma-separated)",
        value=default_compare,
        placeholder="TCS.NS, INFY.NS, WIPRO.NS",
    )

    col_btn1, col_btn2 = st.columns([1, 4])
    compare_btn = col_btn1.button("🔄 Compare", type="primary", width="stretch")

    if compare_btn:
        raw_symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]

        # Validate all symbols
        valid_symbols = []
        for s in raw_symbols[:5]:  # Max 5 stocks
            is_valid, normalized = validate_symbol(s)
            if is_valid:
                valid_symbols.append(normalized)
            else:
                st.warning(f"⚠️ Skipping invalid symbol: {s}")

        if len(valid_symbols) < 2:
            st.error("Please enter at least 2 valid stock symbols")
        else:
            with st.spinner("Fetching comparison data..."):
                from tools.stock_tools import compare_stocks
                df = compare_stocks(valid_symbols)

            if not df.empty:
                st.markdown("### 📊 Side-by-Side Comparison")
                
                # Color-code the dataframe
                def color_change(val):
                    if isinstance(val, (int, float)):
                        color = "#26a69a" if val > 0 else "#ef5350" if val < 0 else "white"
                        return f"color: {color}"
                    return ""

                styled_df = df.style.applymap(
                    color_change,
                    subset=["Change %", "ROE %"] if "Change %" in df.columns else []
                )
                st.dataframe(styled_df, width="stretch", hide_index=True)

                # Performance chart
                st.markdown("### 📈 6-Month Performance (Normalized)")
                with st.spinner("Loading performance chart..."):
                    perf_fig = create_comparison_chart(valid_symbols, df)
                    st.plotly_chart(perf_fig, width="stretch")

                # AI comparison
                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    with st.expander("🤖 AI Comparison Analysis", expanded=True):
                        with st.spinner("AI is comparing..."):
                            result = agent.compare_stocks_with_ai(valid_symbols)
                        if "error" not in result:
                            st.markdown(result["ai_commentary"])
            else:
                st.error("Could not fetch comparison data. Check symbols.")


# ══════════════════════════════════════════════════════════════
# PAGE: NEWS & SENTIMENT
# ══════════════════════════════════════════════════════════════

elif page == "📰 News & Sentiment":
    st.markdown('<div class="section-header">📰 News & Sentiment Analysis</div>',
                unsafe_allow_html=True)

    col_sym, col_btn = st.columns([3, 1])
    symbol_news = col_sym.text_input(
        "Stock Symbol",
        value=st.session_state.get("selected_symbol", "RELIANCE.NS"),
        placeholder="RELIANCE.NS",
    )
    fetch_news_btn = col_btn.button("📰 Get News", type="primary", width="stretch")

    if fetch_news_btn:
        is_valid, normalized = validate_symbol(symbol_news)
        if not is_valid:
            st.error(f"Invalid symbol: {symbol_news}")
        else:
            price_info = get_stock_price(normalized)
            company_name = price_info.get("company_name", normalized) if "error" not in price_info else normalized

            with st.spinner("Fetching news and analyzing sentiment..."):
                news_result = get_news_with_sentiment(normalized, company_name)

            # Sentiment gauge
            col_gauge, col_stats = st.columns([2, 3])

            with col_gauge:
                st.markdown(f"### Sentiment for {company_name}")
                gauge_fig = create_sentiment_gauge(news_result["avg_score"])
                st.plotly_chart(gauge_fig, width="stretch")
                st.markdown(f"**Overall: {news_result['overall_sentiment']}**")

            with col_stats:
                st.markdown("### Sentiment Breakdown")
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("✅ Positive", news_result["pos_count"])
                sc2.metric("⚠️ Neutral", news_result["neu_count"])
                sc3.metric("❌ Negative", news_result["neg_count"])

                st.info(news_result["summary"])

            # Article cards
            st.markdown("### 📋 Recent Articles")
            for i, article in enumerate(news_result["articles"]):
                sentiment = article.get("sentiment", {})
                label = sentiment.get("label", "N/A")
                score = sentiment.get("compound", 0)
                color = sentiment.get("color", "gray")

                with st.expander(f"{article.get('published_at', '')} — {article.get('title', 'No Title')[:80]}"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(article.get("description", "No description available"))
                        st.caption(f"Source: {article.get('source', 'Unknown')}")
                        if article.get("url") and article["url"] != "#":
                            st.markdown(f"[Read Full Article →]({article['url']})")
                    with col_b:
                        st.metric("Sentiment", label, f"Score: {score:.3f}")

            # AI News Summary
            agent = get_agent()
            if agent and not st.session_state.agent_error:
                with st.expander("🤖 AI News Summary", expanded=False):
                    from prompts import get_news_summary_prompt
                    from langchain.chains import LLMChain
                    try:
                        articles_text = "\n".join([
                            f"- {a.get('title', '')} ({a.get('published_at', '')})"
                            for a in news_result["articles"][:5]
                        ])
                        prompt = get_news_summary_prompt()
                        chain = LLMChain(llm=agent.llm, prompt=prompt)
                        with st.spinner("AI summarizing..."):
                            response = chain.invoke({
                                "symbol": normalized,
                                "company_name": company_name,
                                "articles": articles_text,
                                "sentiment_score": news_result["avg_score"],
                                "sentiment_label": news_result["overall_sentiment"],
                            })
                        st.markdown(response["text"])
                    except Exception as e:
                        st.error(f"AI summary failed: {e}")


# ══════════════════════════════════════════════════════════════
# PAGE: PORTFOLIO TRACKER
# ══════════════════════════════════════════════════════════════

elif page == "💼 Portfolio Tracker":
    st.markdown('<div class="section-header">💼 Portfolio Tracker</div>',
                unsafe_allow_html=True)

    tab_view, tab_add = st.tabs(["📊 My Portfolio", "➕ Add Holding"])

    with tab_add:
        st.markdown("### Add New Holding")
        with st.form("add_holding_form"):
            fc1, fc2 = st.columns(2)
            sym = fc1.text_input("Symbol", placeholder="RELIANCE.NS")
            company = fc2.text_input("Company Name", placeholder="Reliance Industries")
            
            fc3, fc4, fc5 = st.columns(3)
            qty = fc3.number_input("Quantity (shares)", min_value=1, value=10)
            buy_px = fc4.number_input("Buy Price (₹)", min_value=0.01, value=1000.0, step=0.01)
            buy_date = fc5.date_input("Buy Date")
            
            notes = st.text_area("Notes (optional)", height=80)
            submitted = st.form_submit_button("➕ Add to Portfolio", type="primary")

            if submitted:
                if sym and buy_px > 0:
                    is_valid, norm_sym = validate_symbol(sym)
                    if is_valid:
                        result = add_to_portfolio(
                            norm_sym, company, float(buy_px),
                            int(qty), str(buy_date), notes
                        )
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.error("Invalid symbol")
                else:
                    st.error("Please fill in all required fields")

    with tab_view:
        holdings = get_portfolio()

        if not holdings:
            st.info("📭 Your portfolio is empty. Add holdings in the 'Add Holding' tab.")
        else:
            # Fetch current prices
            with st.spinner("Fetching current prices..."):
                current_prices = {}
                for h in holdings:
                    price_data = get_stock_price(h["symbol"])
                    if "error" not in price_data:
                        current_prices[h["symbol"]] = price_data["current_price"]
                    else:
                        current_prices[h["symbol"]] = h["buy_price"]

            # Calculate P&L
            rows = []
            total_invested = 0
            total_current = 0

            for h in holdings:
                symbol = h["symbol"]
                buy_price = h["buy_price"]
                quantity = h["quantity"]
                current = current_prices.get(symbol, buy_price)

                invested = buy_price * quantity
                current_val = current * quantity
                pnl = current_val - invested
                pnl_pct = (pnl / invested) * 100 if invested else 0

                total_invested += invested
                total_current += current_val

                rows.append({
                    "ID": h["id"],
                    "Symbol": symbol,
                    "Company": h.get("company_name", "")[:15],
                    "Qty": quantity,
                    "Buy ₹": f"{buy_price:,.2f}",
                    "Now ₹": f"{current:,.2f}",
                    "Invested ₹": f"{invested:,.2f}",
                    "Value ₹": f"{current_val:,.2f}",
                    "P&L ₹": f"{'+'  if pnl >= 0 else ''}{pnl:,.2f}",
                    "Return %": f"{pnl_pct:+.2f}%",
                })

            # Summary metrics
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric("💰 Invested", f"₹{total_invested:,.0f}")
            pm2.metric("📈 Current Value", f"₹{total_current:,.0f}")
            pm3.metric("💵 Total P&L", f"₹{total_pnl:+,.0f}", f"{total_pnl_pct:+.2f}%")
            pm4.metric("📊 Holdings", len(holdings))

            # Portfolio table
            df = pd.DataFrame([{k: v for k, v in r.items() if k != "ID"} for r in rows])
            st.dataframe(df, width="stretch", hide_index=True)

            # Pie chart
            col_pie, col_analysis = st.columns([2, 3])
            with col_pie:
                import plotly.express as px
                pie_df = pd.DataFrame({
                    "Symbol": [r["Symbol"] for r in rows],
                    "Value (₹)": [float(h["buy_price"] * h["quantity"])
                                   for h in holdings],
                })
                pie_fig = create_portfolio_pie(pie_df)
                st.plotly_chart(pie_fig, width="stretch")

            # AI Portfolio Analysis
            with col_analysis:
                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    if st.button("🤖 AI Portfolio Analysis", type="primary"):
                        with st.spinner("Analyzing portfolio..."):
                            result = agent.analyze_portfolio_with_ai(holdings, current_prices)
                        if "error" not in result:
                            st.markdown(result["ai_analysis"])

            # Remove holdings
            st.markdown("### 🗑️ Remove Holding")
            del_col1, del_col2 = st.columns([3, 1])
            holding_options = {f"{r['Symbol']} (ID: {r['ID']})": r['ID'] for r in rows}
            selected_del = del_col1.selectbox("Select holding to remove",
                                               options=list(holding_options.keys()))
            if del_col2.button("Remove", type="secondary"):
                hid = holding_options[selected_del]
                result = remove_from_portfolio(hid)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════
# PAGE: WATCHLIST
# ══════════════════════════════════════════════════════════════

elif page == "⭐ Watchlist":
    st.markdown('<div class="section-header">⭐ Stock Watchlist</div>',
                unsafe_allow_html=True)

    # Add to watchlist
    with st.expander("➕ Add Stock to Watchlist"):
        wc1, wc2, wc3 = st.columns([2, 3, 1])
        w_sym = wc1.text_input("Symbol", placeholder="TATAPOWER.NS")
        w_note = wc2.text_input("Notes (optional)", placeholder="Waiting for pullback")
        if wc3.button("Add", type="primary"):
            if w_sym:
                is_valid, norm = validate_symbol(w_sym)
                if is_valid:
                    price_info = get_stock_price(norm)
                    cname = price_info.get("company_name", norm) if "error" not in price_info else norm
                    result = add_to_watchlist(norm, cname, w_note)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()

    # Display watchlist with live prices
    watchlist = get_watchlist()
    if not watchlist:
        st.info("📭 Your watchlist is empty. Add stocks above or from the Stock Analysis page.")
    else:
        st.markdown(f"### Watching {len(watchlist)} stocks")

        with st.spinner("Loading live prices..."):
            for item in watchlist:
                symbol = item["symbol"]
                price_data = get_stock_price(symbol)

                col_sym, col_price, col_change, col_52wh, col_pe, col_del = st.columns([2, 2, 2, 2, 1, 1])

                col_sym.markdown(f"**{symbol.replace('.NS', '')}**\n\n{item.get('company_name', '')[:18]}")

                if "error" not in price_data:
                    col_price.metric(
                    label="Current Price",
                    value=f"₹{price_data['current_price']:,.2f}",
                    label_visibility="collapsed"
                    )
                    change_pct = price_data["change_pct"]
                    col_change.metric(
                    label="Change %",
                    value=f"{change_pct:+.2f}%",
                    delta_color="normal" if change_pct >= 0 else "inverse",
                    label_visibility="collapsed"
                    )
                    col_52wh.write(f"H: ₹{price_data.get('52_week_high', 'N/A')}\nL: ₹{price_data.get('52_week_low', 'N/A')}")
                    col_pe.write(f"P/E\n{price_data.get('pe_ratio', 'N/A')}")
                else:
                    col_price.warning("N/A")

                if col_del.button("🗑️", key=f"del_wl_{symbol}"):
                    remove_from_watchlist(symbol)
                    st.rerun()

                st.divider()


# ══════════════════════════════════════════════════════════════
# PAGE: CALCULATORS
# ══════════════════════════════════════════════════════════════

elif page == "🧮 Calculators":
    st.markdown('<div class="section-header">🧮 Financial Calculators</div>',
                unsafe_allow_html=True)

    calc_type = st.radio(
        "Calculator",
        ["💰 SIP Calculator", "🏛️ Capital Gains Tax (LTCG/STCG)"],
        horizontal=True,
    )

    # ── SIP Calculator ────────────────────────────────────────
    if calc_type == "💰 SIP Calculator":
        st.markdown("### 💰 SIP Return Calculator")
        st.caption("Systematic Investment Plan — project your mutual fund/stock SIP returns")

        c1, c2, c3 = st.columns(3)
        monthly_sip = c1.number_input("Monthly SIP (₹)", min_value=100, value=5000, step=500)
        annual_return = c2.slider("Expected Annual Return (%)", min_value=4.0, max_value=25.0,
                                   value=12.0, step=0.5)
        years = c3.slider("Investment Duration (Years)", min_value=1, max_value=30, value=10)

        if st.button("📊 Calculate SIP Returns", type="primary"):
            result = calculate_sip(monthly_sip, annual_return, years)

            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.metric("💰 Monthly SIP", f"₹{monthly_sip:,.0f}")
            sr2.metric("📊 Total Invested", f"₹{result['total_invested']:,.0f}")
            sr3.metric("📈 Estimated Returns", f"₹{result['estimated_returns']:,.0f}")
            sr4.metric("🤑 Wealth Gained", f"₹{result['wealth_gained']:,.0f}",
                       f"+{result['absolute_return_pct']:.1f}%")

            sip_fig = create_sip_chart(result["yearly_breakdown"])
            st.plotly_chart(sip_fig, width="stretch")

            # Yearly breakdown table
            with st.expander("📋 Year-by-Year Breakdown"):
                breakdown_df = pd.DataFrame(result["yearly_breakdown"])
                breakdown_df.columns = ["Year", "Invested (₹)", "Value (₹)"]
                breakdown_df["Gain (₹)"] = breakdown_df["Value (₹)"] - breakdown_df["Invested (₹)"]
                breakdown_df["Return %"] = (breakdown_df["Gain (₹)"] / breakdown_df["Invested (₹)"] * 100).round(2)
                st.dataframe(breakdown_df, width="stretch", hide_index=True)

    # ── Tax Calculator ────────────────────────────────────────
    elif calc_type == "🏛️ Capital Gains Tax (LTCG/STCG)":
        st.markdown("### 🏛️ Indian Capital Gains Tax Calculator")
        st.caption("Calculate LTCG (12.5%) and STCG (20%) as per Indian Income Tax Act")

        tc1, tc2, tc3, tc4 = st.columns(4)
        buy_price_tax = tc1.number_input("Buy Price per Share (₹)", min_value=1.0, value=500.0, step=1.0)
        sell_price_tax = tc2.number_input("Sell Price per Share (₹)", min_value=1.0, value=700.0, step=1.0)
        qty_tax = tc3.number_input("Quantity (shares)", min_value=1, value=100)
        holding_days = tc4.number_input("Holding Period (days)", min_value=1, value=400)

        if st.button("🧮 Calculate Tax", type="primary"):
            tax_result = calculate_tax_implications(
                buy_price_tax, sell_price_tax, qty_tax, holding_days
            )

            # Results
            tax_type_color = "#ef5350" if "STCG" in tax_result["tax_type"] else "#ff9800"

            tr1, tr2, tr3 = st.columns(3)
            tr1.metric("💰 Total Investment", f"₹{tax_result['total_investment']:,.2f}")
            tr2.metric("📈 Total Proceeds", f"₹{tax_result['total_proceeds']:,.2f}")
            tr3.metric("💵 Gross Gain/Loss",
                       f"₹{tax_result['gross_gain_loss']:+,.2f}",
                       f"{tax_result['return_pct']:+.2f}%")

            st.markdown(f"""
            <div class='finance-card'>
                <h4 style='color: {tax_type_color}'>📋 {tax_result['tax_type']}</h4>
                <p>Holding Period: <strong>{holding_days} days</strong> 
                   ({'< 1 year → STCG' if holding_days < 365 else '≥ 1 year → LTCG'})</p>
                <p>Tax Rate: <strong>{tax_result['tax_rate_pct']}%</strong></p>
                {'<p>LTCG Exemption: <strong>₹1,25,000</strong></p>' if holding_days >= 365 else ''}
                <hr>
                <h3 style='color: #ef5350'>Tax Payable: ₹{tax_result['tax_payable']:,.2f}</h3>
                <h3 style='color: #26a69a'>Net Gain After Tax: ₹{tax_result['net_gain_after_tax']:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)

            st.caption("⚠️ This is an approximate calculation. Tax rules may change. "
                       "Consult a CA for exact tax computation.")


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
<div style='text-align: center; color: #555; font-size: 12px; padding: 10px;'>
    📈 FinSaarthi — Indian Stock Market AI Agent | 
    Built with LangChain + Streamlit + yfinance | 
    ⚠️ For educational purposes only. Not SEBI-registered financial advice.
</div>
""", unsafe_allow_html=True)
