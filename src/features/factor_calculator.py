"""
factor_calculator.py

Computes basic technical indicators (factors) for stock data.
Inputs: CSV or Pandas DataFrame with OHLCV data
Outputs: DataFrame with added factor columns
"""

import pandas as pd
import numpy as np
from pathlib import Path


def calculate_moving_average(df: pd.DataFrame, window: int, price_col: str = "Close") -> pd.Series:
    """Calculate Simple Moving Average (SMA)."""
    return df[price_col].rolling(window=window).mean()


def calculate_rsi(df: pd.DataFrame, window: int = 14, price_col: str = "Close") -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = df[price_col].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=window).mean()
    avg_loss = pd.Series(loss).rolling(window=window).mean()

    rs = avg_gain / (avg_loss + 1e-10)  # avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(df: pd.DataFrame, short_window: int = 12, long_window: int = 26, signal_window: int = 9, price_col: str = "Close") -> pd.DataFrame:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    short_ema = df[price_col].ewm(span=short_window, adjust=False).mean()
    long_ema = df[price_col].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    hist = macd - signal

    return pd.DataFrame({
        "MACD": macd,
        "MACD_Signal": signal,
        "MACD_Hist": hist
    })


def add_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add multiple factors to the DataFrame.
    Expects columns: Date, Open, High, Low, Close, Volume
    """
    df = df.copy()

    # Moving Averages
    df["SMA_5"] = calculate_moving_average(df, 5)
    df["SMA_20"] = calculate_moving_average(df, 20)

    # RSI
    df["RSI_14"] = calculate_rsi(df, 14)

    # MACD
    macd_df = calculate_macd(df)
    df = pd.concat([df, macd_df], axis=1)

    return df


def process_csv(input_path: str, output_path: str):
    """
    Read historical data from CSV, calculate factors, and save to new CSV.
    """
    df = pd.read_csv(input_path)
    df = add_factors(df)
    Path(output_path).parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Factors saved to {output_path}")


if __name__ == "__main__":
    # Example usage: process a single file
    input_file = "data/AAPL_historical.csv"
    output_file = "data/AAPL_factors.csv"
    process_csv(input_file, output_file)
