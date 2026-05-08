# ============================================================
# app.py — FinSaarthi v2.0  |  Premium UI — Final
# ============================================================


import streamlit as st
import pandas as pd
import time
import os
import logging

logger = logging.getLogger(__name__)

# 🔥 Suppress unwanted yfinance + network logs
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)



st.set_page_config(
    page_title="FinSaarthi — AI Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import settings
from database.db_manager import (
    initialize_database, add_to_watchlist, remove_from_watchlist,
    get_watchlist, add_to_portfolio, get_portfolio, remove_from_portfolio,
)
from tools.stock_tools import (
    get_stock_price, get_historical_data, calculate_sip,
    calculate_tax_implications, get_fundamental_analysis,

)
from tools.news_tools import get_news_with_sentiment
from tools.ai_signals import get_trading_signal, get_market_mood, calculate_portfolio_risk, get_top_movers, get_sector_heatmap, get_market_breadth, get_52week_pulse
from agents.financial_agent import FinancialAgent
from agents.market_brief import generate_market_brief, generate_comparison_summary
from ui.charts import (
    create_candlestick_chart, create_comparison_chart,
    create_sentiment_gauge, create_portfolio_pie, create_sip_chart,
    create_macd_chart, create_market_mood_chart, create_risk_meter,
    create_signal_chart, create_pnl_chart,
)
from utils import is_market_open, validate_symbol, format_inr, export_analysis_to_pdf
import streamlit.components.v1 as components

def render_interactive_chart(symbol, height=500, key_prefix="chart"):
    c_hdr, c_int, c_ind = st.columns([2.5, 1.0, 1.5])
    with c_hdr:
        sec_hdr(f"{symbol} — Real-Time Interactive Chart", "blue")
    with c_int:
        st.markdown("<div style='margin-top:0.85rem;'></div>", unsafe_allow_html=True)
        interval_opt = st.selectbox(
            "Interval", 
            ["1m", "5m", "15m", "1h", "1d", "1wk"], 
            index=4, 
            label_visibility="collapsed",
            key=f"chart_interval_{key_prefix}_{symbol}"
        )
    with c_ind:
        st.markdown("<div style='margin-top:0.85rem;'></div>", unsafe_allow_html=True)
        indicators_opt = st.multiselect(
            "Indicators",
            ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "MACD", "RSI"],
            default=[],
            label_visibility="collapsed",
            key=f"chart_ind_{key_prefix}_{symbol}"
        )
    
    period_map = {"1m": "5d", "5m": "1mo", "15m": "1mo", "1h": "1y", "1d": "5y", "1wk": "10y"}
    yf_interval = "60m" if interval_opt == "1h" else interval_opt
    
    with st.spinner("Generating premium chart..."):
        from ui.charts import create_interactive_plotly_chart
        from tools.stock_tools import get_historical_data, calculate_technical_indicators
        
        df_chart = get_historical_data(symbol, period=period_map[interval_opt], interval=yf_interval)
        
        if not df_chart.empty:
            if indicators_opt:
                df_chart = calculate_technical_indicators(df_chart)
            fig = create_interactive_plotly_chart(df_chart, symbol, indicators=indicators_opt)
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_{key_prefix}_{symbol}_{interval_opt}")
        else:
            st.warning("⚠️ No data available for the selected interval.")


initialize_database()
os.makedirs("data", exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  MASTER CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700;800&display=swap");

/* ── DESIGN TOKENS ── */
:root {
  --bg:        #050810;
  --bg2:       #080C16;
  --bg3:       #0C1220;
  --surface:   #0F1729;
  --surface2:  #141E34;
  --surface3:  #192540;
  --border:    #1C2D4F;
  --border2:   #253D68;
  --border3:   #2E4D82;
  --blue:      #3B82F6;
  --blue2:     #60A5FA;
  --blue3:     #1D4ED8;
  --indigo:    #6366F1;
  --cyan:      #06B6D4;
  --teal:      #14B8A6;
  --green:     #10B981;
  --green2:    #34D399;
  --lime:      #84CC16;
  --red:       #EF4444;
  --red2:      #F87171;
  --orange:    #F97316;
  --amber:     #F59E0B;
  --gold:      #FBBF24;
  --purple:    #A855F7;
  --pink:      #EC4899;
  --text:      #F1F5FF;
  --text2:     #94A3C8;
  --text3:     #4B6494;
  --text4:     #2E3F62;
  --r8:        8px;
  --r12:       12px;
  --r16:       16px;
  --r20:       20px;
}

/* ── BASE ── */
*, *::before, *::after { box-sizing: border-box; }
* { font-family: "Space Grotesk", sans-serif !important; }
html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; }
.main .block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }

/* ── SUBTLE NOISE TEXTURE OVERLAY ── */
.stApp::after {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px 200px;
  opacity: 0.4;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: linear-gradient(160deg, #06091A 0%, #040710 60%, #050912 100%) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 4px 0 40px rgba(0,0,0,0.6) !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 0 0.65rem 1.5rem !important;
  overflow: hidden !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; overflow: hidden !important; }
[data-testid="stSidebar"] > div:first-child > div:first-child {
  height: 0 !important; min-height: 0 !important;
  overflow: visible !important; position: relative !important;
  padding: 0 !important; margin: 0 !important;
}
[data-testid="stSidebar"] > div:first-child > div:first-child > div {
  position: absolute !important; top: 0.5rem !important; right: -0.1rem !important; z-index: 9999 !important;
}

/* NAV radio */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 1px !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] { width:100% !important; padding:0 !important; margin:0 !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display:none !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:last-child {
  background: transparent !important;
  border-radius: var(--r8) !important;
  padding: 0.17rem 0.8rem !important;
  cursor: pointer !important; width: 100% !important;
  transition: all 0.15s ease !important;
  color: var(--text3) !important;
  font-size: 0.83rem !important; font-weight: 500 !important;
  border: 1px solid transparent !important;
  letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:hover > div:last-child {
  background: rgba(59,130,246,0.08) !important;
  color: var(--text2) !important; border-color: rgba(59,130,246,0.2) !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"][aria-checked="true"] > div:last-child {
  background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(99,102,241,0.1)) !important;
  color: var(--text) !important; font-weight: 600 !important;
  border-color: rgba(59,130,246,0.4) !important;
  box-shadow: 0 2px 20px rgba(59,130,246,0.2), inset 0 0 0 1px rgba(59,130,246,0.15) !important;
}

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
  background: linear-gradient(145deg, var(--surface) 0%, var(--bg3) 100%) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r16) !important;
  padding: 1.1rem 1.3rem 1rem !important;
  transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
  position: relative !important; overflow: hidden !important;
}
[data-testid="metric-container"]::before {
  content: '' !important; position: absolute !important;
  inset: 0 !important; border-radius: var(--r16) !important;
  background: linear-gradient(135deg, rgba(59,130,246,0.06) 0%, transparent 60%) !important;
  pointer-events: none !important;
}
[data-testid="metric-container"]:hover {
  border-color: rgba(59,130,246,0.5) !important;
  transform: translateY(-3px) !important;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(59,130,246,0.2) !important;
}
[data-testid="stMetricValue"] {
  font-family: "Outfit", sans-serif !important;
  font-size: 1.55rem !important; font-weight: 800 !important;
  color: var(--text) !important; letter-spacing: -0.6px !important; line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.6rem !important; color: var(--text3) !important;
  text-transform: uppercase !important; letter-spacing: 0.14em !important; font-weight: 500 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 700 !important; }
[data-testid="stMetricDeltaIcon"] { display: none !important; }

/* ── FIN-CARD ── */
.fin-card {
  background: linear-gradient(145deg, var(--surface) 0%, var(--bg3) 100%);
  border: 1px solid var(--border);
  border-radius: var(--r16); padding: 1.2rem 1.4rem;
  position: relative; overflow: hidden;
  transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
}
.fin-card::before {
  content: ''; position: absolute; inset: 0; border-radius: var(--r16);
  background: linear-gradient(135deg, rgba(59,130,246,0.05) 0%, transparent 70%);
  pointer-events: none;
}
.fin-card:hover { border-color: var(--border2); box-shadow: 0 8px 40px rgba(0,0,0,0.4); transform: translateY(-2px); }

.fin-card-glow-green { border-color: rgba(16,185,129,0.35) !important; background: linear-gradient(145deg, rgba(16,185,129,0.07), var(--bg3)) !important; }
.fin-card-glow-red   { border-color: rgba(239,68,68,0.35) !important;   background: linear-gradient(145deg, rgba(239,68,68,0.07),   var(--bg3)) !important; }
.fin-card-glow-blue  { border-color: rgba(59,130,246,0.35) !important;  background: linear-gradient(145deg, rgba(59,130,246,0.07),  var(--bg3)) !important; }
.fin-card-glow-amber { border-color: rgba(245,158,11,0.35) !important;  background: linear-gradient(145deg, rgba(245,158,11,0.07),  var(--bg3)) !important; }

/* ── GLASS CARD ── */
.glass-card {
  background: rgba(15,23,41,0.7);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: var(--r16); padding: 1.2rem 1.4rem;
}

/* ── SIGNAL CARDS ── */
.signal-buy  { background: linear-gradient(145deg,rgba(5,46,22,0.9),rgba(6,78,59,0.5));  border:1px solid rgba(16,185,129,0.5);  border-radius:var(--r16); padding:1.2rem; text-align:center; }
.signal-sell { background: linear-gradient(145deg,rgba(69,10,10,0.9),rgba(127,29,29,0.5)); border:1px solid rgba(239,68,68,0.5);   border-radius:var(--r16); padding:1.2rem; text-align:center; }
.signal-hold { background: linear-gradient(145deg,rgba(69,49,0,0.9),rgba(120,53,15,0.5)); border:1px solid rgba(245,158,11,0.5);  border-radius:var(--r16); padding:1.2rem; text-align:center; }

/* ── TICKER CARD ── */
.ticker-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r12); padding: 0.65rem 1rem; margin: 4px 0;
  display: flex; align-items: center; justify-content: space-between;
  transition: all 0.16s ease; cursor: default;
  position: relative; overflow: hidden;
}
.ticker-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; border-radius: 3px 0 0 3px;
  background: transparent; transition: background 0.16s;
}
.ticker-card:hover { border-color: var(--border2); background: var(--surface2); transform: translateX(4px); }
.ticker-card.gain::after { background: var(--green); }
.ticker-card.loss::after { background: var(--red); }
.ticker-card.gain:hover { border-color: rgba(16,185,129,0.4); }
.ticker-card.loss:hover { border-color: rgba(239,68,68,0.4); }

/* ── SECTION HEADER ── */
.sec-hdr {
  display: flex; align-items: center; gap: 10px;
  margin: 0.85rem 0 0.65rem;
}
.sec-hdr-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--blue); flex-shrink: 0;
  box-shadow: 0 0 12px rgba(59,130,246,0.8);
}
.sec-hdr-dot.green { background: var(--green); box-shadow: 0 0 12px rgba(16,185,129,0.8); }
.sec-hdr-dot.red   { background: var(--red);   box-shadow: 0 0 12px rgba(239,68,68,0.8); }
.sec-hdr-dot.amber { background: var(--amber);  box-shadow: 0 0 12px rgba(245,158,11,0.8); }
.sec-hdr-dot.purple{ background: var(--purple); box-shadow: 0 0 12px rgba(168,85,247,0.8); }
.sec-hdr-label {
  font-family: "Outfit", sans-serif !important;
  font-size: 0.8rem; font-weight: 700; color: var(--text2);
  text-transform: uppercase; letter-spacing: 0.08em;
  flex: 1;
}
.sec-hdr::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); max-width: 200px; }

/* ── PAGE HEADER ── */
.pg-header { margin-bottom: 1.6rem; }
.pg-eyebrow {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.6rem; color: var(--blue2);
  text-transform: uppercase; letter-spacing: 0.2em;
  margin-bottom: 0.3rem; opacity: 0.9;
}
.pg-title {
  font-family: "Outfit", sans-serif !important;
  font-size: 2.1rem; font-weight: 800; color: var(--text);
  letter-spacing: -0.8px; line-height: 1.1; margin-bottom: 0.3rem;
}
.pg-sub { font-size: 0.84rem; color: var(--text3); letter-spacing: 0.01em; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r12) !important;
  padding: 4px !important; gap: 2px !important;
  width: fit-content !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 9px !important; color: var(--text3) !important;
  font-weight: 600 !important; font-size: 0.82rem !important;
  padding: 0.42rem 1.1rem !important; background: transparent !important;
  border: none !important; letter-spacing: 0.01em !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--blue3), var(--blue)) !important;
  color: white !important; box-shadow: 0 2px 16px rgba(59,130,246,0.45) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  border-radius: var(--r8) !important;
  font-family: "Outfit", sans-serif !important;
  font-weight: 700 !important; font-size: 0.8rem !important;
  letter-spacing: 0.04em !important;
  transition: all 0.18s cubic-bezier(0.4,0,0.2,1) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--blue3), var(--blue)) !important;
  color: white !important; border: none !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 30px rgba(59,130,246,0.55) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface2) !important; color: var(--text2) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--border2) !important; color: var(--text) !important; background: var(--surface3) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r8) !important; color: var(--text) !important;
  font-family: "Space Grotesk", sans-serif !important; font-size: 0.88rem !important;
  transition: border-color 0.18s, box-shadow 0.18s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}
.stSelectbox > div > div {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r8) !important; color: var(--text) !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stDateInput label, .stCheckbox label, .stSlider label {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.62rem !important; color: var(--text2) !important;
  text-transform: uppercase !important; letter-spacing: 0.12em !important; font-weight: 500 !important;
}

/* ── RADIO ── */
.stRadio > div { gap: 0.5rem !important; }
.stRadio [data-baseweb="radio"] > div:first-child > div {
  background: var(--surface) !important; border-color: var(--border2) !important;
}
.stRadio [data-baseweb="radio"][aria-checked="true"] > div:first-child > div {
  background: var(--blue) !important; border-color: var(--blue) !important;
}

/* ── CHECKBOX ── */
.stCheckbox > label > div[data-testid="stCheckbox"] {
  background: var(--surface) !important; border-color: var(--border2) !important;
  border-radius: 5px !important;
}

/* ── SLIDER ── */
.stSlider > div > div > div > div { background: var(--blue) !important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r12) !important; color: var(--text2) !important;
  font-weight: 600 !important; font-size: 0.84rem !important;
  padding: 0.7rem 1rem !important;
}
.streamlit-expanderHeader:hover { border-color: var(--border2) !important; color: var(--text) !important; }
.streamlit-expanderContent {
  background: var(--bg3) !important; border: 1px solid var(--border) !important;
  border-top: none !important; border-radius: 0 0 var(--r12) var(--r12) !important; padding: 1rem !important;
}

/* ── DATAFRAME ── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: var(--r12) !important; overflow: hidden !important; }
[data-testid="stDataFrameResizable"] { border-radius: var(--r12) !important; }

/* ── ALERTS ── */
.stAlert { border-radius: var(--r8) !important; }
.stInfo    { background: rgba(59,130,246,0.1) !important;  border: 1px solid rgba(59,130,246,0.3) !important;  color: var(--blue2) !important; }
.stSuccess { background: rgba(16,185,129,0.1) !important;  border: 1px solid rgba(16,185,129,0.3) !important; }
.stError   { background: rgba(239,68,68,0.1) !important;   border: 1px solid rgba(239,68,68,0.3) !important; }
.stWarning { background: rgba(245,158,11,0.1) !important;  border: 1px solid rgba(245,158,11,0.3) !important; }

/* ── CHAT (NEW PREMIUM) ── */
/* Hide default streamlit chat elements on AI Chat page */
.finsaarthi-chat-wrap [data-testid="stChatMessageContent"] { display: none !important; }

/* Custom chat message cards */
.chat-msg-wrap { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 1rem; animation: fadeSlide 0.3s ease; }
.chat-msg-wrap.user-wrap { flex-direction: row-reverse; }
@keyframes fadeSlide { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }

.chat-avatar {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700;
}
.chat-avatar.ai-avatar {
  background: linear-gradient(135deg, #3B82F6, #6366F1);
  box-shadow: 0 4px 15px rgba(99,102,241,0.35);
  color: white;
}
.chat-avatar.user-avatar {
  background: linear-gradient(135deg, #0F1729, #192540);
  border: 1px solid #253D68; color: #60A5FA;
}

.chat-bubble {
  max-width: 75%; padding: 0.85rem 1.1rem;
  border-radius: 16px; font-size: 0.875rem; line-height: 1.7;
  position: relative;
}
.chat-bubble.ai-bubble {
  background: linear-gradient(135deg, rgba(15,23,41,0.95), rgba(20,30,52,0.95));
  border: 1px solid rgba(59,130,246,0.2);
  border-top-left-radius: 4px;
  color: #CBD5E9;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.chat-bubble.user-bubble {
  background: linear-gradient(135deg, rgba(29,78,216,0.4), rgba(99,102,241,0.25));
  border: 1px solid rgba(99,102,241,0.4);
  border-top-right-radius: 4px;
  color: #E2E8F7;
  box-shadow: 0 4px 20px rgba(59,130,246,0.15);
}
.chat-bubble.ai-bubble::before {
  content: ''; position: absolute; top: 10px; left: -8px;
  border: 8px solid transparent;
  border-right-color: rgba(59,130,246,0.2);
  border-left: none;
}
.chat-bubble.user-bubble::before {
  content: ''; position: absolute; top: 10px; right: -8px;
  border: 8px solid transparent;
  border-left-color: rgba(99,102,241,0.4);
  border-right: none;
}
.chat-meta { font-size: 0.68rem; color: var(--text4); margin-top: 4px; }
.user-wrap .chat-meta { text-align: right; }

/* Chat input row - inline, always visible */
.chat-input-row {
  margin-top: 0.6rem;
  margin-bottom: 0.4rem;
}
.chat-input-row .stTextInput > div > div > input {
  background: rgba(15,23,41,0.95) !important;
  border: 1px solid rgba(59,130,246,0.25) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px);
  color: var(--text) !important;
  font-size: 0.9rem !important;
  padding: 0.7rem 1.1rem !important;
  height: 48px !important;
}
.chat-input-row .stTextInput > div > div > input:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15), 0 8px 30px rgba(0,0,0,0.3) !important;
}
.chat-input-row .stButton > button {
  height: 48px !important;
  border-radius: 14px !important;
  font-size: 1.1rem !important;
  background: linear-gradient(135deg, var(--blue3), var(--blue)) !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.4) !important;
}

/* Suggested questions new style */
.suggest-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; margin-bottom: 1.2rem; }
.suggest-card {
  background: rgba(15,23,41,0.8); border: 1px solid rgba(28,45,79,0.8);
  border-radius: 12px; padding: 0.7rem 0.9rem;
  cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center; gap: 8px;
}
.suggest-card:hover {
  border-color: rgba(59,130,246,0.5);
  background: rgba(59,130,246,0.08);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59,130,246,0.12);
}
.suggest-icon { font-size: 1.1rem; flex-shrink: 0; }
.suggest-text { font-size: 0.75rem; font-weight: 500; color: var(--text2); line-height: 1.3; }

/* Chat container scroll area */
.chat-scroll-area {
  height: calc(100vh - 360px); min-height: 400px; overflow-y: auto;
  padding: 1rem; margin-bottom: 0.5rem;
  border-radius: 16px;
  border: 1px solid rgba(28,45,79,0.6);
  background: rgba(8,12,22,0.6);
  backdrop-filter: blur(8px);
  scrollbar-width: thin; scrollbar-color: var(--border) transparent;
}
.chat-scroll-area::-webkit-scrollbar { width: 4px; }
.chat-scroll-area::-webkit-scrollbar-track { background: transparent; }
.chat-scroll-area::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

/* Typing indicator */
.typing-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--blue2); animation: typingBounce 1.2s infinite ease-in-out; margin: 0 2px; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

/* Chat status bar */
.chat-status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.6rem 1rem; border-radius: 12px;
  background: rgba(15,23,41,0.7); border: 1px solid rgba(28,45,79,0.5);
  margin-bottom: 1rem;
}
.chat-status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

/* Welcome state */
.chat-welcome {
  text-align: center; padding: 2.5rem 1rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.8rem;
}
.chat-welcome-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.2));
  border: 1px solid rgba(99,102,241,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.8rem; margin-bottom: 0.5rem;
  box-shadow: 0 8px 30px rgba(99,102,241,0.2);
}
.chat-welcome h3 { font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.2rem; color: var(--text); margin: 0; }
.chat-welcome p { font-size: 0.82rem; color: var(--text3); margin: 0; max-width: 300px; }

/* Quick questions old style - keep for compat */
.quick-q-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-bottom: 1rem; }
.quick-q-item {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r8); padding: 0.5rem 0.85rem;
  font-size: 0.76rem; font-weight: 500; color: var(--text2);
  cursor: pointer; transition: all 0.15s;
}
.quick-q-item:hover { border-color: var(--blue); color: var(--text); background: rgba(59,130,246,0.1); }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
  background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(20,184,166,0.1)) !important;
  border: 1px solid rgba(16,185,129,0.4) !important;
  color: var(--green2) !important; border-radius: var(--r8) !important;
  font-family: "Outfit", sans-serif !important; font-weight: 700 !important;
}
.stDownloadButton > button:hover { background: rgba(16,185,129,0.25) !important; transform: translateY(-1px) !important; }

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--blue) !important; }

/* ── DIVIDER ── */
hr {
  border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--border) 25%, var(--border2) 50%, var(--border) 75%, transparent) !important;
  margin: 1.1rem 0 !important;
}

/* ── MISC ── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
.block-container { position: relative; z-index: 1; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

/* ── BADGE ── */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 6px;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
}
.badge-green { background: rgba(16,185,129,0.15); color: var(--green2); border: 1px solid rgba(16,185,129,0.3); }
.badge-red   { background: rgba(239,68,68,0.15);  color: var(--red2);   border: 1px solid rgba(239,68,68,0.3); }
.badge-blue  { background: rgba(59,130,246,0.15); color: var(--blue2);  border: 1px solid rgba(59,130,246,0.3); }
.badge-amber { background: rgba(245,158,11,0.15); color: var(--gold);   border: 1px solid rgba(245,158,11,0.3); }
.badge-live  { background: rgba(16,185,129,0.18); color: var(--green2); border: 1px solid rgba(16,185,129,0.4);
               animation: blink-live 2s ease-in-out infinite; }
@keyframes blink-live { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

/* ── STAT ROW (fundamental kv) ── */
.stat-row { display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid rgba(28,45,79,0.5); }
.stat-row:last-child { border-bottom:none; }
.stat-key { font-size:0.76rem; color:var(--text2); }
.stat-val { font-family:"JetBrains Mono",monospace !important; font-size:0.8rem; font-weight:600; color:var(--text); }

/* ── MOOD BARS ── */
.mood-bar-outer { display:flex; gap:5px; align-items:flex-end; height:72px; margin:0.75rem 0 0.4rem; }
.mood-bar-wrap  { flex:1; display:flex; flex-direction:column; align-items:center; gap:5px; }
.mood-bar       { width:100%; border-radius:5px 5px 0 0; min-height:4px; transition:height 0.5s ease; }

/* ── PROGRESS BAR ── */
.prog-wrap { margin: 0.35rem 0; }
.prog-label { display:flex; justify-content:space-between; font-size:0.74rem; color:var(--text2); margin-bottom:3px; }
.prog-track { background:var(--border); border-radius:4px; height:6px; overflow:hidden; }
.prog-fill  { height:100%; border-radius:4px; transition:width 0.5s ease; }

/* ── NEWS CARD ── */
.news-item {
  background: var(--surface); border: 1px solid var(--border);
  border-left: 3px solid transparent;
  border-radius: 0 var(--r12) var(--r12) 0;
  padding: 0.9rem 1.1rem; margin: 5px 0;
  transition: all 0.16s ease;
}
.news-item:hover { border-color: var(--border2); background: var(--surface2); transform: translateX(4px); }
.news-item.pos { border-left-color: var(--green); }
.news-item.neg { border-left-color: var(--red); }
.news-item.neu { border-left-color: var(--text3); }

/* ── HOLDING ROW ── */
.holding-hdr {
  display: grid; grid-template-columns: 2fr 0.7fr 1fr 1fr 1.1fr 1.1fr 0.7fr;
  padding: 0.5rem 1rem;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.58rem; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;
  border-bottom: 1px solid var(--border);
}
.holding-row {
  display: grid; grid-template-columns: 2fr 0.7fr 1fr 1fr 1.1fr 1.1fr 0.7fr;
  align-items: center; padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(28,45,79,0.4);
  transition: background 0.15s;
}
.holding-row:hover { background: rgba(59,130,246,0.04); }
.holding-row:last-child { border-bottom: none; }

/* ── WATCHLIST ROW ── */
.wl-hdr {
  display: grid; grid-template-columns: 2fr 1.5fr 1fr 1.8fr 1.2fr 0.6fr;
  padding: 0.5rem 1rem;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.58rem; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;
  border-bottom: 1px solid var(--border);
}
.wl-row {
  display: grid; grid-template-columns: 2fr 1.5fr 1fr 1.8fr 1.2fr 0.6fr;
  align-items: center; padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(28,45,79,0.35);
  transition: background 0.15s;
}
.wl-row:hover { background: rgba(59,130,246,0.03); }
.wl-row:last-child { border-bottom: none; }


/* ── INDEX PILL (top banner) ── */
.idx-pill {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r12); padding: 0.85rem 1.3rem;
  transition: all 0.2s; cursor: default;
  position: relative; overflow: hidden;
}
.idx-pill::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue), var(--cyan), transparent);
  opacity: 0.7;
}
.idx-pill:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.35); }
.idx-pill.green-top::before { background: linear-gradient(90deg, transparent, var(--green), var(--teal), transparent); }
.idx-pill.red-top::before   { background: linear-gradient(90deg, transparent, var(--red), var(--orange), transparent); }

</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────
for key, default in [
    ("agent", None), ("chat_history", []),
    ("agent_error", None), ("selected_symbol", "BTC-USD"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

query_params = st.query_params
if "symbol" in query_params:
    st.session_state["selected_symbol"] = query_params["symbol"]
if "page" in query_params:
    st.session_state["nav_page"] = query_params["page"]
    st.query_params.clear()


def get_agent():
    if st.session_state.agent is None:
        try:
            st.session_state.agent = FinancialAgent()
            st.session_state.agent_error = None
        except Exception as e:
            st.session_state.agent_error = str(e)
    return st.session_state.agent


# ─── HELPER COMPONENTS ────────────────────────────────────
def page_header(eyebrow, title, sub):
    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-eyebrow">⬡ &nbsp;{eyebrow}</div>
      <div class="pg-title">{title}</div>
      <div class="pg-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def sec_hdr(label, dot_color="blue"):
    st.markdown(f"""
    <div class="sec-hdr">
      <div class="sec-hdr-dot {dot_color}"></div>
      <div class="sec-hdr-label">{label}</div>
    </div>""", unsafe_allow_html=True)


def ticker_card(symbol, company, price, change_pct, rank=None):
    arrow  = "▲" if change_pct >= 0 else "▼"
    cc     = "#10B981" if change_pct >= 0 else "#EF4444"
    cls    = "gain" if change_pct >= 0 else "loss"
    rank_html = f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;color:var(--text4);margin-right:10px;">#{rank}</div>' if rank else ''

    st.markdown(f"""
    <div class="ticker-card {cls}" style="cursor:default;">
      {rank_html}
      <div style="flex:1;">
        <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:0.85rem;color:var(--text);line-height:1.2;">{symbol.replace('.NS','')}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:1px;">{company[:22]}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.84rem;font-weight:600;color:var(--text);">₹{price:,.1f}</div>
        <div style="color:{cc};font-weight:700;font-size:0.78rem;margin-top:1px;">{arrow} {abs(change_pct):.2f}%</div>
      </div>
    </div>""", unsafe_allow_html=True)


def prog_bar(label, value_str, pct, color="#3B82F6"):
    st.markdown(f"""
    <div class="prog-wrap">
      <div class="prog-label"><span>{label}</span><span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;">{value_str}</span></div>
      <div class="prog-track"><div class="prog-fill" style="width:{min(pct,100)}%;background:{color};"></div></div>
    </div>""", unsafe_allow_html=True)


def stat_row(key, val, val_color=None):
    col_style = f"color:{val_color};" if val_color else ""
    st.markdown(f"""
    <div class="stat-row">
      <span class="stat-key">{key}</span>
      <span class="stat-val" style="{col_style}">{val}</span>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    market_info = is_market_open()
    is_open     = "Open" in market_info.get("status", "")
    s_color     = "#10B981" if is_open else "#EF4444"
    s_dot       = "🟢" if is_open else "🔴"
    s_label     = "Market Open" if is_open else "Market Closed"

    st.markdown(f"""
    <style>@keyframes pulse-dot{{0%,100%{{box-shadow:0 0 0 0 {s_color}66}}50%{{box-shadow:0 0 0 5px transparent}}}}</style>
    <div style="padding:1.5rem 0.3rem 0.85rem; text-align:center;">
      <!-- Logo -->
      <div style="display:inline-flex;align-items:center;justify-content:center;
                  width:48px;height:48px;border-radius:14px;
                  background:linear-gradient(135deg,#1D4ED8,#3B82F6,#06B6D4);
                  box-shadow:0 0 30px rgba(59,130,246,0.55), 0 0 60px rgba(6,182,212,0.2);
                  margin-bottom:0.75rem; position:relative;">
        <span style="font-size:1.4rem;filter:drop-shadow(0 0 6px rgba(255,255,255,0.3));">📈</span>
      </div>
      <div style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;
                  color:#F1F5FF;letter-spacing:-0.4px;">FinSaarthi</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.55rem;color:#2E3F62;
                  text-transform:uppercase;letter-spacing:0.18em;margin-top:3px;">AI · Stock Intelligence · v2.0</div>
    </div>

    <!-- Market Status Pill -->
    <div style="background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.2);
                border-radius:10px;padding:0.48rem 0.9rem;margin:0 0.1rem 0.85rem;
                display:flex;align-items:center;justify-content:space-between;">
      <div style="display:flex;align-items:center;gap:7px;">
        <div style="width:7px;height:7px;border-radius:50%;background:{s_color};
                    box-shadow:0 0 0 0 {s_color}66;
                    animation:pulse-dot 2s ease-in-out infinite;"></div>
        <span style="color:{s_color};font-weight:700;font-size:0.75rem;">{s_label}</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;color:#2E3F62;font-size:0.62rem;">
        {market_info.get("current_time_ist","")[:8]} IST
      </span>
    </div>

    <div style="height:1px;background:linear-gradient(90deg,transparent,#1C2D4F 30%,#1C2D4F 70%,transparent);margin:0 0.1rem 0.6rem;"></div>

    <!-- Nav labels -->
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.56rem;color:#2E3F62;
                text-transform:uppercase;letter-spacing:0.16em;font-weight:600;
                padding:0.5rem 0.5rem 0.2rem;">Navigation</div>
    """, unsafe_allow_html=True)

    nav_options = [
        "🏠 Dashboard",
        "📊 Stock Analysis",
        "🔄 Compare Stocks",
        "📰 News & Sentiment",
        "💼 Portfolio Tracker",
        "⭐ Watchlist",
        "📋 Market Brief",
        "🧮 Calculators",
        "🤖 AI Chat",
    ]
    nav_index = 0
    if "nav_page" in st.session_state:
        for i, opt in enumerate(nav_options):
            if st.session_state["nav_page"] in opt:
                nav_index = i
                break

    page = st.radio("nav", options=nav_options, index=nav_index, label_visibility="collapsed")

    st.markdown("""
    <div style="margin-top:1.5rem;padding-top:0.85rem;border-top:1px solid #1C2D4F;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:#2E3F62;line-height:1.7;">
        LangChain · Streamlit · yfinance · Plotly
      </div>
      <div style="font-size:0.6rem;color:#7F1D1D;margin-top:4px;line-height:1.5;">
        ⚠️ Not SEBI-registered.<br>Educational purposes only.
      </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  🏠 DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    page_header("Live Overview", "Market Dashboard", "Real-time pulse of Indian equity markets")

    # ── Parallel load ALL dashboard data at once ──────────────
    import concurrent.futures as _cf
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

    _ctx = get_script_run_ctx()  # capture main thread's Streamlit context

    def _safe_ctx(fn, fallback):
        """Run fn in a thread with Streamlit context propagated — suppresses ScriptRunContext warnings."""
        add_script_run_ctx(ctx=_ctx)
        try:
            return fn()
        except Exception:
            return fallback

    _mood_fallback   = {"mood_label":"Neutral ➡️","mood_color":"#F59E0B","mood_score":50,"bullish_pct":40,"neutral_pct":35,"bearish_pct":25,"gainers":0,"losers":0}
    _movers_fallback = {"gainers":[],"losers":[],"all":[]}

    with _cf.ThreadPoolExecutor(max_workers=8) as _ex:
        _f_nifty   = _ex.submit(_safe_ctx, lambda: get_stock_price("^NSEI"),    {"error": "Unavailable"})
        _f_sensex  = _ex.submit(_safe_ctx, lambda: get_stock_price("^BSESN"),   {"error": "Unavailable"})
        _f_mood    = _ex.submit(_safe_ctx, lambda: get_market_mood(),            _mood_fallback)
        _f_movers  = _ex.submit(_safe_ctx, lambda: get_top_movers(),             _movers_fallback)
        _f_heat    = _ex.submit(_safe_ctx, lambda: get_sector_heatmap(),         [])
        _f_pulse   = _ex.submit(_safe_ctx, lambda: get_52week_pulse(),           {"near_high":[],"near_low":[]})
        _f_portf   = _ex.submit(_safe_ctx, lambda: get_portfolio(),              [])
        _f_wl      = _ex.submit(_safe_ctx, lambda: get_watchlist(),              [])

    nifty        = _f_nifty.result()
    sensex       = _f_sensex.result()
    mood_data    = _f_mood.result()
    movers_data  = _f_movers.result()
    heatmap_data = _f_heat.result()
    pulse_data   = _f_pulse.result()
    portfolio    = _f_portf.result()
    wl_items     = _f_wl.result()

    # ── Top 5 index / portfolio metrics ──────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    if "error" not in nifty:
        nifty_cc = "#10B981" if nifty["change_pct"] >= 0 else "#EF4444"
        c1.metric("🔵 Nifty 50", f"{nifty['current_price']:,.2f}", f"{nifty['change_pct']:+.2f}%")
    else:
        c1.metric("🔵 Nifty 50", "N/A", "—")

    if "error" not in sensex:
        c2.metric("🟠 Sensex", f"{sensex['current_price']:,.2f}", f"{sensex['change_pct']:+.2f}%")
    else:
        c2.metric("🟠 Sensex", "N/A", "—")

    c3.metric("🌡️ Mood", mood_data["mood_label"].split(" ")[0], f"{mood_data['mood_score']}% score")

    if portfolio:
        try:
            # Portfolio prices already in cache from batch_fetch_prices — instant
            portf_syms = [h["symbol"] for h in portfolio]
            from tools.stock_tools import batch_fetch_prices as _bfp
            portf_prices = _bfp(portf_syms)
            total_val = sum(portf_prices.get(h["symbol"], {}).get("current_price", h["buy_price"]) * h["quantity"] for h in portfolio)
            total_inv = sum(h["buy_price"] * h["quantity"] for h in portfolio)
            pnl = total_val - total_inv
            c4.metric("💼 Portfolio", f"₹{total_val:,.0f}", f"₹{pnl:+,.0f}")
        except:
            c4.metric("💼 Portfolio", "—", "Refresh")
    else:
        c4.metric("💼 Portfolio", "—", "Add holdings")

    wl_count = len(wl_items)
    c5.metric("📋 Watchlist", wl_count, f"{len(portfolio)} holdings")

    st.markdown("---")

    # ── Row 2: Mood + Heatmap + 52-Week ──────────────────────
    col_mood, col_gain, col_lose = st.columns([1.1, 1.8, 1.8])

    with col_mood:
        sec_hdr("Market Mood", "blue")
        mc    = mood_data["mood_color"]
        bull  = mood_data["bullish_pct"]
        neu   = mood_data["neutral_pct"]
        bear  = mood_data["bearish_pct"]
        score = mood_data["mood_score"]

        # Mood chart (Plotly)
        fig_mood = create_market_mood_chart(score)
        st.plotly_chart(fig_mood, use_container_width=True)

        st.markdown(f"""
        <div class="fin-card" style="text-align:center;padding:0.9rem 1rem;margin-top:0.2rem;">
          <div style="font-family:'Outfit',sans-serif;font-size:1.45rem;font-weight:800;color:{mc};">
            {mood_data["mood_label"]}
          </div>
          <div style="display:flex;justify-content:center;gap:1rem;margin-top:0.6rem;">
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;font-weight:700;color:#10B981;">{bull}%</div>
              <div style="font-size:0.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;">Bull</div>
            </div>
            <div style="width:1px;background:var(--border);"></div>
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;font-weight:700;color:var(--text2);">{neu}%</div>
              <div style="font-size:0.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;">Neu</div>
            </div>
            <div style="width:1px;background:var(--border);"></div>
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;font-weight:700;color:#EF4444;">{bear}%</div>
              <div style="font-size:0.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;">Bear</div>
            </div>
          </div>
          <div style="font-size:0.68rem;color:var(--text3);margin-top:0.5rem;">
            ↑ {mood_data.get("gainers",0)} Advancing &nbsp;·&nbsp; ↓ {mood_data.get("losers",0)} Declining
          </div>
        </div>""", unsafe_allow_html=True)

    # ── SECTOR HEATMAP ───────────────────────────────────────
    with col_gain:
        sec_hdr("Sector Heatmap", "purple")
        if heatmap_data:
            st.markdown('<div class="fin-card" style="padding:0.8rem 1rem; margin-top:0.2rem; height: 100%;">', unsafe_allow_html=True)
            for sec in heatmap_data[:5]:
                c = "#10B981" if sec["avg_change"] >= 0 else "#EF4444"
                prog_bar(sec["sector"], f"{sec['avg_change']:+.2f}%", min(abs(sec["avg_change"]) * 20 + 10, 100), color=c)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No sector data.")

    # ── 52-WEEK PULSE ────────────────────────────────────────
    with col_lose:
        sec_hdr("52-Week Pulse", "amber")
        near_high = pulse_data.get("near_high", [])
        near_low = pulse_data.get("near_low", [])
        
        if near_high or near_low:
            with st.container(height=360, border=False):
                for p in near_high:
                    ticker_card(p["symbol"] + " 🎯 High", p["company"], p["price"], p["change_pct"])
                for p in near_low:
                    ticker_card(p["symbol"] + " 📉 Low", p["company"], p["price"], p["change_pct"])
        else:
            st.info("No 52-week pulse data.")

    st.markdown("---")

    # ── Market Chart ──────────────────────────────────────────
    if True:
        render_interactive_chart("^NSEI", height=500, key_prefix="dash")


# ═══════════════════════════════════════════════════════════
#  📊 STOCK ANALYSIS
# ═══════════════════════════════════════════════════════════
elif page == "📊 Stock Analysis":
    page_header("Deep Dive", "Stock Analysis", "Technical · Fundamental · AI Signal · PDF Export")

    # ── Search bar row ───────────────────────────────────────
    col_sym, col_btn = st.columns([4, 1])
    
    if st.session_state.get("selected_symbol") in ["BTC-USD", "RELIANCE.NS"]:
        st.session_state["selected_symbol"] = ""
        
    with col_sym:
        symbol_raw = st.text_input("Stock Symbol", value=st.session_state.get("selected_symbol", ""), placeholder="e.g. RELIANCE.NS  /  TCS.NS  /  HDFCBANK.NS")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

    is_valid, norm_sym = validate_symbol(symbol_raw)
    
    if not symbol_raw:
        st.info("💡 Type an Indian stock symbol above (e.g. RELIANCE.NS or INFY.NS) to begin analysis.")
    elif not is_valid:
        st.warning(f"⚠️ {norm_sym}")

    elif analyze_btn or st.session_state.get("auto_analyze") == norm_sym:
        st.session_state["auto_analyze"]    = norm_sym
        st.session_state["selected_symbol"] = norm_sym

        if True:
            try:    price_data = get_stock_price(norm_sym)
            except: price_data = {"error": "Could not fetch price data."}

        if "error" in price_data:
            st.error(f"❌ {price_data['error']}")
        else:
            cname   = price_data.get("company_name", norm_sym)
            price   = price_data["current_price"]
            change  = price_data["change"]
            chg_pct = price_data["change_pct"]

            # Company name + live badge
            chg_color = "#10B981" if chg_pct >= 0 else "#EF4444"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin:0.5rem 0 1.1rem;">
              <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:var(--text);letter-spacing:-0.4px;">{cname}</div>
              <span class="badge badge-live">● LIVE</span>
              <span class="badge badge-blue">{norm_sym}</span>
            </div>""", unsafe_allow_html=True)

            # 5 metrics
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("💰 Current Price", f"₹{price:,.2f}",  f"{chg_pct:+.2f}% ({change:+.2f})")
            m2.metric("📉 Prev Close",    f"₹{price_data['previous_close']:,.2f}")
            m3.metric("📈 52W High",      f"₹{price_data.get('52_week_high','N/A')}")
            m4.metric("📉 52W Low",       f"₹{price_data.get('52_week_low','N/A')}")
            m5.metric("P/E Ratio",        str(price_data.get("pe_ratio","N/A")))

            st.markdown("---")

            # ── Main layout: Chart (left-wide) | Signal (right-narrow) ──
            col_chart, col_sig = st.columns([3.2, 1])

            with col_sig:
                # AI Signal
                sec_hdr("AI Signal", "purple")
                if True:
                    try:    sig = get_trading_signal(norm_sym)
                    except: sig = {"error": "Unavailable"}

                if "error" not in sig:
                    sc   = sig["signal_color"]
                    conf = sig["confidence"]
                    sig_label = sig["signal"]
                    sig_emoji = sig["signal_emoji"]

                    # Color map for backgrounds
                    bg_map = {
                        "BUY":  ("rgba(5,46,22,0.95)",  "rgba(16,185,129,0.25)", "rgba(16,185,129,0.08)"),
                        "SELL": ("rgba(69,10,10,0.95)",  "rgba(239,68,68,0.25)",  "rgba(239,68,68,0.08)"),
                        "HOLD": ("rgba(69,49,0,0.95)",   "rgba(245,158,11,0.25)", "rgba(245,158,11,0.08)"),
                    }
                    bg_dark, glow_mid, glow_outer = bg_map.get(sig_label, bg_map["HOLD"])

                    # SVG arc for confidence ring
                    r, cx, cy = 38, 50, 50
                    circ = 2 * 3.14159 * r
                    dash_fill = circ * conf / 100
                    dash_gap  = circ - dash_fill

                    st.markdown(f"""
                    <style>
                    @keyframes sig-pulse {{
                      0%,100% {{ box-shadow: 0 0 0 0 {sc}40, 0 0 40px {sc}20; }}
                      50%      {{ box-shadow: 0 0 0 8px transparent, 0 0 60px {sc}35; }}
                    }}
                    @keyframes arc-draw {{
                      from {{ stroke-dashoffset: {circ:.1f}; }}
                      to   {{ stroke-dashoffset: {circ - dash_fill:.1f}; }}
                    }}
                    </style>

                    <!-- SIGNAL MAIN CARD -->
                    <div style="
                      background: linear-gradient(160deg, {bg_dark} 0%, #080C16 100%);
                      border: 1px solid {sc}55;
                      border-radius: 20px;
                      padding: 1.4rem 1rem 1rem;
                      text-align: center;
                      position: relative;
                      overflow: hidden;
                      animation: sig-pulse 3s ease-in-out infinite;
                    ">
                      <!-- top shimmer line -->
                      <div style="position:absolute;top:0;left:0;right:0;height:2px;
                                  background:linear-gradient(90deg,transparent,{sc}CC,transparent);"></div>

                      <!-- SVG Confidence Ring -->
                      <div style="position:relative;display:inline-block;margin-bottom:0.5rem;">
                        <svg width="100" height="100" viewBox="0 0 100 100" style="transform:rotate(-90deg);">
                          <!-- track -->
                          <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                                  stroke="rgba(255,255,255,0.08)" stroke-width="6"/>
                          <!-- fill arc -->
                          <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                                  stroke="{sc}" stroke-width="6"
                                  stroke-linecap="round"
                                  stroke-dasharray="{dash_fill:.1f} {dash_gap:.1f}"
                                  stroke-dashoffset="0"
                                  style="filter:drop-shadow(0 0 4px {sc});
                                         animation: arc-draw 1.2s cubic-bezier(0.4,0,0.2,1) forwards;"/>
                        </svg>
                        <!-- center content -->
                        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);line-height:1;">
                          <div style="font-size:1.6rem;">{sig_emoji}</div>
                        </div>
                      </div>

                      <!-- Signal label -->
                      <div style="font-family:'Outfit',sans-serif;font-size:1.75rem;font-weight:900;
                                  color:{sc};letter-spacing:0.06em;line-height:1;margin-bottom:0.5rem;
                                  text-shadow:0 0 20px {sc}80;">{sig_label}</div>

                      <!-- Confidence row -->
                      <div style="display:inline-flex;align-items:center;gap:8px;
                                  background:rgba(0,0,0,0.3);border:1px solid {sc}30;
                                  border-radius:50px;padding:5px 14px;margin-bottom:0.3rem;">
                        <span style="font-size:0.65rem;color:rgba(255,255,255,0.4);
                                     text-transform:uppercase;letter-spacing:0.12em;">Confidence</span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:1rem;
                                     font-weight:700;color:{sc};">{conf}%</span>
                      </div>
                    </div>

                    <!-- REASONS CARD -->
                    <div style="
                      background: rgba(9,14,26,0.9);
                      border: 1px solid rgba(255,255,255,0.07);
                      border-radius: 14px;
                      padding: 0.9rem 1rem;
                      margin-top: 0.6rem;
                    ">
                      <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;
                                  color:rgba(255,255,255,0.25);text-transform:uppercase;
                                  letter-spacing:0.15em;margin-bottom:0.6rem;">Signal Factors</div>
                      {"".join([f'''
                      <div style="display:flex;align-items:flex-start;gap:8px;padding:0.45rem 0;
                                  border-bottom:1px solid rgba(255,255,255,0.05);">
                        <div style="width:6px;height:6px;border-radius:50%;margin-top:5px;flex-shrink:0;
                                    background:{"#10B981" if "positive" in r.lower() or "bullish" in r.lower() or "above" in r.lower()
                                               else "#EF4444" if "negative" in r.lower() or "bearish" in r.lower() or "below" in r.lower()
                                               else "#94A3C8"};
                                    box-shadow:0 0 6px {"#10B98180" if "positive" in r.lower() or "bullish" in r.lower() or "above" in r.lower()
                                                        else "#EF444480" if "negative" in r.lower() or "bearish" in r.lower() or "below" in r.lower()
                                                        else "#94A3C840"};"></div>
                        <div style="font-size:0.76rem;color:rgba(255,255,255,0.6);line-height:1.45;">{r}</div>
                      </div>''' for r in sig.get("reasons", [])])}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {sig.get('error','Unavailable')}")

            with col_chart:
                if True:
                    render_interactive_chart(norm_sym, height=600, key_prefix="analysis")

            # ── Fundamentals ─────────────────────────────────
            with st.expander("📋 Fundamental Metrics", expanded=True):
                if True:
                    try:    fd = get_fundamental_analysis(norm_sym)
                    except: fd = {"error": "Unavailable"}
                if "error" not in fd:
                    roe   = fd.get("roe","N/A")
                    roa   = fd.get("roa","N/A")
                    roe_s = f"{roe:.1%}" if isinstance(roe, float) else str(roe)
                    roa_s = f"{roa:.1%}" if isinstance(roa, float) else str(roa)
                    mktcap = fd.get("market_cap_cr","N/A")
                    mc_s   = f"₹{mktcap:,.0f} Cr" if isinstance(mktcap, (int,float)) else str(mktcap)

                    # Helper: color for numeric values
                    def val_color(v, good_above=None, bad_above=None):
                        if not isinstance(v, (int,float)): return "var(--text)"
                        if good_above and v > good_above:  return "#10B981"
                        if bad_above  and v > bad_above:   return "#EF4444"
                        return "var(--text)"

                    pe  = fd.get("pe_ratio","N/A")
                    pb  = fd.get("pb_ratio","N/A")
                    eps = fd.get("eps","N/A")
                    de  = fd.get("debt_to_equity","N/A")
                    dy  = fd.get("dividend_yield","N/A")

                    pe_c  = val_color(pe,  bad_above=35)
                    pb_c  = val_color(pb,  bad_above=5)
                    roe_c = "#10B981" if isinstance(roe, float) and roe > 0.15 else "var(--text)"
                    de_c  = "#EF4444" if isinstance(de,  (int,float)) and de > 1.5 else "#10B981" if isinstance(de,(int,float)) and de < 0.5 else "var(--text)"

                    st.markdown(f"""
                    <style>
                    .fm-section {{
                      background: var(--surface);
                      border: 1px solid var(--border);
                      border-radius: 16px;
                      padding: 1.1rem 1.2rem 1rem;
                      position: relative; overflow: hidden;
                    }}
                    .fm-section::before {{
                      content:''; position:absolute; top:0; left:0; right:0; height:2px;
                      border-radius:16px 16px 0 0;
                    }}
                    .fm-blue::before  {{ background: linear-gradient(90deg, #3B82F6, #06B6D4); }}
                    .fm-green::before {{ background: linear-gradient(90deg, #10B981, #84CC16); }}
                    .fm-amber::before {{ background: linear-gradient(90deg, #F59E0B, #F97316); }}

                    .fm-title {{
                      display: flex; align-items: center; gap: 7px;
                      margin-bottom: 0.85rem;
                    }}
                    .fm-title-icon {{
                      width: 28px; height: 28px; border-radius: 8px;
                      display: flex; align-items: center; justify-content: center;
                      font-size: 0.85rem;
                    }}
                    .fm-title-text {{
                      font-family: 'Outfit', sans-serif !important;
                      font-size: 0.82rem; font-weight: 700; letter-spacing: 0.02em;
                    }}

                    .fm-metric {{
                      display: flex; align-items: center;
                      justify-content: space-between;
                      padding: 0.5rem 0;
                      border-bottom: 1px solid rgba(255,255,255,0.04);
                    }}
                    .fm-metric:last-child {{ border-bottom: none; padding-bottom: 0; }}
                    .fm-metric-label {{
                      font-size: 0.76rem; color: var(--text3);
                      display: flex; align-items: center; gap: 6px;
                    }}
                    .fm-metric-val {{
                      font-family: 'JetBrains Mono', monospace !important;
                      font-size: 0.92rem; font-weight: 700;
                    }}
                    </style>

                    <div style="display:grid; grid-template-columns: repeat(3,1fr); gap: 0.85rem;">

                      <!-- VALUATION -->
                      <div class="fm-section fm-blue">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(59,130,246,0.15);">📊</div>
                          <div class="fm-title-text" style="color:#60A5FA;">Valuation</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#60A5FA;display:inline-block;"></span>
                            P/E Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{pe_c};">{pe}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#60A5FA;display:inline-block;"></span>
                            P/B Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{pb_c};">{pb}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#60A5FA;display:inline-block;"></span>
                            EPS
                          </span>
                          <span class="fm-metric-val">₹{eps}</span>
                        </div>
                      </div>

                      <!-- PROFITABILITY -->
                      <div class="fm-section fm-green">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(16,185,129,0.15);">💹</div>
                          <div class="fm-title-text" style="color:#34D399;">Profitability</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#34D399;display:inline-block;"></span>
                            ROE
                          </span>
                          <span class="fm-metric-val" style="color:{roe_c};">{roe_s}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#34D399;display:inline-block;"></span>
                            ROA
                          </span>
                          <span class="fm-metric-val">{roa_s}</span>
                        </div>
                        <div class="fm-metric" style="border-bottom:none;padding-bottom:0;">
                          <span class="fm-metric-label" style="font-size:0.68rem;color:var(--text4);font-style:italic;">
                            Return on equity &amp; assets
                          </span>
                        </div>
                      </div>

                      <!-- BALANCE SHEET -->
                      <div class="fm-section fm-amber">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(245,158,11,0.15);">🏦</div>
                          <div class="fm-title-text" style="color:#FBBF24;">Balance Sheet</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            D/E Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{de_c};">{de}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            Div Yield
                          </span>
                          <span class="fm-metric-val">{dy}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            Market Cap
                          </span>
                          <span class="fm-metric-val" style="font-size:0.78rem;">{mc_s}</span>
                        </div>
                      </div>

                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ Fundamental data unavailable.")

            # ── AI Deep Analysis ─────────────────────────────
            with st.expander("🤖 AI Deep Analysis", expanded=False):
                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    if True:
                        try:    result = agent.analyze_stock(norm_sym)
                        except Exception as e:
                            logger.error("AI analysis: %s", e)
                            result = {"error": "AI analysis error."}
                    if "error" not in result:
                        st.markdown(f'<div class="fin-card" style="border-left:3px solid var(--blue);line-height:1.75;font-size:0.88rem;color:var(--text2);">{result["ai_analysis"]}</div>', unsafe_allow_html=True)
                        try:
                            pdf_b = export_analysis_to_pdf(norm_sym, cname, price_data, result.get("fundamental_data",{}), result["ai_analysis"])
                            st.download_button("📥 Download PDF Report", data=pdf_b, file_name=f"{norm_sym}_analysis.pdf", mime="application/pdf")
                        except Exception as e:
                            logger.warning("PDF: %s", e)
                    else:
                        st.error(f"❌ {result['error']}")
                else:
                    st.info("⚙️ Configure LLM API key in .env to enable AI analysis.")

            st.markdown("---")
            if st.button(f"⭐ Add {norm_sym.replace('.NS','')} to Watchlist", type="secondary", use_container_width=True):
                res = add_to_watchlist(norm_sym, cname)
                st.success(res["message"]) if res["success"] else st.warning(res["message"])


# ═══════════════════════════════════════════════════════════
#  🔄 COMPARE STOCKS
# ═══════════════════════════════════════════════════════════
elif page == "🔄 Compare Stocks":
    page_header("Side by Side", "Compare Stocks", "Multi-stock technical & AI signal comparison")

    # Sector quick-pick
    sec_hdr("Quick Sector Pick", "blue")
    sc_cols = st.columns(len(settings.SECTORS))
    for i, (name, syms) in enumerate(settings.SECTORS.items()):
        if sc_cols[i].button(name, use_container_width=True):
            st.session_state["compare_symbols"] = ", ".join(syms[:3])
            st.rerun()

    default_cmp   = st.session_state.get("compare_symbols", "TCS.NS, INFY.NS, WIPRO.NS")
    symbols_input = st.text_input("Symbols (comma-separated, max 5)", value=default_cmp)
    compare_btn   = st.button("🔄 Compare Now", type="primary")

    if compare_btn:
        raw_syms   = [s.strip() for s in symbols_input.split(",") if s.strip()]
        valid_syms = []
        for s in raw_syms[:5]:
            ok, norm = validate_symbol(s)
            if ok: valid_syms.append(norm)

        if len(valid_syms) < 2:
            st.error("Please enter at least 2 valid symbols.")
        else:
            if True:
                try:
                    from tools.stock_tools import compare_stocks
                    df = compare_stocks(valid_syms)
                except Exception as e:
                    logger.error("compare_stocks: %s", e)
                    df = pd.DataFrame()

            if not df.empty:
                sec_hdr("Metrics Table", "blue")
                st.dataframe(df, use_container_width=True, hide_index=True)

                sec_hdr("AI Signals", "purple")
                sig_cols    = st.columns(len(valid_syms))
                all_signals = []
                for i, sym in enumerate(valid_syms):
                    with sig_cols[i]:
                        with st.spinner(f"{sym.replace('.NS','')}"):
                            try:    sig = get_trading_signal(sym)
                            except: sig = {"error": "N/A"}
                        all_signals.append(sig)
                        if "error" not in sig:
                            css = {"BUY":"signal-buy","SELL":"signal-sell","HOLD":"signal-hold"}.get(sig["signal"],"signal-hold")
                            sc  = sig["signal_color"]
                            st.markdown(f"""
                            <div class="{css}">
                              <div style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:800;color:var(--text);margin-bottom:5px;">{sym.replace('.NS','')}</div>
                              <div style="font-size:1.6rem;">{sig["signal_emoji"]}</div>
                              <div style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:{sc};">{sig["signal"]}</div>
                              <div style="background:rgba(255,255,255,0.1);border-radius:4px;height:5px;margin-top:8px;overflow:hidden;">
                                <div style="background:{sc};width:{sig['confidence']}%;height:100%;border-radius:4px;"></div>
                              </div>
                              <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:rgba(255,255,255,0.4);margin-top:5px;">{sig['confidence']}% conf.</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.caption(f"N/A — {sym.replace('.NS','')}")

                sec_hdr("6-Month Performance", "green")
                if True:
                    try:
                        st.plotly_chart(create_comparison_chart(valid_syms, df), use_container_width=True)
                    except Exception as e:
                        logger.error("Comparison chart: %s", e)
                        st.warning("⚠️ Chart unavailable.")

                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    with st.expander("🤖 AI Comparison Verdict", expanded=True):
                        if True:
                            try:
                                ai_sum = generate_comparison_summary(agent.llm, valid_syms, df.to_string(index=False), all_signals)
                            except Exception as e:
                                logger.error("AI compare: %s", e)
                                ai_sum = "⚠️ AI summary unavailable."
                        st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.75;font-size:0.88rem;color:var(--text2);">{ai_sum}</div>', unsafe_allow_html=True)
            else:
                st.error("❌ Could not fetch data. Check your symbols.")


# ═══════════════════════════════════════════════════════════
#  📰 NEWS & SENTIMENT
# ═══════════════════════════════════════════════════════════
elif page == "📰 News & Sentiment":
    page_header("Market Intelligence", "News & Sentiment", "Real-time articles with VADER sentiment scoring")

    col_sym, col_btn = st.columns([4, 1])
    
    if st.session_state.get("selected_symbol") in ["BTC-USD", "RELIANCE.NS"]:
        st.session_state["selected_symbol"] = ""
        
    symbol_news = col_sym.text_input("Stock Symbol", value=st.session_state.get("selected_symbol",""), placeholder="e.g. RELIANCE.NS")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_btn = st.button("📰 Fetch", type="primary", use_container_width=True)

    if fetch_btn:
        ok, norm = validate_symbol(symbol_news)
        if not ok:
            st.error(f"❌ {norm}"); st.stop()

        cname = norm
        try:
            p_info = get_stock_price(norm)
            cname  = p_info.get("company_name", norm) if "error" not in p_info else norm
        except: pass

        if True:
            try:    nr = get_news_with_sentiment(norm, cname)
            except Exception as e:
                logger.error("News: %s", e); st.error("⚠️ News unavailable."); nr = None

        if not nr: st.stop()

        # ── Layout: Gauge (left) | Stats + Summary (right) ──
        col_g, col_s = st.columns([1.5, 2.5])

        with col_g:
            sec_hdr(f"Sentiment — {cname.split()[0]}", "blue")
            st.plotly_chart(create_sentiment_gauge(nr["avg_score"]), use_container_width=True)
            sc_color = "#10B981" if nr["avg_score"] > 0.05 else ("#EF4444" if nr["avg_score"] < -0.05 else "#94A3C8")
            st.markdown(f"""
            <div class="fin-card" style="text-align:center;padding:0.9rem;">
              <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:{sc_color};">{nr["overall_sentiment"]}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:{sc_color};margin-top:2px;">{nr["avg_score"]:+.3f}</div>
              <div style="font-size:0.68rem;color:var(--text3);margin-top:4px;">Avg Compound Score</div>
            </div>""", unsafe_allow_html=True)

        with col_s:
            sec_hdr("Breakdown", "blue")
            sb1, sb2, sb3 = st.columns(3)
            sb1.metric("📈 Positive", nr["pos_count"])
            sb2.metric("➡️ Neutral",  nr["neu_count"])
            sb3.metric("📉 Negative", nr["neg_count"])
            st.markdown(f'<div class="fin-card" style="border-left:3px solid var(--cyan);padding:0.9rem 1.1rem;font-size:0.84rem;color:var(--text2);line-height:1.6;margin-top:0.5rem;">{nr["summary"]}</div>', unsafe_allow_html=True)

        st.markdown("---")
        sec_hdr("Recent Articles", "blue")

        import html
        for art in nr["articles"]:
            sentiment = art.get("sentiment", {})
            score     = sentiment.get("compound", 0)
            if score > 0.05:
                cls = "pos"; badge_cls = "badge-green"; emoji = "📈"
            elif score < -0.05:
                cls = "neg"; badge_cls = "badge-red";   emoji = "📉"
            else:
                cls = "neu"; badge_cls = "badge-blue";  emoji = "➡️"

            title  = html.escape(art.get("title","Untitled"))[:120]
            desc   = html.escape(art.get("description",""))[:160]
            source = html.escape(art.get("source",""))
            pub    = html.escape(art.get("published_at",""))
            url    = art.get("url","#")
            label  = sentiment.get("label","Neutral ➡️").split()[0]

            st.markdown(f"""
            <div class="news-item {cls}">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;">
                <a href="{url}" target="_blank"
                   style="font-weight:600;font-size:0.88rem;color:var(--text);text-decoration:none;flex:1;">{title}</a>
                <span class="badge {badge_cls}" style="flex-shrink:0;">{emoji} {label} ({score:+.2f})</span>
              </div>
              <div style="font-size:0.8rem;color:var(--text3);margin:0.4rem 0 0.6rem;line-height:1.45;">{desc}</div>
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:0.7rem;color:var(--text4);"><strong style="color:var(--text3);">{source}</strong> · {pub}</span>
                <a href="{url}" target="_blank" style="font-size:0.75rem;color:var(--blue2);font-weight:600;text-decoration:none;">Read article →</a>
              </div>
            </div>""", unsafe_allow_html=True)

        agent = get_agent()
        if agent and not st.session_state.agent_error:
            with st.expander("🤖 AI News Summary", expanded=False):
                from prompts import get_news_summary_prompt
                try:
                    articles_text = "\n".join([f"- {a.get('title','')} ({a.get('published_at','')})" for a in nr["articles"][:5]])
                    chain = get_news_summary_prompt() | agent.llm
                    if True:
                        resp = chain.invoke({"symbol": norm, "company_name": cname, "articles": articles_text,
                                            "sentiment_score": nr["avg_score"], "sentiment_label": nr["overall_sentiment"]})
                    st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.75;font-size:0.88rem;color:var(--text2);">{resp.content}</div>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error("AI news: %s", e)
                    st.warning("⚠️ AI summary unavailable.")


# ═══════════════════════════════════════════════════════════
#  💼 PORTFOLIO TRACKER
# ═══════════════════════════════════════════════════════════
elif page == "💼 Portfolio Tracker":
    page_header("Wealth Management", "Portfolio Tracker", "Live P&L · Risk Analysis · AI Insights")

    tab_view, tab_add = st.tabs(["📊 My Portfolio", "➕ Add Holding"])

    with tab_add:
        sec_hdr("Add New Holding", "green")
        fa1, fa2 = st.columns(2)
        p_sym  = fa1.text_input("Symbol",       placeholder="RELIANCE.NS")
        p_comp = fa2.text_input("Company Name", placeholder="Reliance Industries")
        fb1, fb2, fb3 = st.columns(3)
        p_qty  = fb1.number_input("Quantity",       min_value=1,    value=10)
        p_buy  = fb2.number_input("Buy Price (₹)",  min_value=0.01, value=1000.0, step=0.01)
        p_date = fb3.date_input("Buy Date")
        p_note = st.text_area("Notes (optional)", height=65)
        if st.button("➕ Add to Portfolio", type="primary"):
            if p_sym and p_buy > 0:
                ok, ns = validate_symbol(p_sym)
                if ok:
                    res = add_to_portfolio(ns, p_comp, float(p_buy), int(p_qty), str(p_date), p_note)
                    msg = str(res.get("message","Done"))
                    st.success(f"✅ {msg}") if res.get("success") else st.error(f"❌ {msg}")
                else:
                    st.error("❌ Invalid symbol")

    with tab_view:
        holdings = get_portfolio()
        if not holdings:
            st.info("📭 No holdings yet. Add in the ➕ tab.")
        else:
            if True:
                cur_px = {}
                for h in holdings:
                    try:
                        p = get_stock_price(h["symbol"])
                        cur_px[h["symbol"]] = p["current_price"] if "error" not in p else h["buy_price"]
                    except:
                        cur_px[h["symbol"]] = h["buy_price"]

            rows = []
            t_inv = t_cur = 0
            for h in holdings:
                sym = h["symbol"]
                inv = h["buy_price"] * h["quantity"]
                cur = cur_px[sym] * h["quantity"]
                pnl = cur - inv
                pct = (pnl/inv*100) if inv else 0
                t_inv += inv; t_cur += cur
                rows.append({"ID":h["id"],"Symbol":sym,"Company":h.get("company_name","")[:16],
                             "Qty":h["quantity"],"Buy ₹":f"{h['buy_price']:,.2f}","Now ₹":f"{cur_px[sym]:,.2f}",
                             "Invested ₹":f"{inv:,.0f}","Value ₹":f"{cur:,.0f}",
                             "P&L ₹":f"{pnl:+,.0f}","Return %":f"{pct:+.2f}%"})

            t_pnl = t_cur - t_inv
            t_pct = (t_pnl/t_inv*100) if t_inv else 0

            # Summary metrics
            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric("💰 Invested",      f"₹{t_inv:,.0f}")
            pm2.metric("📈 Current Value", f"₹{t_cur:,.0f}")
            pm3.metric("💵 Total P&L",     f"₹{t_pnl:+,.0f}", f"{t_pct:+.2f}%")
            pm4.metric("📋 Holdings",      len(holdings))

            st.markdown("---")

            # Risk | Allocation | Returns
            col_r, col_p, col_ret = st.columns([1.2, 1.5, 1.5])

            with col_r:
                sec_hdr("Risk Score", "amber")
                if True:
                    try:    risk = calculate_portfolio_risk(holdings, cur_px)
                    except: risk = {"error": "Unavailable"}
                if "error" not in risk:
                    st.plotly_chart(create_risk_meter(risk["risk_score"]), use_container_width=True)
                    rc = risk["risk_color"]
                    st.markdown(f"""
                    <div class="fin-card" style="text-align:center;padding:0.8rem;">
                      <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:800;color:{rc};">{risk["risk_label"]}</div>
                      <div style="font-size:0.75rem;color:var(--text3);margin-top:4px;line-height:1.5;">{risk["risk_description"]}</div>
                      <div style="font-size:0.68rem;color:var(--text4);margin-top:6px;">{risk.get("n_sectors",0)} sectors · {risk.get("n_holdings",0)} stocks · {risk.get("weighted_volatility",0):.1f}%/yr vol</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {risk.get('error','Unavailable')}")

            with col_p:
                sec_hdr("Allocation", "blue")
                try:
                    pie_df = pd.DataFrame({"Symbol":[r["Symbol"] for r in rows],
                                           "Value (₹)":[h["buy_price"]*h["quantity"] for h in holdings]})
                    st.plotly_chart(create_portfolio_pie(pie_df), use_container_width=True)
                except Exception as e:
                    logger.error("Pie: %s", e); st.info("Chart unavailable.")

            with col_ret:
                sec_hdr("Returns by Stock", "green")
                try:
                    st.plotly_chart(create_pnl_chart(rows), use_container_width=True)
                except Exception as e:
                    logger.error("PnL chart: %s", e); st.info("Chart unavailable.")

            st.markdown("---")
            sec_hdr("All Holdings", "blue")

            # Table header
            st.markdown('<div class="fin-card" style="padding:0;">', unsafe_allow_html=True)
            st.markdown('<div class="holding-hdr"><div>Stock</div><div>Qty</div><div>Buy ₹</div><div>Now ₹</div><div>P&amp;L ₹</div><div>Return</div><div></div></div>', unsafe_allow_html=True)
            for r in rows:
                pnl_color = "#10B981" if "+" in r["P&L ₹"] else "#EF4444"
                st.markdown(f"""
                <div class="holding-row">
                  <div>
                    <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:0.86rem;">{r["Symbol"].replace(".NS","")}</div>
                    <div style="font-size:0.67rem;color:var(--text3);">{r["Company"]}</div>
                  </div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">{r["Qty"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">₹{r["Buy ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">₹{r["Now ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;font-weight:700;color:{pnl_color};">{r["P&L ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;font-weight:700;color:{pnl_color};">{r["Return %"]}</div>
                  <div></div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            agent = get_agent()
            if agent and not st.session_state.agent_error:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖 AI Portfolio Analysis", type="primary"):
                    if True:
                        try:    result = agent.analyze_portfolio_with_ai(holdings, cur_px)
                        except Exception as e:
                            logger.error("AI portfolio: %s", e)
                            result = {"error": "Analysis error."}
                    if "error" not in result:
                        st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.75;font-size:0.88rem;color:var(--text2);">{result["ai_analysis"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {result.get('error','Unavailable')}")

            st.markdown("---")
            sec_hdr("Remove Holding", "red")
            dc1, dc2 = st.columns([4, 1])
            hopts = {f"{r['Symbol']} · ID:{r['ID']}": r["ID"] for r in rows}
            sel   = dc1.selectbox("Select holding", list(hopts.keys()))
            if dc2.button("Remove", type="secondary"):
                res = remove_from_portfolio(hopts[sel])
                if res["success"]: st.success(res["message"]); st.rerun()


# ═══════════════════════════════════════════════════════════
#  ⭐ WATCHLIST
# ═══════════════════════════════════════════════════════════
elif page == "⭐ Watchlist":
    page_header("Monitoring Centre", "Watchlist", "Live prices, AI signals and trend tracking")

    with st.expander("➕ Add Stock to Watchlist", expanded=False):
        wc1, wc2, wc3 = st.columns([1.8, 3, 1])
        w_sym  = wc1.text_input("Symbol",          placeholder="TATAPOWER.NS")
        w_note = wc2.text_input("Note (optional)",  placeholder="Waiting for pullback near support")
        with wc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add ➕", type="primary"):
                if w_sym:
                    ok, norm = validate_symbol(w_sym)
                    if ok:
                        try:
                            p     = get_stock_price(norm)
                            cname = p.get("company_name", norm) if "error" not in p else norm
                        except:
                            cname = norm
                        try:
                            res = add_to_watchlist(norm, cname, w_note)
                            if res["success"]: st.success(res["message"]); st.rerun()
                            else: st.error(res["message"])
                        except Exception as e:
                            st.error(f"❌ {e}")

    watchlist = get_watchlist()
    if not watchlist:
        st.info("📭 Watchlist empty. Add stocks above.")
    else:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
          <span class="badge badge-blue">WATCHING {len(watchlist)} STOCKS</span>
          <span class="badge badge-live">● LIVE</span>
        </div>""", unsafe_allow_html=True)

        if True:
            wl_data = {}
            for item in watchlist:
                s = item["symbol"]
                try:    wl_data[s] = {"price": get_stock_price(s), "signal": get_trading_signal(s)}
                except: wl_data[s] = {"price":{"error":"N/A"}, "signal":{"error":"N/A"}}

        # Table inside a card
        st.markdown('<div class="fin-card" style="padding:0;overflow:hidden;">', unsafe_allow_html=True)
        st.markdown('<div class="wl-hdr"><div>Stock</div><div>Price</div><div>Change</div><div>AI Signal</div><div>Trend</div><div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        for item in watchlist:
            sym        = item["symbol"]
            pd_        = wl_data[sym]["price"]
            sd_        = wl_data[sym]["signal"]
            cols       = st.columns([2, 1.5, 1, 1.8, 1.2, 0.6])

            cols[0].markdown(f"""<div style="padding:0.65rem 0;">
              <div style="font-family:'Outfit',sans-serif;font-weight:700;color:var(--text);font-size:0.86rem;">{sym.replace('.NS','')}</div>
              <div style="font-size:0.67rem;color:var(--text3);">{item.get('company_name','')[:18]}</div>
            </div>""", unsafe_allow_html=True)

            if "error" not in pd_:
                px  = pd_["current_price"]; ch = pd_["change_pct"]
                cc  = "#10B981" if ch >= 0 else "#EF4444"
                cols[1].markdown(f"<div style='padding:0.65rem 0;font-family:\"JetBrains Mono\",monospace;font-weight:600;color:var(--text);font-size:0.84rem;'>₹{px:,.2f}</div>", unsafe_allow_html=True)
                cols[2].markdown(f"<div style='padding:0.65rem 0;color:{cc};font-weight:700;font-size:0.82rem;'>{'▲' if ch>=0 else '▼'} {abs(ch):.2f}%</div>", unsafe_allow_html=True)
            else:
                cols[1].markdown("<div style='padding:0.65rem 0;color:var(--text4);'>N/A</div>", unsafe_allow_html=True)
                cols[2].markdown("<div style='padding:0.65rem 0;color:var(--text4);'>—</div>", unsafe_allow_html=True)

            if "error" not in sd_:
                sc  = sd_["signal_color"]
                cols[3].markdown(f"""<div style="padding:0.65rem 0;">
                  <span style="background:{sc}1A;border:1px solid {sc}55;border-radius:7px;padding:3px 9px;
                               font-family:'Outfit',sans-serif;font-weight:800;font-size:0.78rem;color:{sc};">
                    {sd_["signal_emoji"]} {sd_["signal"]}
                  </span>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:var(--text3);margin-top:3px;">{sd_['confidence']}% conf.</div>
                </div>""", unsafe_allow_html=True)
                is_bull   = sd_.get("sma20",0) > sd_.get("sma50",0)
                tc        = "#10B981" if is_bull else "#EF4444"
                tl        = "🔼 Bullish" if is_bull else "🔽 Bearish"
                cols[4].markdown(f"<div style='padding:0.65rem 0;color:{tc};font-weight:600;font-size:0.8rem;'>{tl}</div>", unsafe_allow_html=True)

            if cols[5].button("🗑️", key=f"rm_{sym}"):
                remove_from_watchlist(sym); st.rerun()

            st.markdown("<div style='height:1px;background:var(--border);margin:0 1rem;'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  📋 MARKET BRIEF
# ═══════════════════════════════════════════════════════════
elif page == "📋 Market Brief":
    page_header("Daily Digest", "AI Market Brief", "AI-generated market summary with movers & macro context")

    gen_btn = st.button("⚡ Generate Today's Brief", type="primary")

    st.markdown("---")

    if True:
        try:    nifty  = get_stock_price("^NSEI")
        except: nifty  = {"error":"Unavailable"}
        try:    sensex = get_stock_price("^BSESN")
        except: sensex = {"error":"Unavailable"}
        try:    mood   = get_market_mood()
        except: mood   = {"mood_label":"Neutral ➡️","mood_color":"#F59E0B","mood_score":50,"bullish_pct":40,"neutral_pct":35,"bearish_pct":25}
        try:    movers = get_top_movers()
        except: movers = {"gainers":[],"losers":[]}

    # Indices row
    col_n, col_s, col_m = st.columns(3)
    with col_n:
        sec_hdr("Nifty 50", "blue")
        if "error" not in nifty:
            cc = "#10B981" if nifty["change_pct"] >= 0 else "#EF4444"
            arrow = "▲" if nifty["change_pct"] >= 0 else "▼"
            cls   = "green-top" if nifty["change_pct"] >= 0 else "red-top"
            st.markdown(f"""
            <div class="idx-pill {cls}">
              <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--text);letter-spacing:-1px;">{nifty['current_price']:,.2f}</div>
              <div style="font-size:1rem;color:{cc};font-weight:700;margin-top:3px;">{arrow} {abs(nifty['change_pct']):.2f}%</div>
              <div style="font-size:0.65rem;color:var(--text3);margin-top:3px;">Prev: ₹{nifty.get('previous_close',0):,.2f}</div>
            </div>""", unsafe_allow_html=True)

    with col_s:
        sec_hdr("Sensex", "amber")
        if "error" not in sensex:
            cc = "#10B981" if sensex["change_pct"] >= 0 else "#EF4444"
            arrow = "▲" if sensex["change_pct"] >= 0 else "▼"
            cls   = "green-top" if sensex["change_pct"] >= 0 else "red-top"
            st.markdown(f"""
            <div class="idx-pill {cls}">
              <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--text);letter-spacing:-1px;">{sensex['current_price']:,.2f}</div>
              <div style="font-size:1rem;color:{cc};font-weight:700;margin-top:3px;">{arrow} {abs(sensex['change_pct']):.2f}%</div>
              <div style="font-size:0.65rem;color:var(--text3);margin-top:3px;">Prev: ₹{sensex.get('previous_close',0):,.2f}</div>
            </div>""", unsafe_allow_html=True)

    with col_m:
        sec_hdr("Market Mood", "blue")
        st.plotly_chart(create_market_mood_chart(mood["mood_score"]), use_container_width=True)

    st.markdown("---")

    # ── MARKET BREADTH METER ─────────────────────────────────
    try:
        breadth = get_market_breadth()
    except:
        breadth = {"advance": 0, "decline": 0, "unchanged": 0, "total": 1, "ad_ratio": 0.0, "avg_change": 0.0, "breadth_label": "Unknown", "breadth_color": "#888"}

    cb1, cb2 = st.columns([1.5, 1])
    with cb1:
        sec_hdr("Market Breadth Meter", "blue")
        st.markdown(f"""
        <div class="fin-card">
          <div style="font-size:0.85rem;color:var(--text2);margin-bottom:8px;font-weight:600;">{breadth['breadth_label']}</div>
          <div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin-bottom:12px;">
            <div style="width:{(breadth['advance']/breadth['total'])*100}%;background:#10B981;"></div>
            <div style="width:{(breadth['unchanged']/breadth['total'])*100}%;background:#F59E0B;"></div>
            <div style="width:{(breadth['decline']/breadth['total'])*100}%;background:#EF4444;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
            <span style="color:#10B981;">{breadth['advance']} Adv</span>
            <span style="color:#F59E0B;">{breadth['unchanged']} Unc</span>
            <span style="color:#EF4444;">{breadth['decline']} Dec</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with cb2:
        sec_hdr("A/D Ratio", "amber")
        st.markdown(f"""
        <div class="fin-card" style="text-align:center;padding:1.5rem 1rem;">
          <div style="font-family:'Outfit',sans-serif;font-size:2.2rem;font-weight:800;color:{breadth['breadth_color']};line-height:1;">{breadth['ad_ratio']}</div>
          <div style="font-size:0.7rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-top:6px;">Advance/Decline</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── SECTOR PERFORMANCE TILES ─────────────────────────────
    try:
        heatmap_data = get_sector_heatmap()
    except:
        heatmap_data = []

    sec_hdr("Sector Performance Tiles", "purple")
    if heatmap_data:
        tile_cols = st.columns(min(len(heatmap_data), 5))
        for i, sec in enumerate(heatmap_data[:5]):
            with tile_cols[i]:
                c = "#10B981" if sec["avg_change"] >= 0 else "#EF4444"
                arrow = "▲" if sec["avg_change"] >= 0 else "▼"
                st.markdown(f"""
                <div class="idx-pill" style="padding:0.7rem;text-align:center;">
                  <div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{sec['sector']}</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;color:{c};">{arrow} {abs(sec['avg_change']):.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No sector data available.")

    st.markdown("---")

    if gen_btn:
        agent = get_agent()
        if agent and not st.session_state.agent_error:
            if True:
                try:
                    mn   = get_news_with_sentiment("NIFTY","Indian stock market")
                    hdls = "\n".join([f"- {a['title']}" for a in mn.get("articles",[])[:6]]) or "No headlines"
                except:
                    hdls = "News unavailable"
                try:
                    brief = generate_market_brief(agent.llm,
                        nifty  if "error" not in nifty  else {},
                        sensex if "error" not in sensex else {},
                        heatmap_data, breadth,
                        hdls, mood["mood_label"])
                except Exception as e:
                    logger.error("Brief: %s", e)
                    brief = "⚠️ Brief generation failed."

            st.markdown("---")
            sec_hdr("AI Brief", "blue")
            st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.8;font-size:0.9rem;color:var(--text2);">{brief}</div>', unsafe_allow_html=True)
        else:
            st.error("⚠️ LLM API key not configured.")


# ═══════════════════════════════════════════════════════════
#  🧮 CALCULATORS
# ═══════════════════════════════════════════════════════════
elif page == "🧮 Calculators":
    page_header("Financial Tools", "Calculators", "SIP projection · Capital gains tax estimator")

    calc_type = st.radio("Type", ["💰 SIP Calculator", "🏛️ Capital Gains Tax"], horizontal=True)

    if calc_type == "💰 SIP Calculator":
        sec_hdr("SIP Return Calculator", "green")

        # Inputs in a card
        st.markdown('<div class="fin-card">', unsafe_allow_html=True)
        ci1, ci2, ci3 = st.columns(3)
        monthly_sip   = ci1.number_input("Monthly SIP (₹)", min_value=100, value=5000, step=500)
        annual_return = ci2.slider("Expected Return (%)", 4.0, 25.0, 12.0, 0.5)
        years         = ci3.slider("Duration (Years)",    1,   30,   10)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("📊 Calculate Returns", type="primary"):
            result = calculate_sip(monthly_sip, annual_return, years)
            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.metric("💰 Monthly SIP",   f"₹{monthly_sip:,.0f}")
            sr2.metric("📊 Total Invested", f"₹{result['total_invested']:,.0f}")
            sr3.metric("📈 Future Value",   f"₹{result['estimated_returns']:,.0f}")
            sr4.metric("🤑 Wealth Gained",  f"₹{result['wealth_gained']:,.0f}", f"+{result['absolute_return_pct']:.1f}%")

            st.plotly_chart(create_sip_chart(result["yearly_breakdown"]), use_container_width=True)

            with st.expander("📋 Year-by-Year Breakdown"):
                bdf = pd.DataFrame(result["yearly_breakdown"])
                bdf.columns = ["Year","Invested (₹)","Value (₹)"]
                bdf["Gain (₹)"] = bdf["Value (₹)"] - bdf["Invested (₹)"]
                bdf["Return %"] = (bdf["Gain (₹)"] / bdf["Invested (₹)"] * 100).round(2)
                st.dataframe(bdf, use_container_width=True, hide_index=True)

    else:
        sec_hdr("Capital Gains Tax Calculator", "amber")
        st.markdown('<div class="fin-card fin-card-glow-amber" style="margin-bottom:1rem;">', unsafe_allow_html=True)
        st.caption("LTCG (12.5%) applies after 1 year · STCG (20%) for ≤1 year — as per Indian tax law")
        tc1, tc2, tc3, tc4 = st.columns(4)
        buy_pt       = tc1.number_input("Buy Price (₹)",  min_value=1.0, value=500.0)
        sell_pt      = tc2.number_input("Sell Price (₹)", min_value=1.0, value=700.0)
        qty_t        = tc3.number_input("Quantity",       min_value=1,   value=100)
        holding_days = tc4.number_input("Holding Days",   min_value=1,   value=400)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🧮 Calculate Tax", type="primary"):
            tax = calculate_tax_implications(buy_pt, sell_pt, qty_t, holding_days)
            tr1, tr2, tr3 = st.columns(3)
            tr1.metric("💰 Investment", f"₹{tax['total_investment']:,.2f}")
            tr2.metric("📈 Proceeds",   f"₹{tax['total_proceeds']:,.2f}")
            tr3.metric("💵 Gross Gain", f"₹{tax['gross_gain_loss']:+,.2f}", f"{tax['return_pct']:+.2f}%")

            is_lt  = "LTCG" in tax["tax_type"]
            t_bdr  = "#F59E0B" if is_lt else "#EF4444"
            t_bg   = "rgba(245,158,11,0.06)" if is_lt else "rgba(239,68,68,0.06)"
            t_cls  = "fin-card-glow-amber" if is_lt else "fin-card-glow-red"

            st.markdown(f"""
            <div class="fin-card {t_cls}" style="margin-top:0.75rem;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.9rem;">
                <span style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:800;color:{t_bdr};">📋 {tax["tax_type"]}</span>
                <span class="badge {'badge-amber' if is_lt else 'badge-red'}">{holding_days} days · {tax["tax_rate_pct"]}% rate</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1.1rem;">
                <div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Tax Payable</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;color:#EF4444;">₹{tax["tax_payable"]:,.2f}</div>
                </div>
                <div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Net Gain After Tax</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;color:#10B981;">₹{tax["net_gain_after_tax"]:,.2f}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            st.caption("⚠️ Approximate. Consult a CA for accurate computation.")


# ═══════════════════════════════════════════════════════════
#  🤖 AI CHAT  ─  NEW PREMIUM DESIGN
# ═══════════════════════════════════════════════════════════
elif page == "🤖 AI Chat":

    # ── Page Header ───────────────────────────────────────
    page_header("Intelligent Assistant", "FinSaarthi AI", "Ask anything about Indian stocks, markets & investing")

    # ── Status Bar ────────────────────────────────────────
    agent_ok = not st.session_state.agent_error
    status_color = "#10B981" if agent_ok else "#EF4444"
    status_label = "AI Ready · Connected" if agent_ok else "LLM Not Configured"
    history_count = len(st.session_state.chat_history)

    st.markdown(f"""
    <div class="chat-status-bar">
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="chat-status-dot" style="background:{status_color};box-shadow:0 0 8px {status_color};"></div>
        <span style="font-size:0.75rem;font-weight:600;color:{'#34D399' if agent_ok else '#F87171'};">{status_label}</span>
        <span style="font-size:0.7rem;color:var(--text4);">·</span>
        <span style="font-size:0.7rem;color:var(--text3);">FinSaarthi AI v2.0</span>
      </div>
      <div style="display:flex;align-items:center;gap:16px;">
        <span style="font-size:0.72rem;color:var(--text4);">{history_count // 2} conversation{'s' if history_count // 2 != 1 else ''}</span>
        <div style="display:flex;align-items:center;gap:5px;">
          <div style="width:5px;height:5px;border-radius:50%;background:#3B82F6;"></div>
          <span style="font-size:0.7rem;color:var(--text4);">Powered by LangChain</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.agent_error:
        st.error(f"⚠️ LLM Not Configured: {st.session_state.agent_error}")

    # ── Chat History Display ──────────────────────────────
    import datetime as _dt

    if st.session_state.chat_history:
        chat_html = '<div class="chat-scroll-area">'
        for idx, msg in enumerate(st.session_state.chat_history):
            is_user = msg["role"] == "user"
            bubble_cls = "user-bubble" if is_user else "ai-bubble"
            wrap_cls   = "user-wrap"   if is_user else ""
            avatar_cls = "user-avatar" if is_user else "ai-avatar"
            avatar_icon = "U" if is_user else "📈"
            content = str(msg["content"]).replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            chat_html += f"""
            <div class="chat-msg-wrap {wrap_cls}">
              <div class="chat-avatar {avatar_cls}">{avatar_icon}</div>
              <div>
                <div class="chat-bubble {bubble_cls}">{content}</div>
                <div class="chat-meta">{'You' if is_user else 'FinSaarthi AI'} · just now</div>
              </div>
            </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # ── Input Row ─────────────────────────────────────────
    prefill = st.session_state.pop("prefill_q", "")

    st.markdown('<div class="chat-input-row">', unsafe_allow_html=True)
    inp_col, btn_col = st.columns([9, 1])
    with inp_col:
        typed = st.text_input(
            label="chat_input_hidden",
            label_visibility="collapsed",
            placeholder="Ask about stocks, markets, SIP, tax, investing…",
            key="chat_input_box",
            value=prefill if prefill else st.session_state.get("_chat_draft", ""),
        )
    with btn_col:
        send_clicked = st.button("➤", key="chat_send_btn", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = typed if send_clicked else None

    if (user_input and send_clicked) or prefill:
        q = (user_input or prefill).strip()
        # Clear input box after send
        st.session_state["_chat_draft"] = ""
        st.session_state.chat_history.append({"role": "user", "content": q})
        agent = get_agent()
        if agent:
            if True:
                st.markdown("""
                <div style="display:flex;align-items:center;gap:8px;padding:0.5rem 0 0.8rem;">
                  <div style="font-size:0.78rem;color:var(--text3);">FinSaarthi AI is thinking</div>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                </div>
                """, unsafe_allow_html=True)
                try:
                    resp = agent.chat(q)
                except Exception as e:
                    logger.error("Chat: %s", e)
                    resp = "⚠️ Error processing your question. Please try again."
        else:
            resp = "⚠️ LLM not configured. Please add your API key in `.env` to enable AI responses."
        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        st.rerun()

    # ── Action Row ────────────────────────────────────────
    if st.session_state.chat_history:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        col_clr, col_exp, col_info = st.columns([1, 2, 3])
        with col_clr:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                if st.session_state.agent:
                    st.session_state.agent.clear_memory()
                st.rerun()
        with col_exp:
            export_lines = []
            for m in st.session_state.chat_history:
                role = "You" if m["role"] == "user" else "FinSaarthi AI"
                export_lines.append(f"[{role}]\n{m['content']}\n")
            chat_txt = "\n".join(export_lines)
            st.download_button(
                "⬇️ Export Conversation",
                data=chat_txt,
                file_name="finsaarthi_chat.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_info:
            msg_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            st.markdown(
                f"<div style='font-size:0.72rem;color:var(--text4);padding-top:0.55rem;'>"
                f"💬 {msg_count} question{'s' if msg_count != 1 else ''} asked · "
                f"Responses are AI-generated, not SEBI-registered advice.</div>",
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center;padding:1.1rem 0 0.4rem;margin-top:1.5rem;
            border-top:1px solid #1C2D4F;">
  <span style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#2E3F62;">
    📈 &nbsp;<strong style="color:#4B6494;">FinSaarthi v2.0</strong>&nbsp;
    ·&nbsp; LangChain &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; yfinance &nbsp;·&nbsp; Plotly
    &nbsp;·&nbsp;
    <span style="color:#7F1D1D;">⚠️ Educational only · Not SEBI-registered financial advice</span>
  </span>
</div>
""", unsafe_allow_html=True)
