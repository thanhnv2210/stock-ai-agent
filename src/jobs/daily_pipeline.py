"""
daily_pipeline.py

Daily automation job:
1. Incrementally fetch new OHLCV data for all symbols in tickers.json
2. Compute technical factors (SMA_5, SMA_20, RSI_14, MACD)
3. Generate momentum signals via MomentumAgent
4. Alert on buy/sell signals via Notifier

Run:
    python -m src.jobs.daily_pipeline

Schedule (crontab example — weekdays at 6 PM):
    0 18 * * 1-5 /path/to/stock-ai-agent/scripts/run_daily.sh
"""

import json
from datetime import datetime, timedelta, date
from pathlib import Path

import pandas as pd

from src.agents.momentum_agent import MomentumAgent
from src.data.fetch_data import fetch_stock_data
from src.features.factor_calculator_v1 import add_factors
from src.notifications.notifier import Notifier


class DailyPipeline:
    def __init__(self, config_path: str = "tickers.json", data_dir: str = "data"):
        with open(config_path) as f:
            self.symbols = json.load(f)["symbols"]
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.agent = MomentumAgent()
        self.notifier = Notifier()

    def run(self):
        print(f"=== Daily Pipeline: {date.today()} ===")
        alerts = []

        for symbol in self.symbols:
            print(f"\n--- {symbol} ---")
            try:
                factors_df = self._fetch_and_update_factors(symbol)
                if factors_df is None or factors_df.empty:
                    continue

                signals_df = self.agent.generate_signals(factors_df)
                signals_df.to_csv(self.data_dir / f"{symbol}_signals.csv", index=False)

                latest = signals_df.iloc[-1]
                signal = int(latest["Signal"])
                price = float(latest["Close"])
                latest_date = str(latest["Date"])[:10]

                if signal == 1:
                    alerts.append((symbol, "BUY", price, latest_date))
                    print(f"  BUY signal @ ${price:.2f} on {latest_date}")
                elif signal == -1:
                    alerts.append((symbol, "SELL", price, latest_date))
                    print(f"  SELL signal @ ${price:.2f} on {latest_date}")
                else:
                    print(f"  HOLD @ ${price:.2f} on {latest_date}")

            except Exception as e:
                print(f"  ERROR: {e}")

        self._send_alert(alerts)

    def _fetch_and_update_factors(self, symbol: str) -> pd.DataFrame:
        """Incrementally fetch new data and recompute factors. Returns full updated DataFrame."""
        output_file = self.data_dir / f"{symbol}_factors.csv"
        today = datetime.today().date()
        yesterday = today - timedelta(days=1)
        start_date = "2020-01-01"

        existing = pd.DataFrame()
        if output_file.exists():
            existing = pd.read_csv(output_file)
            existing["Date"] = pd.to_datetime(existing["Date"], utc=True).dt.tz_localize(None)
            if not existing.empty:
                last_date = existing["Date"].max().date()
                if last_date >= yesterday:
                    print(f"  Up-to-date (last: {last_date})")
                    return existing
                start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"  Fetching {start_date} to {yesterday}")
        new_data = fetch_stock_data(symbol, start=start_date, end=yesterday.strftime("%Y-%m-%d"))

        if new_data.empty:
            print("  No new data available.")
            return existing if not existing.empty else None

        new_factors = add_factors(new_data)
        updated = pd.concat([existing, new_factors], ignore_index=True)
        updated.to_csv(output_file, index=False)
        print(f"  +{len(new_factors)} rows added.")
        return updated

    def _send_alert(self, alerts: list):
        if not alerts:
            self.notifier.send(
                subject=f"Daily Pipeline ({date.today()}): No new signals",
                body=f"Processed {len(self.symbols)} symbols. No buy/sell signals today.",
            )
            return

        lines = [f"  {sym}: {action} @ ${price:.2f} ({dt})" for sym, action, price, dt in alerts]
        buy_count = sum(1 for _, a, _, _ in alerts if a == "BUY")
        sell_count = sum(1 for _, a, _, _ in alerts if a == "SELL")

        self.notifier.send(
            subject=f"Daily Pipeline ({date.today()}): {buy_count} BUY, {sell_count} SELL",
            body="\n".join(lines),
        )


if __name__ == "__main__":
    pipeline = DailyPipeline()
    pipeline.run()
