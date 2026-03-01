# ============================================================
# agents/financial_agent.py
# LangChain financial agent with memory and tool integration
# ============================================================

import json
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage, AIMessage

from llm import get_llm
from prompts import (
    get_chat_prompt, get_stock_analysis_prompt,
    get_comparison_prompt, get_portfolio_prompt, get_news_summary_prompt,
)
from tools.stock_tools import (
    get_stock_price, get_historical_data, calculate_technical_indicators,
    get_fundamental_analysis, compare_stocks,
)
from tools.news_tools import get_news_with_sentiment
from database.db_manager import save_analysis


class FinancialAgent:
    """
    Main AI financial agent.
    
    Capabilities:
    - Conversational Q&A about Indian stocks (with memory)
    - Full stock analysis combining price, fundamentals, technicals, news
    - Multi-stock comparison
    - Portfolio analysis
    - News summarization
    
    Architecture:
    - LLM: Gemini or OpenAI (configured via .env)
    - Memory: ConversationBufferWindowMemory (last 10 exchanges)
    - Prompts: Specialized templates per task
    """

    def __init__(self):
        self.llm = get_llm()
        # Window memory keeps last 10 conversation turns
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10,
        )

    def chat(self, user_message: str) -> str:
        """
        General conversational interface with memory.
        
        The agent remembers context across turns within a session,
        so users can ask follow-up questions naturally.
        
        Args:
            user_message: User's natural language query
        
        Returns:
            AI response string
        """
        try:
            prompt = get_chat_prompt()
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=self.memory,
                verbose=False,
            )
            response = chain.invoke({"input": user_message})
            return response["text"]
        except Exception as e:
            return f"❌ Error: {str(e)}\n\nPlease check your API key and internet connection."

    def analyze_stock(self, symbol: str) -> dict:
        """
        Full multi-dimensional stock analysis.
        
        Gathers data from all sources, runs AI interpretation,
        and returns structured results including AI commentary.
        
        Args:
            symbol: NSE stock symbol e.g. 'RELIANCE.NS'
        
        Returns:
            dict with price_data, fundamental_data, technical_summary,
                  news_data, ai_analysis, raw_df (for charting)
        """
        # Normalize symbol
        symbol = symbol.strip().upper()
        if not symbol.endswith((".NS", ".BO")):
            symbol += ".NS"  # Default to NSE

        # Gather all data
        price_data = get_stock_price(symbol)
        if "error" in price_data:
            return {"error": price_data["error"]}

        fundamental_data = get_fundamental_analysis(symbol)
        company_name = price_data.get("company_name", symbol)
        news_data = get_news_with_sentiment(symbol, company_name)

        # Technical indicators
        df = get_historical_data(symbol, period="6mo")
        technical_summary = {}
        if not df.empty:
            df_with_indicators = calculate_technical_indicators(df)
            last = df_with_indicators.iloc[-1]
            technical_summary = {
                "current_price": round(float(last["Close"]), 2),
                "sma_20": round(float(last.get("SMA_20", 0) or 0), 2),
                "sma_50": round(float(last.get("SMA_50", 0) or 0), 2),
                "ema_20": round(float(last.get("EMA_20", 0) or 0), 2),
                "rsi": round(float(last.get("RSI", 0) or 0), 2),
                "macd": round(float(last.get("MACD", 0) or 0), 2),
                "macd_signal": round(float(last.get("MACD_Signal", 0) or 0), 2),
                "bb_upper": round(float(last.get("BB_Upper", 0) or 0), 2),
                "bb_lower": round(float(last.get("BB_Lower", 0) or 0), 2),
                "trend": "Bullish" if last["Close"] > (last.get("SMA_50") or last["Close"]) else "Bearish",
                "rsi_signal": (
                    "Overbought (>70)" if (last.get("RSI") or 0) > 70
                    else "Oversold (<30)" if (last.get("RSI") or 0) < 30
                    else "Neutral (30-70)"
                ),
            }

        # Generate AI analysis
        ai_analysis = self._generate_stock_analysis(
            symbol, company_name, price_data, fundamental_data,
            technical_summary, news_data
        )

        # Save to history
        save_analysis(symbol, "full_analysis", {"price": price_data, "fundamentals": fundamental_data})

        return {
            "symbol": symbol,
            "company_name": company_name,
            "price_data": price_data,
            "fundamental_data": fundamental_data,
            "technical_summary": technical_summary,
            "news_data": news_data,
            "ai_analysis": ai_analysis,
            "raw_df": df,  # For Plotly charts
        }

    def _generate_stock_analysis(self, symbol, company_name, price_data,
                                  fundamental_data, technical_summary, news_data) -> str:
        """Internal: Call LLM to generate analysis narrative."""
        try:
            prompt = get_stock_analysis_prompt()
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)

            # Format news articles for the prompt
            articles_text = "\n".join([
                f"- [{a.get('published_at', '')}] {a.get('title', '')} "
                f"(Sentiment: {a.get('sentiment', {}).get('label', 'N/A')})"
                for a in news_data.get("articles", [])[:5]
            ])

            response = chain.invoke({
                "symbol": symbol,
                "company_name": company_name,
                "price_data": json.dumps(price_data, default=str, indent=2),
                "fundamental_data": json.dumps(fundamental_data, default=str, indent=2),
                "technical_data": json.dumps(technical_summary, default=str, indent=2),
                "news_sentiment": f"{news_data.get('summary', '')}\n\nRecent Headlines:\n{articles_text}",
            })
            return response["text"]
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"

    def compare_stocks_with_ai(self, symbols: list) -> dict:
        """
        Compare multiple stocks and generate AI commentary.
        
        Args:
            symbols: List of stock symbols e.g. ['TCS.NS', 'INFY.NS']
        
        Returns:
            dict with comparison_df and ai_commentary
        """
        try:
            df = compare_stocks(symbols)
            if df.empty:
                return {"error": "Could not fetch data for comparison"}

            # Infer sector from first stock
            sector = "Indian Equity"
            try:
                info = get_fundamental_analysis(symbols[0])
                sector = info.get("sector", "Indian Equity")
            except Exception:
                pass

            # AI commentary
            prompt = get_comparison_prompt()
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)
            response = chain.invoke({
                "comparison_data": df.to_string(index=False),
                "sector": sector,
            })

            return {
                "comparison_df": df,
                "ai_commentary": response["text"],
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_portfolio_with_ai(self, portfolio_data: list, current_prices: dict) -> dict:
        """
        Analyze user portfolio and provide AI insights.
        
        Args:
            portfolio_data: List of holdings from database
            current_prices: Dict of {symbol: current_price}
        
        Returns:
            dict with portfolio_df, metrics, and ai_analysis
        """
        try:
            import pandas as pd

            rows = []
            total_invested = 0
            total_current = 0

            for holding in portfolio_data:
                symbol = holding["symbol"]
                buy_price = holding["buy_price"]
                quantity = holding["quantity"]
                current_price = current_prices.get(symbol, buy_price)

                invested = buy_price * quantity
                current_val = current_price * quantity
                pnl = current_val - invested
                pnl_pct = (pnl / invested) * 100 if invested else 0

                total_invested += invested
                total_current += current_val

                rows.append({
                    "Symbol": symbol,
                    "Company": holding.get("company_name", symbol),
                    "Qty": quantity,
                    "Buy Price (₹)": round(buy_price, 2),
                    "Current (₹)": round(current_price, 2),
                    "Invested (₹)": round(invested, 2),
                    "Value (₹)": round(current_val, 2),
                    "P&L (₹)": round(pnl, 2),
                    "Return %": round(pnl_pct, 2),
                })

            df = pd.DataFrame(rows)
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

            # AI analysis
            prompt = get_portfolio_prompt()
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)
            response = chain.invoke({
                "portfolio_data": df.to_string(index=False),
                "total_invested": f"{total_invested:,.2f}",
                "current_value": f"{total_current:,.2f}",
                "pnl": f"{total_pnl:,.2f}",
                "pnl_pct": f"{total_pnl_pct:.2f}",
            })

            return {
                "portfolio_df": df,
                "total_invested": total_invested,
                "current_value": total_current,
                "pnl": total_pnl,
                "pnl_pct": total_pnl_pct,
                "ai_analysis": response["text"],
            }

        except Exception as e:
            return {"error": str(e)}

    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()
