"""
momentum_agent.py

Simple momentum-based trading strategy:
- Buy when SMA_5 > SMA_20 and RSI > 50
- Sell when SMA_5 < SMA_20 or RSI < 50

Inputs: DataFrame with columns: Date, Close, SMA_5, SMA_20, RSI_14
Outputs: DataFrame with trade signals and positions
"""

import pandas as pd
from pathlib import Path


class MomentumAgent:
    def __init__(self, sma_short: int = 5, sma_long: int = 20, rsi_threshold: float = 50):
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.rsi_threshold = rsi_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals.
        :param df: DataFrame with columns: Date, Close, SMA_5, SMA_20, RSI_14
        :return: DataFrame with added columns: Signal, Position
        """
        df = df.copy()

        # Initialize signals
        df["Signal"] = 0

        # Buy when SMA_5 > SMA_20 and RSI > 50
        df.loc[(df["SMA_5"] > df["SMA_20"]) & (df["RSI_14"] > self.rsi_threshold), "Signal"] = 1

        # Sell when SMA_5 < SMA_20 or RSI < 50
        df.loc[(df["SMA_5"] < df["SMA_20"]) | (df["RSI_14"] < self.rsi_threshold), "Signal"] = -1

        # Position: 1 = long, -1 = short, 0 = no position
        df["Position"] = df["Signal"].replace(to_replace=0, method="ffill").fillna(0)

        return df

    def save_signals(self, df: pd.DataFrame, output_path: str):
        """
        Save signals to a CSV file.
        """
        Path(output_path).parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Strategy signals saved to {output_path}")


if __name__ == "__main__":
    # Example run
    input_file = "data/AAPL_factors.csv"
    output_file = "data/AAPL_signals.csv"

    df = pd.read_csv(input_file)
    agent = MomentumAgent()
    signals_df = agent.generate_signals(df)
    agent.save_signals(signals_df, output_file)
