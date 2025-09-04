#!/usr/bin/env python3
"""
fetch_data.py

Fetches historical stock data using yfinance and saves it to a local CSV file.
Usage:
    python scripts/fetch_data.py --symbol AAPL --start 2020-01-01 --end 2025-01-01
"""

import argparse
import os
from pathlib import Path
import yfinance as yf
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def fetch_stock_data(symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a given symbol.
    
    :param symbol: Stock ticker (e.g., "AAPL")
    :param start: Start date (YYYY-MM-DD)
    :param end: End date (YYYY-MM-DD)
    :param interval: Data interval (e.g., "1d", "1h")
    :return: DataFrame with historical data
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)
    df.reset_index(inplace=True)
    return df


def save_data(df: pd.DataFrame, symbol: str) -> str:
    """
    Save fetched stock data to CSV.
    
    :param df: DataFrame containing stock data
    :param symbol: Stock ticker
    :return: Path to saved CSV
    """
    DATA_DIR.mkdir(exist_ok=True)
    file_path = DATA_DIR / f"{symbol.upper()}_historical.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)


def main():
    parser = argparse.ArgumentParser(description="Fetch historical stock data and save to CSV.")
    parser.add_argument("--symbol", required=True, help="Stock ticker symbol, e.g., AAPL")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
    args = parser.parse_args()

    print(f"Fetching data for {args.symbol} from {args.start} to {args.end}...")

    df = fetch_stock_data(args.symbol, args.start, args.end, args.interval)
    file_path = save_data(df, args.symbol)

    print(f"✅ Data saved to {file_path}")


if __name__ == "__main__":
    main()
