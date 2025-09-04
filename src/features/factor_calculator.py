# src/features/factor_calculator.py
"""
factor_calculator.py
Calculates trading factors/indicators for a given stock DataFrame.
"""

import pandas as pd


class FactorCalculator:
    def __init__(self, df: pd.DataFrame):
        """
        :param df: DataFrame with columns: Date, Open, High, Low, Close, Adj_Close, Volume
        """
        self.df = df.copy()
        self.df.sort_values("Date", inplace=True)

    def add_moving_averages(self, short_window=10, long_window=50):
        self.df["SMA_Short"] = self.df["Close"].rolling(window=short_window).mean()
        self.df["SMA_Long"] = self.df["Close"].rolling(window=long_window).mean()
        return self

    def add_rsi(self, period=14):
        delta = self.df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        self.df["RSI"] = 100 - (100 / (1 + rs))
        return self

    def add_macd(self, short_window=12, long_window=26, signal_window=9):
        exp1 = self.df["Close"].ewm(span=short_window, adjust=False).mean()
        exp2 = self.df["Close"].ewm(span=long_window, adjust=False).mean()
        self.df["MACD"] = exp1 - exp2
        self.df["Signal"] = self.df["MACD"].ewm(span=signal_window, adjust=False).mean()
        return self

    def add_all_factors(self):
        self.add_moving_averages()
        self.add_rsi()
        self.add_macd()
        return self.df
