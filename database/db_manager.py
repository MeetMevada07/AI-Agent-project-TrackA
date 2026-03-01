# ============================================================
# database/db_manager.py
# SQLite database manager for watchlists, portfolio, and history
# ============================================================

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from config.settings import settings


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    return conn


def initialize_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            company_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    # Portfolio table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            company_name TEXT,
            buy_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            buy_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Price alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            target_price REAL NOT NULL,
            alert_type TEXT NOT NULL,  -- 'above' or 'below'
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Analysis history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            analysis_type TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ── Watchlist Operations ──────────────────────────────────────

def add_to_watchlist(symbol: str, company_name: str = "", notes: str = "") -> dict:
    """Add a stock to the watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO watchlist (symbol, company_name, notes) VALUES (?, ?, ?)",
            (symbol.upper(), company_name, notes)
        )
        conn.commit()
        return {"success": True, "message": f"{symbol} added to watchlist"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def remove_from_watchlist(symbol: str) -> dict:
    """Remove a stock from the watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
        return {"success": True, "message": f"{symbol} removed from watchlist"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def get_watchlist() -> list:
    """Get all stocks in the watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ── Portfolio Operations ──────────────────────────────────────

def add_to_portfolio(symbol: str, company_name: str, buy_price: float,
                     quantity: int, buy_date: str, notes: str = "") -> dict:
    """Add a stock holding to the portfolio."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO portfolio (symbol, company_name, buy_price, quantity, buy_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (symbol.upper(), company_name, buy_price, quantity, buy_date, notes)
        )
        conn.commit()
        return {"success": True, "message": f"Added {quantity} shares of {symbol} at ₹{buy_price}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def get_portfolio() -> list:
    """Get all portfolio holdings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def remove_from_portfolio(holding_id: int) -> dict:
    """Remove a portfolio holding by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM portfolio WHERE id = ?", (holding_id,))
        conn.commit()
        return {"success": True, "message": "Holding removed"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


# ── Analysis History ──────────────────────────────────────────

def save_analysis(symbol: str, analysis_type: str, result: dict):
    """Save an analysis result to history."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO analysis_history (symbol, analysis_type, result_json) VALUES (?, ?, ?)",
            (symbol.upper(), analysis_type, json.dumps(result))
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
