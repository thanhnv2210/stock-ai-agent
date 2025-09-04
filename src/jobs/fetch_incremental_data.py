"""
fetch_incremental_data.py

Incrementally fetch stock data for symbols listed in tickers.json.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.data.fetch_data import fetch_stock_data
from src.features.factor_calculator import FactorCalculator


class IncrementalDataFetcher:
    def __init__(self, config_path: str = "tickers.json", output_dir: str = "data"):
        self.symbols = self._load_symbols(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _load_symbols(self, config_path: str) -> List[str]:
        """Load symbols from a JSON file."""
        with open(config_path, "r") as f:
            config = json.load(f)
        return config.get("symbols", [])

    def run(self):
        today = datetime.today().date()
        yesterday = today - timedelta(days=1)

        for symbol in self.symbols:
            output_file = self.output_dir / f"{symbol}_factors.csv"
            start_date = "2020-01-01"

            # If file exists, determine start date
            if output_file.exists():
                existing = pd.read_csv(output_file, parse_dates=["Date"])
                if not existing.empty:
                    last_date = existing["Date"].max().date()
                    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

                    if last_date >= yesterday:
                        print(f"⏩ {symbol}: Up-to-date (last date: {last_date})")
                        continue
                else:
                    existing = pd.DataFrame()
            else:
                existing = pd.DataFrame()

            print(f"🔍 Fetching {symbol} from {start_date} to {yesterday}")
            try:
                # Fetch only missing data
                new_data = fetch_stock_data(symbol, start=start_date, end=yesterday.strftime("%Y-%m-%d"))

                if new_data.empty:
                    print(f"⚠️ No new data for {symbol}")
                    continue

                # Calculate factors
                fc = FactorCalculator(new_data)
                new_factors = fc.add_all_factors()

                # Merge with existing
                updated_data = pd.concat([existing, new_factors], ignore_index=True)
                updated_data.to_csv(output_file, index=False)
                print(f"✅ Updated {symbol}: {len(new_factors)} new rows added")
            except Exception as e:
                print(f"❌ Failed for {symbol}: {e}")


if __name__ == "__main__":
    job = IncrementalDataFetcher(config_path="tickers.json")
    job.run()
