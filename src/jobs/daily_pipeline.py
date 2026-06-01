"""
daily_pipeline.py

Daily automation job:
1. Resolve symbol groups from tickers.json:
   - "db"      → watchlist table (holdings / potential)
   - "dynamic" → top-N NASDAQ by dollar turnover (yfinance screener)
2. Deduplicate symbols across groups; assign a primary group label per symbol
3. Incrementally fetch OHLCV → compute factors → persist to stock_ai.ohlcv_factors
4. Generate momentum signals → persist new rows to stock_ai.signals
5. Record group membership in stock_ai.symbol_groups
6. Alert via Notifier (console + optional Telegram / Slack / email)

Run:
    python -m src.jobs.daily_pipeline

Schedule (crontab example — weekdays at 6 PM):
    0 18 * * 1-5 /path/to/stock-ai-agent/scripts/run_daily.sh

Env vars:
    NASDAQ_TOP_N  - number of NASDAQ symbols to screen (default: 20)
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, date

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from src.agents.momentum_agent import MomentumAgent
from src.data.fetch_data import fetch_stock_data
from src.data.nasdaq_screener import fetch_nasdaq_top_by_turnover
from src.features.factor_calculator_v1 import add_factors
from src.notifications.notifier import Notifier
from src.db.database import init_schema
from src.db.repository import (
    get_last_date, get_factors, upsert_factors,
    get_last_signal_date, upsert_signals,
    get_watchlist, save_symbol_groups, save_signal_history,
)

# Primary group label priority when a symbol appears in multiple groups
_GROUP_PRIORITY = ["holdings", "potential", "nasdaq_top_turnover"]


class DailyPipeline:
    def __init__(self, config_path: str = "tickers.json"):
        with open(config_path) as f:
            self.group_config = json.load(f)["groups"]
        self.nasdaq_top_n = int(os.getenv("NASDAQ_TOP_N", "20"))
        self.agent = MomentumAgent()
        self.notifier = Notifier()
        asyncio.run(init_schema())

    # ------------------------------------------------------------------
    # Group resolution
    # ------------------------------------------------------------------

    def _resolve_groups(self) -> dict[str, list[str]]:
        """Return {group_name: [symbols]} for every configured group."""
        groups: dict[str, list[str]] = {}
        for name, cfg in self.group_config.items():
            group_type = cfg.get("type") if isinstance(cfg, dict) else "static"

            if group_type == "dynamic":
                print(f"\n[{name}] Fetching top {self.nasdaq_top_n} NASDAQ symbols by turnover...")
                symbols = fetch_nasdaq_top_by_turnover(self.nasdaq_top_n)
                print(f"  {len(symbols)} symbols fetched.")
            elif group_type == "db":
                symbols = asyncio.run(get_watchlist(name))
                print(f"\n[{name}] {len(symbols)} symbols from watchlist.")
            else:
                symbols = []

            groups[name] = symbols
        return groups

    def _primary_group(self, symbol: str, symbol_to_groups: dict[str, set[str]]) -> str:
        """Return the highest-priority group label for a symbol."""
        groups = symbol_to_groups[symbol]
        for g in _GROUP_PRIORITY:
            if g in groups:
                return g
        return next(iter(groups))  # fallback: any remaining group

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self):
        today = date.today()
        print(f"\n=== Daily Pipeline: {today} ===")

        groups = self._resolve_groups()
        asyncio.run(save_symbol_groups(today, groups))

        # Build symbol → set-of-groups map
        symbol_to_groups: dict[str, set[str]] = {}
        for group_name, symbols in groups.items():
            for sym in symbols:
                symbol_to_groups.setdefault(sym, set()).add(group_name)

        total = len(symbol_to_groups)
        print(f"\n{total} unique symbols across {len(groups)} groups.\n")

        # {group_name: [(symbol, signal_str, price), ...]}
        group_results: dict[str, list[tuple]] = {g: [] for g in groups}
        analysis_date: str = str(today)

        for symbol, group_set in symbol_to_groups.items():
            group_label = self._primary_group(symbol, symbol_to_groups)
            print(f"--- {symbol} [{group_label}] ---")
            try:
                factors_df = self._fetch_and_update_factors(symbol)
                if factors_df is None or factors_df.empty:
                    continue

                signals_df = self.agent.generate_signals(factors_df)

                last_signal_date = asyncio.run(get_last_signal_date(symbol))
                new_signals = (
                    signals_df[signals_df["Date"].dt.date > last_signal_date]
                    if last_signal_date else signals_df
                )
                asyncio.run(upsert_signals(symbol, new_signals))

                latest = signals_df.iloc[-1]
                signal = int(latest["Signal"])
                price = float(latest["Close"])
                analysis_date = str(latest["Date"])[:10]

                signal_str = {1: "BUY", -1: "SELL"}.get(signal, "HOLD")
                print(f"  {signal_str} @ ${price:.2f} on {analysis_date}")
                group_results[group_label].append((symbol, signal_str, price))

            except Exception as e:
                print(f"  ERROR: {e}")

        self._send_alert(group_results, analysis_date)
        asyncio.run(save_signal_history(today, analysis_date, group_results))

    # ------------------------------------------------------------------
    # Incremental data fetch
    # ------------------------------------------------------------------

    def _fetch_and_update_factors(self, symbol: str) -> pd.DataFrame:
        """Incrementally fetch new data, upsert to DB, return full DataFrame."""
        today = datetime.today().date()
        yesterday = today - timedelta(days=1)
        start_date = "2020-01-01"

        last_date = asyncio.run(get_last_date(symbol))
        if last_date is not None:
            if last_date >= yesterday:
                print(f"  Up-to-date (last: {last_date})")
                return asyncio.run(get_factors(symbol))
            start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"  Fetching {start_date} → {yesterday}")
        new_data = fetch_stock_data(symbol, start=start_date, end=yesterday.strftime("%Y-%m-%d"))

        if new_data.empty:
            print("  No new data available.")
            existing = asyncio.run(get_factors(symbol))
            return existing if not existing.empty else None

        new_factors = add_factors(new_data)
        asyncio.run(upsert_factors(symbol, new_factors))
        print(f"  +{len(new_factors)} rows saved to DB.")
        return asyncio.run(get_factors(symbol))

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def _send_alert(self, group_results: dict[str, list[tuple]], analysis_date: str):
        all_signals = [(sym, sig, price) for rows in group_results.values() for sym, sig, price in rows]
        buy_count  = sum(1 for _, s, _ in all_signals if s == "BUY")
        sell_count = sum(1 for _, s, _ in all_signals if s == "SELL")

        subject = f"Daily Pipeline ({date.today()}): {buy_count} BUY, {sell_count} SELL"

        body_lines = [f"Analysis date: {analysis_date}"]
        for group_name, rows in group_results.items():
            if not rows:
                continue
            body_lines.append(f"\n{group_name}")
            _ORDER = {"BUY": 0, "HOLD": 1, "SELL": 2}
            for sym, sig, price in sorted(rows, key=lambda r: _ORDER.get(r[1], 9)):
                body_lines.append(f"{sig}: {sym} - ${price:.2f}")

        self.notifier.send(subject=subject, body="\n".join(body_lines))


if __name__ == "__main__":
    pipeline = DailyPipeline()
    pipeline.run()
