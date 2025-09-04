"""
visualizer.py

Plots stock price, buy/sell signals, and portfolio value over time.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class Visualizer:
    @staticmethod
    def plot_signals(df: pd.DataFrame, symbol: str, output_path: str = None):
        """
        Plots stock price with buy/sell signals.
        :param df: DataFrame with columns: Date, Close, Signal, PortfolioValue (optional)
        :param symbol: Stock symbol
        :param output_path: Optional path to save the figure
        """
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])

        plt.figure(figsize=(14, 8))

        # Price chart
        plt.plot(df["Date"], df["Close"], label="Close Price", color="blue", alpha=0.6)

        # Buy and Sell signals
        buys = df[df["Signal"] == 1]
        sells = df[df["Signal"] == -1]
        plt.scatter(buys["Date"], buys["Close"], label="Buy", marker="^", color="green", alpha=1)
        plt.scatter(sells["Date"], sells["Close"], label="Sell", marker="v", color="red", alpha=1)

        plt.title(f"{symbol} - Trading Signals")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(alpha=0.3)

        if output_path:
            Path(output_path).parent.mkdir(exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"✅ Chart saved to {output_path}")
        else:
            plt.show()

    @staticmethod
    def plot_portfolio(df: pd.DataFrame, output_path: str = None):
        """
        Plots portfolio value over time.
        :param df: DataFrame with PortfolioValue column
        :param output_path: Optional path to save the figure
        """
        if "PortfolioValue" not in df.columns:
            raise ValueError("PortfolioValue column not found in DataFrame")

        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])

        plt.figure(figsize=(14, 6))
        plt.plot(df["Date"], df["PortfolioValue"], label="Portfolio Value", color="purple", linewidth=2)

        plt.title("Portfolio Value Over Time")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.legend()
        plt.grid(alpha=0.3)

        if output_path:
            Path(output_path).parent.mkdir(exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"✅ Portfolio chart saved to {output_path}")
        else:
            plt.show()


if __name__ == "__main__":
    symbol = "AAPL"
    input_file = "data/AAPL_portfolio.csv"

    df = pd.read_csv(input_file)

    viz = Visualizer()
    viz.plot_signals(df, symbol)
    viz.plot_portfolio(df)
