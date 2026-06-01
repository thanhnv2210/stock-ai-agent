"""
database.py

Async PostgreSQL connection config and schema initialisation for the stock AI agent.
Schema: stock_ai (inside tradingdb)
"""

import asyncpg

# Connection URL (asyncpg native DSN — no dialect prefix)
DB_DSN = "postgresql://admin:admin@localhost:54320/tradingdb"
SCHEMA = "stock_ai"

_CREATE_SCHEMA = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"

_CREATE_OHLCV_FACTORS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.ohlcv_factors (
    symbol       VARCHAR(20)      NOT NULL,
    date         DATE             NOT NULL,
    open         DOUBLE PRECISION,
    high         DOUBLE PRECISION,
    low          DOUBLE PRECISION,
    close        DOUBLE PRECISION,
    volume       BIGINT,
    dividends    DOUBLE PRECISION,
    stock_splits DOUBLE PRECISION,
    sma_5        DOUBLE PRECISION,
    sma_20       DOUBLE PRECISION,
    rsi_14       DOUBLE PRECISION,
    macd         DOUBLE PRECISION,
    macd_signal  DOUBLE PRECISION,
    macd_hist    DOUBLE PRECISION,
    PRIMARY KEY (symbol, date)
)
"""

_CREATE_SIGNALS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.signals (
    symbol   VARCHAR(20) NOT NULL,
    date     DATE        NOT NULL,
    close    DOUBLE PRECISION,
    signal   SMALLINT,
    position SMALLINT,
    PRIMARY KEY (symbol, date)
)
"""


async def init_schema() -> None:
    """Create the stock_ai schema and tables if they don't exist."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.execute(_CREATE_SCHEMA)
        await conn.execute(_CREATE_OHLCV_FACTORS)
        await conn.execute(_CREATE_SIGNALS)
    finally:
        await conn.close()
