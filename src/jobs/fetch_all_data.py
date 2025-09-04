"""
fetch_all_data.py

Batch job to fetch and process data for multiple stocks.
- Downloads historical price data for a list of tickers.
- Calculates technical indicators (factors).
- Saves each ticker's data as a CSV in data/ folder.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List

from src.data.fetch_data import fetch_stock_data
from src.features.factor_calculator import FactorCalculator


class BatchDataFetcher:
    def __init__(self, symbols: List[str], output_dir: str = "data"):
        self.symbols = symbols
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run(self, start: str = "2020-01-01", end: str = None):
        """
        Fetch and process data for all symbols.
        :param start: Start date for historical data (YYYY-MM-DD)
        :param end: End date (default: today)
        """
        end = end or datetime.today().strftime("%Y-%m-%d")

        for symbol in self.symbols:
            print(f"🔍 Fetching data for {symbol} from {start} to {end}")
            try:
                df = fetch_stock_data(symbol, start, end)

                # Calculate factors
                fc = FactorCalculator(df)
                df_factors = fc.add_all_factors()

                # Save
                output_file = self.output_dir / f"{symbol}_factors.csv"
                df_factors.to_csv(output_file, index=False)
                print(f"✅ Saved {symbol} data to {output_file}")
            except Exception as e:
                print(f"❌ Failed for {symbol}: {e}")


if __name__ == "__main__":
    # Add more symbols as needed
    symbols = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"]

    job = BatchDataFetcher(symbols)
    job.run(start="2020-01-01")
