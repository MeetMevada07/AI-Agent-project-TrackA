# ============================================================
# ui/charts.py  (UPGRADED v2)
# Plotly chart builders — all new + existing charts
# ============================================================

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from tools.stock_tools import calculate_technical_indicators

COLORS = {
    "primary": "#2563EB",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "bg_dark": "#0A0E1A",
    "bg_card": "#0F1629",
    "bg_card2": "#1A2035",
    "border": "#2A3650",
    "text_muted": "#6B7280",
    "neon_blue": "#3B82F6",
    "neon_green": "#10B981",
    "purple": "#8B5CF6",
}

CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0E1A",
    plot_bgcolor="#0F1629",
    font=dict(family="Inter, sans-serif", color="#E5E7EB"),
    
)


def create_candlestick_chart(df, symbol, show_sma=True, show_bb=False):
    if df.empty:
        return _empty_chart("No price data available")
    df = calculate_technical_indicators(df.copy())
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        subplot_titles=[f"Price — {symbol}", "Volume", "RSI (14)"],
        vertical_spacing=0.04,
    )
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="OHLC",
        increasing_line_color=COLORS["success"], decreasing_line_color=COLORS["danger"],
        increasing_fillcolor=COLORS["success"], decreasing_fillcolor=COLORS["danger"],
    ), row=1, col=1)
    if show_sma:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="SMA 20",
                                  line=dict(color="#F59E0B", width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50",
                                  line=dict(color="#8B5CF6", width=1.5)), row=1, col=1)
    if show_bb:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper",
                                  line=dict(color="#3B82F6", width=1, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower",
                                  line=dict(color="#3B82F6", width=1, dash="dash"),
                                  fill="tonexty", fillcolor="rgba(59,130,246,0.06)"), row=1, col=1)
    vol_colors = [COLORS["success"] if c >= o else COLORS["danger"]
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                          marker_color=vol_colors, opacity=0.75), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                              line=dict(color="#F97316", width=2)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["danger"], row=3, col=1,
                  annotation_text="Overbought", annotation_position="right")
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["success"], row=3, col=1,
                  annotation_text="Oversold", annotation_position="right")
    fig.update_layout(**CHART_THEME, height=720,
                       title=dict(text=f"📊 {symbol} — Technical Analysis",
                                  font=dict(size=18, color="#F9FAFB"), x=0.02),
                       xaxis_rangeslider_visible=False, showlegend=True,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                   xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
                       yaxis3=dict(range=[0, 100]))
    return fig


def create_macd_chart(df, symbol):
    if df.empty:
        return _empty_chart("No data available")
    df = calculate_technical_indicators(df.copy())
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                              line=dict(color=COLORS["neon_blue"], width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal",
                              line=dict(color="#F97316", width=2)))
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram",
                          marker_color=[COLORS["success"] if v >= 0 else COLORS["danger"]
                                        for v in df["MACD_Hist"].fillna(0)]))
    fig.update_layout(**CHART_THEME, title=f"📈 {symbol} — MACD", height=320)
    return fig


def create_comparison_chart(symbols, df_compare=None):
    fig = go.Figure()
    palette = ["#3B82F6","#22C55E","#F97316","#8B5CF6","#F59E0B"]
    for i, symbol in enumerate(symbols):
        try:
            from tools.stock_tools import get_historical_data
            hist = get_historical_data(symbol, period="6mo")
            if hist.empty: continue
            normalized = (hist["Close"] / hist["Close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(x=hist.index, y=normalized,
                                      name=symbol.replace(".NS",""),
                                      line=dict(color=palette[i%len(palette)], width=2.5)))
        except Exception:
            continue
    fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(**CHART_THEME,
                       title=dict(text="📊 Normalized Performance (Base=100)", font=dict(size=16), x=0.02),
                       yaxis_title="Return Index (Base=100)", height=450, hovermode="x unified",
                       yaxis=dict(ticksuffix="%"))
    return fig


def create_sentiment_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": "News Sentiment Score", "font": {"size": 14, "color": "#9CA3AF"}},
        number={"font": {"size": 36, "color": "#F9FAFB"}, "valueformat": ".3f"},
        gauge={
            "axis": {"range": [-1, 1], "tickwidth": 1, "tickcolor": "#6B7280"},
            "bar": {"color": COLORS["neon_blue"], "thickness": 0.3},
            "bgcolor": COLORS["bg_card2"], "borderwidth": 1, "bordercolor": COLORS["border"],
            "steps": [
                {"range": [-1, -0.3], "color": "rgba(239,68,68,0.3)"},
                {"range": [-0.3, -0.05], "color": "rgba(239,68,68,0.15)"},
                {"range": [-0.05, 0.05], "color": "rgba(107,114,128,0.2)"},
                {"range": [0.05, 0.3], "color": "rgba(34,197,94,0.15)"},
                {"range": [0.3, 1], "color": "rgba(34,197,94,0.3)"},
            ],
        },
    ))
    fig.update_layout(**CHART_THEME, height=280, margin=dict(l=30, r=30, t=40, b=20))
    return fig


def create_market_mood_chart(score):
    if score >= 65:
        bar_color = COLORS["success"]
    elif score >= 45:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["danger"]
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 42, "color": bar_color, "family": "Outfit, sans-serif"}, "valueformat": ".0f"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748B", "nticks": 5},
            "bar": {"color": bar_color, "thickness": 0.3},
            "bgcolor": "rgba(15, 23, 41, 0.4)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 45], "color": "rgba(239, 68, 68, 0.15)"},
                {"range": [45, 65], "color": "rgba(245, 158, 11, 0.15)"},
                {"range": [65, 100], "color": "rgba(16, 185, 129, 0.15)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": score
            }
        }
    ))
    
    fig.add_annotation(x=0.0, y=0.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom", text="Extreme Fear", font=dict(color="#EF4444", size=12, family="Outfit"), showarrow=False)
    fig.add_annotation(x=1.0, y=0.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", text="Extreme Greed", font=dict(color="#10B981", size=12, family="Outfit"), showarrow=False)

    fig.update_layout(
        **CHART_THEME,
        height=220,
        margin=dict(l=10, r=10, t=20, b=10)
    )
    return fig


def create_risk_meter(risk_score):
    if risk_score <= 3:
        bar_color = COLORS["success"]
    elif risk_score <= 6:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["danger"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=risk_score,
        title={"text": "Portfolio Risk Score", "font": {"size": 14, "color": "#9CA3AF"}},
        number={"font": {"size": 40, "color": "#F9FAFB"}, "suffix": "/10"},
        gauge={
            "axis": {"range": [0, 10], "tickwidth": 1, "tickcolor": "#6B7280", "nticks": 6},
            "bar": {"color": bar_color, "thickness": 0.35},
            "bgcolor": COLORS["bg_card2"], "borderwidth": 1, "bordercolor": COLORS["border"],
            "steps": [
                {"range": [0, 3], "color": "rgba(34,197,94,0.2)"},
                {"range": [3, 6], "color": "rgba(245,158,11,0.2)"},
                {"range": [6, 8], "color": "rgba(239,68,68,0.2)"},
                {"range": [8, 10], "color": "rgba(220,38,38,0.35)"},
            ],
            "threshold": {"line": {"color": "white", "width": 3},
                          "thickness": 0.8, "value": risk_score},
        },
    ))
    fig.update_layout(**CHART_THEME, height=280, margin=dict(l=30, r=30, t=40, b=20))
    return fig


def create_signal_chart(signal_data):
    breakdown = signal_data.get("score_breakdown", {})
    if not breakdown:
        return _empty_chart("No signal data")
    labels = {"ma_crossover": "MA Crossover", "rsi": "RSI Signal",
               "macd": "MACD", "sentiment": "News Sentiment", "position": "52W Position"}
    items = sorted([(labels.get(k, k), v) for k, v in breakdown.items()], key=lambda x: x[1])
    names = [i[0] for i in items]
    values = [i[1] for i in items]
    colors_list = [COLORS["success"] if v > 0 else COLORS["danger"] if v < 0 else COLORS["text_muted"] for v in values]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h", marker_color=colors_list,
                            text=[f"+{v}" if v > 0 else str(v) for v in values],
                            textposition="outside", textfont=dict(color="#E5E7EB", size=12)))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(**CHART_THEME, title=dict(text="Signal Score Breakdown", font=dict(size=14)),
                       height=280, showlegend=False, margin=dict(l=120, r=60, t=50, b=30))
    return fig


def create_portfolio_pie(portfolio_df):
    if portfolio_df.empty:
        return _empty_chart("No portfolio data")
    palette = ["#3B82F6","#22C55E","#F97316","#8B5CF6","#F59E0B","#EC4899","#14B8A6","#84CC16"]
    fig = go.Figure(go.Pie(
        labels=portfolio_df["Symbol"], values=portfolio_df["Value (₹)"],
        hole=0.5, textinfo="label+percent", textfont=dict(size=13),
        marker=dict(colors=palette[:len(portfolio_df)],
                    line=dict(color="#0A0E1A", width=2)),
    ))
    fig.update_layout(**CHART_THEME, title=dict(text="Portfolio Allocation", font=dict(size=16), x=0.02),
                       height=380, annotations=[dict(text="Portfolio", x=0.5, y=0.5,
                                                     font_size=14, showarrow=False,
                                                     font_color="#9CA3AF")])
    return fig


def create_sip_chart(yearly_data):
    years = [d["year"] for d in yearly_data]
    invested = [d["invested"] for d in yearly_data]
    value = [d["value"] for d in yearly_data]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=invested, name="Total Invested ₹",
                          marker_color="rgba(59,130,246,0.5)",
                          marker_line_color=COLORS["primary"], marker_line_width=1.5))
    fig.add_trace(go.Scatter(x=years, y=value, name="Estimated Value ₹",
                              line=dict(color=COLORS["success"], width=3),
                              mode="lines+markers",
                              fill="tozeroy", fillcolor="rgba(34,197,94,0.07)"))
    fig.update_layout(**CHART_THEME,
                       title=dict(text="💰 SIP Growth Projection", font=dict(size=16), x=0.02),
                       xaxis_title="Year", yaxis_title="Amount (₹)", height=420,
                       yaxis=dict(tickprefix="₹"))
    return fig


def create_pnl_chart(rows):
    if not rows: return _empty_chart("No holdings data")
    symbols = [r["Symbol"] for r in rows]
    pnl_pcts = [float(str(r["Return %"]).replace("%","").replace("+","")) for r in rows]
    colors_list = [COLORS["success"] if p >= 0 else COLORS["danger"] for p in pnl_pcts]
    fig = go.Figure(go.Bar(x=pnl_pcts, y=symbols, orientation="h", marker_color=colors_list,
                            text=[f"{p:+.1f}%" for p in pnl_pcts],
                            textposition="outside", textfont=dict(color="#E5E7EB", size=12)))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(**CHART_THEME, title=dict(text="Holdings Return %", font=dict(size=14), x=0.02),
                       height=max(200, len(rows)*45), showlegend=False,
                       xaxis=dict(ticksuffix="%"), margin=dict(l=100, r=80, t=50, b=30))
    return fig


def create_sector_chart(sector_data):
    if not sector_data: return _empty_chart("No sector data")
    sectors = list(sector_data.keys())
    changes = [sector_data[s] for s in sectors]
    colors_list = [COLORS["success"] if c >= 0 else COLORS["danger"] for c in changes]
    fig = go.Figure(go.Bar(x=sectors, y=changes, marker_color=colors_list,
                            text=[f"{c:+.1f}%" for c in changes], textposition="outside"))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)")
    fig.update_layout(**CHART_THEME, title=dict(text="Sector Performance Today", font=dict(size=14), x=0.02),
                       height=300, yaxis=dict(ticksuffix="%"), showlegend=False)
    return fig


def _empty_chart(message):
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=16, color=COLORS["text_muted"]))
    fig.update_layout(**CHART_THEME, height=280,
                       xaxis=dict(showgrid=False, showticklabels=False),
                       yaxis=dict(showgrid=False, showticklabels=False))
    return fig

def create_lightweight_chart(df, symbol):
    import json
    if df.empty:
        return ""
        
    df = df.copy()
    # Handle timezone and convert to seconds
    # Make sure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    # Clean data to prevent JS errors (NaNs, duplicates, unsorted)
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    if df.empty:
        return ""
        
    # Check if the entire dataframe is daily (all times are midnight)
    is_daily = True
    for t_idx in df.index:
        if t_idx.hour != 0 or t_idx.minute != 0:
            is_daily = False
            break
            
    candle_data = []
    volume_data = []
    
    for t_val, row in df.iterrows():
        if is_daily:
            # Lightweight Charts accepts YYYY-MM-DD for daily data
            t = t_val.strftime("%Y-%m-%d")
        else:
            # Unix timestamp for intraday
            t = int(t_val.timestamp())
            
        o, h, l, c = float(row['Open']), float(row['High']), float(row['Low']), float(row['Close'])
        candle_data.append({"time": t, "open": o, "high": h, "low": l, "close": c})
        
        vol = float(row.get('Volume', 0))
        if pd.isna(vol): vol = 0.0
        
        # Volume color (Green if Close >= Open, Red otherwise)
        color = 'rgba(8, 153, 129, 0.5)' if c >= o else 'rgba(242, 54, 69, 0.5)'
        volume_data.append({"time": t, "value": vol, "color": color})
        
    candle_json = json.dumps(candle_data)
    volume_json = json.dumps(volume_data)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #0F1729; overflow: hidden; font-family: 'Inter', sans-serif; }}
            #tvchart {{ width: 100vw; height: 100vh; position: relative; }}
            .chart-title {{
                position: absolute;
                top: 15px;
                left: 15px;
                z-index: 10;
                color: #d1d4dc;
                font-size: 18px;
                font-weight: 600;
                pointer-events: none;
            }}
        </style>
    </head>
    <body>
        <div id="tvchart">
            <div class="chart-title">{symbol}</div>
        </div>
        <script>
            const chartOptions = {{
                autoSize: true,
                width: window.innerWidth,
                height: window.innerHeight,
                layout: {{
                    textColor: '#d1d4dc',
                    background: {{ type: 'solid', color: '#0F1729' }},
                }},
                grid: {{
                    vertLines: {{ color: 'rgba(42, 54, 80, 0.5)' }},
                    horzLines: {{ color: 'rgba(42, 54, 80, 0.5)' }},
                }},
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                }},
                timeScale: {{
                    timeVisible: true,
                    secondsVisible: false,
                }},
            }};
            
            const chart = LightweightCharts.createChart(document.getElementById('tvchart'), chartOptions);
            
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#089981',
                downColor: '#f23645',
                borderVisible: false,
                wickUpColor: '#089981',
                wickDownColor: '#f23645',
            }});
            
            const candleData = {candle_json};
            candlestickSeries.setData(candleData);
            
            const volumeSeries = chart.addHistogramSeries({{
                color: '#26a69a',
                priceFormat: {{ type: 'volume' }},
                priceScaleId: '', // set as an overlay
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});
            
            const volumeData = {volume_json};
            volumeSeries.setData(volumeData);
            
            chart.timeScale().fitContent();
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                chart.applyOptions({{ width: window.innerWidth, height: window.innerHeight }});
            }});
        </script>
    </body>
    </html>
    """
    return html

def create_interactive_plotly_chart(df, symbol, indicators=None):
    if indicators is None:
        indicators = []
        
    if df.empty:
        return go.Figure()

    is_crypto = "-USD" in symbol
    currency_prefix = "$" if is_crypto else "₹"
        
    # Determine trend
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    is_up = last_close >= first_close
    
    line_color = '#10B981' if is_up else '#EF4444' # Emerald Green or Red
    fill_color = 'rgba(16, 185, 129, 0.15)' if is_up else 'rgba(239, 68, 68, 0.15)'
    
    # Needs subplots if MACD or RSI is selected
    has_oscillator = "MACD" in indicators or "RSI" in indicators
    
    if has_oscillator:
        from plotly.subplots import make_subplots
        rows = 1
        if "MACD" in indicators: rows += 1
        if "RSI" in indicators: rows += 1
        
        row_heights = [0.6] + [0.4 / (rows - 1)] * (rows - 1) if rows > 1 else [1]
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)
    else:
        fig = go.Figure()

    # Area trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Price',
        line=dict(color=line_color, width=2.5),
        fill='tozeroy',
        fillcolor=fill_color,
        hovertemplate='<b>%{x}</b><br>Price: %{y:,.2f}<extra></extra>'
    ), row=1 if has_oscillator else None, col=1 if has_oscillator else None)
    
    # Add Overlays to main chart
    if "SMA 20" in indicators and 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='#F59E0B', width=1.5)), row=1 if has_oscillator else None, col=1 if has_oscillator else None)
    if "SMA 50" in indicators and 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='#3B82F6', width=1.5)), row=1 if has_oscillator else None, col=1 if has_oscillator else None)
    if "EMA 20" in indicators and 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], mode='lines', name='EMA 20', line=dict(color='#D946EF', width=1.5, dash='dot')), row=1 if has_oscillator else None, col=1 if has_oscillator else None)
    if "Bollinger Bands" in indicators and 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='BB Upper', line=dict(color='rgba(148, 163, 184, 0.5)', width=1)), row=1 if has_oscillator else None, col=1 if has_oscillator else None)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='BB Lower', line=dict(color='rgba(148, 163, 184, 0.5)', width=1), fill='tonexty', fillcolor='rgba(148, 163, 184, 0.05)'), row=1 if has_oscillator else None, col=1 if has_oscillator else None)

    # Add Oscillators
    current_row = 2
    if "RSI" in indicators and 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='#A855F7', width=1.5)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.5)", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(16, 185, 129, 0.5)", row=current_row, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=current_row, col=1)
        current_row += 1
        
    if "MACD" in indicators and 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD', line=dict(color='#3B82F6', width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], mode='lines', name='Signal', line=dict(color='#F59E0B', width=1.5)), row=current_row, col=1)
        # MACD Histogram
        colors = ['#10B981' if val >= 0 else '#EF4444' for val in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Hist', marker_color=colors), row=current_row, col=1)
        fig.update_yaxes(title_text="MACD", row=current_row, col=1)
        current_row += 1

    # Dynamic y-axis zooming
    min_y = df['Low'].min() * 0.99
    max_y = df['High'].max() * 1.01
    
    fig.update_layout(
        height=600 if has_oscillator else 450,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit, sans-serif", color='#94A3B8'),
        hovermode="x unified",
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=13,
            font_family="JetBrains Mono, monospace",
            bordercolor=line_color
        )
    )
    
    fig.update_xaxes(showgrid=False, showline=False, zeroline=False, type="date", tickfont=dict(color="#64748B"), rangeslider_visible=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(51, 65, 85, 0.3)', griddash='dash', zeroline=False, tickfont=dict(color="#64748B"), side="right")
    
    # Update specifically the first y-axis (price)
    fig.update_yaxes(tickprefix=currency_prefix, range=[min_y, max_y], row=1 if has_oscillator else None, col=1 if has_oscillator else None)
    
    return fig
