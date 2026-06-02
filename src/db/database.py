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

_CREATE_WATCHLIST = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.watchlist (
    symbol     VARCHAR(20) NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    added_at   DATE        NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (symbol, group_name)
)
"""

_CREATE_SYMBOL_GROUPS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.symbol_groups (
    run_date   DATE        NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    symbol     VARCHAR(20) NOT NULL,
    PRIMARY KEY (run_date, group_name, symbol)
)
"""

_CREATE_SIGNAL_HISTORY = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.signal_history (
    id            SERIAL           PRIMARY KEY,
    run_date      DATE             NOT NULL,
    analysis_date DATE             NOT NULL,
    symbol        VARCHAR(20)      NOT NULL,
    group_name    VARCHAR(50)      NOT NULL,
    signal        VARCHAR(10)      NOT NULL,
    price         DOUBLE PRECISION NOT NULL,
    created_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW()
)
"""

_CREATE_SIGNAL_HISTORY_UNIQUE = f"""
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'signal_history_run_date_symbol_key'
    ) THEN
        ALTER TABLE {SCHEMA}.signal_history
            ADD CONSTRAINT signal_history_run_date_symbol_key UNIQUE (run_date, symbol);
    END IF;
END $$
"""

_CREATE_SIGNAL_HISTORY_IDX = f"""
CREATE INDEX IF NOT EXISTS signal_history_symbol_run_date_idx
    ON {SCHEMA}.signal_history (symbol, run_date)
"""

# ---------------------------------------------------------------------------
# job_configs — one row per job, defines scheduling and runtime behaviour
# ---------------------------------------------------------------------------

_CREATE_JOB_CONFIGS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.job_configs (
    job_name            VARCHAR(100)  PRIMARY KEY,
    display_name        VARCHAR(200)  NOT NULL,
    allow_multiple_runs BOOLEAN       NOT NULL DEFAULT false,
    schedule            VARCHAR(100),
    config              JSONB         NOT NULL DEFAULT '{{}}',
    enabled             BOOLEAN       NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
)
"""

# Seed the built-in daily pipeline job (idempotent)
_SEED_DAILY_PIPELINE = f"""
INSERT INTO {SCHEMA}.job_configs (job_name, display_name, allow_multiple_runs, schedule, config)
VALUES (
    'daily_pipeline',
    'Daily Signal Pipeline',
    false,
    '0 18 * * 1-5',
    '{{}}'
)
ON CONFLICT (job_name) DO NOTHING
"""

# ---------------------------------------------------------------------------
# job_runs — execution history, one row per run attempt
# ---------------------------------------------------------------------------

_CREATE_JOB_RUNS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.job_runs (
    id                SERIAL        PRIMARY KEY,
    job_name          VARCHAR(100)  NOT NULL REFERENCES {SCHEMA}.job_configs(job_name),
    run_date          DATE          NOT NULL,
    status            VARCHAR(20)   NOT NULL DEFAULT 'running',
    started_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    finished_at       TIMESTAMPTZ,
    symbols_processed INT,
    error_message     TEXT
)
"""

_CREATE_JOB_RUNS_IDX = f"""
CREATE INDEX IF NOT EXISTS job_runs_job_name_run_date_idx
    ON {SCHEMA}.job_runs (job_name, run_date)
"""

# Migrations for existing job_runs rows (pre job_configs schema)
_MIGRATE_JOB_RUNS = f"""
DO $$ BEGIN
    -- Drop legacy UNIQUE on run_date if it exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'job_runs_run_date_key'
    ) THEN
        ALTER TABLE {SCHEMA}.job_runs DROP CONSTRAINT job_runs_run_date_key;
    END IF;

    -- Add job_name column if missing (backfill existing rows as 'daily_pipeline')
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = '{SCHEMA}' AND table_name = 'job_runs' AND column_name = 'job_name'
    ) THEN
        ALTER TABLE {SCHEMA}.job_runs
            ADD COLUMN job_name VARCHAR(100) NOT NULL DEFAULT 'daily_pipeline'
            REFERENCES {SCHEMA}.job_configs(job_name);
    END IF;
END $$
"""


async def init_schema() -> None:
    """Create the stock_ai schema and all tables if they don't exist."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.execute(_CREATE_SCHEMA)
        await conn.execute(_CREATE_OHLCV_FACTORS)
        await conn.execute(_CREATE_SIGNALS)
        await conn.execute(_CREATE_WATCHLIST)
        await conn.execute(_CREATE_SYMBOL_GROUPS)
        await conn.execute(_CREATE_SIGNAL_HISTORY)
        await conn.execute(_CREATE_SIGNAL_HISTORY_UNIQUE)
        await conn.execute(_CREATE_SIGNAL_HISTORY_IDX)
        # job_configs must exist before job_runs (FK reference)
        await conn.execute(_CREATE_JOB_CONFIGS)
        await conn.execute(_SEED_DAILY_PIPELINE)
        await conn.execute(_CREATE_JOB_RUNS)
        await conn.execute(_MIGRATE_JOB_RUNS)
        await conn.execute(_CREATE_JOB_RUNS_IDX)
    finally:
        await conn.close()
