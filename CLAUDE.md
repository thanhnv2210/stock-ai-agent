# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Dependencies: `yfinance`, `pandas`, `matplotlib`

## Common Commands

All `src` modules must be run from the project root using `python -m` to resolve internal imports correctly:

```bash
# Fetch historical data for a single symbol (saves to data/<SYMBOL>_historical.csv)
python3 src/data/fetch_data.py --symbol AAPL --start 2020-01-01 --end 2025-01-01

# Batch fetch + compute factors for all symbols in tickers.json
python -m src.jobs.fetch_all_data

# Incremental fetch (only missing dates) for all symbols in tickers.json
python -m src.jobs.fetch_incremental_data

# Run momentum agent (generates signals from factors CSV)
python3 src/agents/momentum_agent.py

# Run backtester (multi-symbol portfolio backtest)
python3 -m src.backtester.backtester

# Run execution adapter (paper trade simulation)
python -m src.execution.execution_adapter

# Visualize signals and portfolio value
python3 -m src.visualization.visualizer

# Run the full daily pipeline (fetch + factors + signals + alerts)
python -m src.jobs.daily_pipeline
```

## Architecture

The pipeline flows in this order:

```
tickers.json
    -> src/jobs/fetch_all_data.py or fetch_incremental_data.py
        -> src/data/fetch_data.py          (yfinance OHLCV download)
        -> src/features/factor_calculator.py  (SMA, RSI, MACD)
        -> data/<SYMBOL>_factors.csv
    -> src/agents/momentum_agent.py        (Signal: 1=buy, -1=sell, 0=hold)
        -> data/<SYMBOL>_signals.csv
    -> src/risk/risk_manager.py            (position sizing, SL/TP)
    -> src/backtester/backtester.py        (multi-symbol portfolio backtest)
        -> data/portfolio_backtest.csv
    -> src/execution/execution_adapter.py  (paper trading simulation)
        -> data/<SYMBOL>_trades.csv, data/<SYMBOL>_portfolio.csv
    -> src/visualization/visualizer.py     (price/signal/portfolio charts)
```

**Key design points:**

- `tickers.json` is the single source of truth for which symbols are tracked.
- `FactorCalculator` uses a builder pattern (chainable `add_*` methods); call `add_all_factors()` for SMA + RSI + MACD together.
- `MomentumAgent` reads `SMA_5`, `SMA_20`, and `RSI_14` columns — these are produced by `factor_calculator_v1.py` (the v1 variant), not the default `factor_calculator.py` which produces `SMA_Short`/`SMA_Long`/`RSI`. Be aware of this column name mismatch between the two calculator versions.
- `Backtester` calls `RiskManager.apply_risk()` internally; it splits `initial_cash` equally across symbols.
- `ExecutionAdapter` is a separate paper-trading simulator that replays signals row-by-row with commission.
- `data/` directory is gitignored; CSV outputs from all pipeline stages land here.

## Phase 9: Automation & Alerts

**`src/notifications/notifier.py`** — `Notifier` class always prints to console; also sends to Slack and/or email when env vars are configured. Uses only stdlib (`smtplib`, `urllib`), no extra dependencies.

**`src/jobs/daily_pipeline.py`** — `DailyPipeline` orchestrates the full daily loop: incremental fetch → `add_factors()` (v1) → `MomentumAgent.generate_signals()` → `Notifier.send()`. Run directly with `python -m src.jobs.daily_pipeline`.

**Notification config** — copy `.env.template` to `.env` and fill in values. `.env` is gitignored. Supported channels:
- Slack: set `SLACK_WEBHOOK_URL`
- Email: set `EMAIL_FROM`, `EMAIL_TO`, `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_PASSWORD`

**Cron scheduling** — `scripts/run_daily.sh` sources `.env`, activates the venv, and runs the pipeline. Add to crontab:
```
0 18 * * 1-5 /absolute/path/to/stock-ai-agent/scripts/run_daily.sh >> /absolute/path/to/stock-ai-agent/logs/daily.log 2>&1
```
Logs land in `logs/` (gitignored except `.gitkeep`).
