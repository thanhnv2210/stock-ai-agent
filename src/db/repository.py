"""
repository.py

Async read/write operations for the stock_ai schema.
All public functions are async; call them with asyncio.run() from sync code.
"""

import asyncpg
import pandas as pd
from datetime import date

from src.db.database import DB_DSN, SCHEMA


def _to_float(val):
    """Convert NaN / None to None (SQL NULL), otherwise float."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if f != f else f  # NaN check: NaN != NaN
    except (TypeError, ValueError):
        return None


def _to_int(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if f != f else int(f)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# ohlcv_factors
# ---------------------------------------------------------------------------

async def get_last_date(symbol: str) -> date | None:
    """Return the most recent date stored for a symbol, or None."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        row = await conn.fetchrow(
            f"SELECT MAX(date) FROM {SCHEMA}.ohlcv_factors WHERE symbol = $1",
            symbol,
        )
        return row[0]  # datetime.date or None
    finally:
        await conn.close()


async def get_factors(symbol: str) -> pd.DataFrame:
    """Return all OHLCV + factor rows for a symbol as a DataFrame."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        rows = await conn.fetch(
            f"SELECT * FROM {SCHEMA}.ohlcv_factors WHERE symbol = $1 ORDER BY date",
            symbol,
        )
    finally:
        await conn.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in rows])
    df.rename(columns={
        "date": "Date", "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume", "dividends": "Dividends",
        "stock_splits": "Stock Splits", "sma_5": "SMA_5", "sma_20": "SMA_20",
        "rsi_14": "RSI_14", "macd": "MACD", "macd_signal": "MACD_Signal",
        "macd_hist": "MACD_Hist",
    }, inplace=True)
    df.drop(columns=["symbol"], inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


async def upsert_factors(symbol: str, df: pd.DataFrame) -> None:
    """Upsert OHLCV + factor rows for a symbol."""
    needed = ["Date", "Open", "High", "Low", "Close", "Volume", "Dividends",
              "Stock Splits", "SMA_5", "SMA_20", "RSI_14", "MACD", "MACD_Signal", "MACD_Hist"]
    df = df[[c for c in needed if c in df.columns]].copy()

    records = []
    for _, row in df.iterrows():
        d = row["Date"]
        records.append((
            symbol,
            d.date() if hasattr(d, "date") else d,
            _to_float(row.get("Open")),
            _to_float(row.get("High")),
            _to_float(row.get("Low")),
            _to_float(row.get("Close")),
            _to_int(row.get("Volume")),
            _to_float(row.get("Dividends")),
            _to_float(row.get("Stock Splits")),
            _to_float(row.get("SMA_5")),
            _to_float(row.get("SMA_20")),
            _to_float(row.get("RSI_14")),
            _to_float(row.get("MACD")),
            _to_float(row.get("MACD_Signal")),
            _to_float(row.get("MACD_Hist")),
        ))

    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.executemany(
            f"""
            INSERT INTO {SCHEMA}.ohlcv_factors
                (symbol, date, open, high, low, close, volume, dividends, stock_splits,
                 sma_5, sma_20, rsi_14, macd, macd_signal, macd_hist)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            ON CONFLICT (symbol, date) DO UPDATE SET
                open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                close=EXCLUDED.close, volume=EXCLUDED.volume,
                dividends=EXCLUDED.dividends, stock_splits=EXCLUDED.stock_splits,
                sma_5=EXCLUDED.sma_5, sma_20=EXCLUDED.sma_20, rsi_14=EXCLUDED.rsi_14,
                macd=EXCLUDED.macd, macd_signal=EXCLUDED.macd_signal,
                macd_hist=EXCLUDED.macd_hist
            """,
            records,
        )
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# signals
# ---------------------------------------------------------------------------

async def upsert_signals(symbol: str, df: pd.DataFrame) -> None:
    """Upsert signal rows for a symbol."""
    records = []
    for _, row in df.iterrows():
        d = row["Date"]
        records.append((
            symbol,
            d.date() if hasattr(d, "date") else d,
            _to_float(row.get("Close")),
            _to_int(row.get("Signal")),
            _to_int(row.get("Position")),
        ))

    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.executemany(
            f"""
            INSERT INTO {SCHEMA}.signals (symbol, date, close, signal, position)
            VALUES ($1,$2,$3,$4,$5)
            ON CONFLICT (symbol, date) DO UPDATE SET
                close=EXCLUDED.close, signal=EXCLUDED.signal, position=EXCLUDED.position
            """,
            records,
        )
    finally:
        await conn.close()
