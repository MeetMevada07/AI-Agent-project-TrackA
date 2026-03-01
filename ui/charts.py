# ============================================================
# ui/charts.py
# Plotly chart builders for financial visualizations
# ============================================================

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from tools.stock_tools import calculate_technical_indicators


def create_candlestick_chart(df: pd.DataFrame, symbol: str,
                              show_sma: bool = True,
                              show_bb: bool = False) -> go.Figure:
    """
    Interactive candlestick chart with optional technical overlays.
    
    Args:
        df: OHLCV DataFrame
        symbol: Stock symbol for chart title
        show_sma: Show SMA 20/50 lines
        show_bb: Show Bollinger Bands
    
    Returns:
        Plotly Figure
    """
    if df.empty:
        return _empty_chart("No data available")

    df = calculate_technical_indicators(df.copy())

    # Create subplots: price + volume + RSI
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=[f"{symbol} — Price", "Volume", "RSI (14)"],
        vertical_spacing=0.05,
    )

    # ── Candlestick ──────────────────────────────────────────
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # ── Moving Averages ──────────────────────────────────────
    if show_sma:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_20"], name="SMA 20",
                       line=dict(color="#ffb300", width=1.5)),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50",
                       line=dict(color="#7b1fa2", width=1.5)),
            row=1, col=1,
        )

    # ── Bollinger Bands ──────────────────────────────────────
    if show_bb:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper",
                       line=dict(color="#42a5f5", width=1, dash="dash")),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower",
                       line=dict(color="#42a5f5", width=1, dash="dash"),
                       fill="tonexty", fillcolor="rgba(66, 165, 245, 0.05)"),
            row=1, col=1,
        )

    # ── Volume ───────────────────────────────────────────────
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume",
               marker_color=colors, opacity=0.7),
        row=2, col=1,
    )

    # ── RSI ──────────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                   line=dict(color="#ff7043", width=2)),
        row=3, col=1,
    )
    # RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1,
                  annotation_text="Overbought", annotation_position="right")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1,
                  annotation_text="Oversold", annotation_position="right")
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1)

    # ── Layout ───────────────────────────────────────────────
    fig.update_layout(
        title=dict(text=f"📊 {symbol} — Technical Analysis", font_size=18),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=60, t=80, b=60),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
    )

    return fig


def create_macd_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """MACD indicator chart."""
    if df.empty:
        return _empty_chart("No data available")

    df = calculate_technical_indicators(df.copy())
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                             line=dict(color="#42a5f5", width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal",
                             line=dict(color="#ff7043", width=2)))
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram",
                         marker_color=["#26a69a" if v >= 0 else "#ef5350"
                                       for v in df["MACD_Hist"].fillna(0)]))

    fig.update_layout(
        title=f"📈 {symbol} — MACD",
        template="plotly_dark",
        height=350,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
    )
    return fig


def create_comparison_chart(symbols: list, df_compare: pd.DataFrame) -> go.Figure:
    """
    Normalized performance comparison chart (base = 100).
    Shows relative % returns since start date.
    """
    if df_compare.empty:
        return _empty_chart("No comparison data")

    fig = go.Figure()
    colors = ["#42a5f5", "#26a69a", "#ff7043", "#ab47bc", "#ffca28"]

    for i, symbol in enumerate(symbols):
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            if hist.empty:
                continue
            normalized = (hist["Close"] / hist["Close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=normalized,
                name=symbol.replace(".NS", ""),
                line=dict(color=colors[i % len(colors)], width=2),
            ))
        except Exception:
            continue

    fig.add_hline(y=100, line_dash="dash", line_color="white", opacity=0.3)
    fig.update_layout(
        title="📊 Normalized Performance Comparison (Base=100)",
        yaxis_title="Return Index (Base = 100)",
        template="plotly_dark",
        height=450,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
    )
    return fig


def create_sentiment_gauge(score: float) -> go.Figure:
    """
    Gauge chart showing news sentiment score (-1 to +1).
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": "News Sentiment Score", "font": {"size": 16}},
        gauge={
            "axis": {"range": [-1, 1], "tickwidth": 1},
            "bar": {"color": "#42a5f5"},
            "steps": [
                {"range": [-1, -0.05], "color": "#ef5350"},
                {"range": [-0.05, 0.05], "color": "#bdbdbd"},
                {"range": [0.05, 1], "color": "#26a69a"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 4},
                "thickness": 0.75,
                "value": score,
            },
        },
        number={"suffix": "", "font": {"size": 30}},
    ))
    fig.update_layout(
        height=300,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        margin=dict(l=30, r=30, t=50, b=30),
    )
    return fig


def create_portfolio_pie(portfolio_df: pd.DataFrame) -> go.Figure:
    """Pie chart of portfolio allocation by stock."""
    if portfolio_df.empty:
        return _empty_chart("No portfolio data")

    fig = go.Figure(go.Pie(
        labels=portfolio_df["Symbol"],
        values=portfolio_df["Value (₹)"],
        hole=0.4,
        textinfo="label+percent",
        marker=dict(colors=px.colors.qualitative.Set3),
    ))
    fig.update_layout(
        title="Portfolio Allocation",
        template="plotly_dark",
        height=400,
        paper_bgcolor="#0e1117",
    )
    return fig


def create_sip_chart(yearly_data: list) -> go.Figure:
    """Bar + line chart showing SIP growth over time."""
    years = [d["year"] for d in yearly_data]
    invested = [d["invested"] for d in yearly_data]
    value = [d["value"] for d in yearly_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=invested, name="Total Invested (₹)",
                         marker_color="#546e7a"))
    fig.add_trace(go.Scatter(x=years, y=value, name="Estimated Value (₹)",
                             line=dict(color="#26a69a", width=3),
                             mode="lines+markers"))

    fig.update_layout(
        title="SIP Growth Projection",
        xaxis_title="Year",
        yaxis_title="Amount (₹)",
        template="plotly_dark",
        height=400,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    """Return a blank chart with a message."""
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False, font_size=18)
    fig.update_layout(template="plotly_dark", height=300,
                      paper_bgcolor="#0e1117")
    return fig
