"""
execution_adapter.py

Simulates trade execution for paper trading or backtesting.

Features:
- Takes trade signals (from strategy)
- Simulates fills (market orders)
- Tracks portfolio cash, positions, and trade history
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


class ExecutionAdapter:
    def __init__(self, initial_cash: float = 100000, commission: float = 0.001):
        """
        :param initial_cash: Starting cash
        :param commission: Commission per trade (e.g., 0.001 = 0.1%)
        """
        self.cash = initial_cash
        self.portfolio = {}  # symbol -> position size
        self.commission = commission
        self.trade_log = []

    def execute_trade(self, symbol: str, price: float, signal: int):
        """
        Execute a trade based on signal.
        :param symbol: Stock symbol
        :param price: Execution price
        :param signal: 1=Buy, -1=Sell, 0=Hold
        """
        timestamp = datetime.now().isoformat()

        if signal == 1:  # Buy
            max_shares = (self.cash / price)
            shares = max_shares  # full allocation
            cost = shares * price * (1 + self.commission)
            if cost <= self.cash:
                self.cash -= cost
                self.portfolio[symbol] = self.portfolio.get(symbol, 0) + shares
                self.trade_log.append((timestamp, symbol, "BUY", shares, price, cost))
        elif signal == -1 and self.portfolio.get(symbol, 0) > 0:  # Sell
            shares = self.portfolio[symbol]
            proceeds = shares * price * (1 - self.commission)
            self.cash += proceeds
            self.trade_log.append((timestamp, symbol, "SELL", shares, price, proceeds))
            self.portfolio[symbol] = 0
        # signal == 0 => Hold, do nothing

    def run_execution(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Replay trade execution over a DataFrame with signals.
        :param df: DataFrame with columns: Date, Close, Signal
        :param symbol: Stock symbol
        :return: DataFrame with PortfolioValue at each step
        """
        df = df.copy()
        df["PortfolioValue"] = 0

        for i, row in df.iterrows():
            price = row["Close"]
            signal = row["Signal"]

            self.execute_trade(symbol, price, signal)

            # Calculate total value
            position_value = sum(self.portfolio.get(symbol, 0) * price for symbol in self.portfolio)
            df.at[i, "PortfolioValue"] = self.cash + position_value

        return df

    def save_trades(self, output_path: str):
        """
        Save trade log to CSV.
        """
        Path(output_path).parent.mkdir(exist_ok=True)
        trades_df = pd.DataFrame(self.trade_log, columns=["Timestamp", "Symbol", "Side", "Shares", "Price", "Amount"])
        trades_df.to_csv(output_path, index=False)
        print(f"✅ Trade log saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    symbol = "AAPL"
    input_file = "data/AAPL_signals.csv"
    output_trades = "data/AAPL_trades.csv"
    output_portfolio = "data/AAPL_portfolio.csv"

    df_signals = pd.read_csv(input_file)

    executor = ExecutionAdapter(initial_cash=100000, commission=0.001)
    result_df = executor.run_execution(df_signals, symbol)
    result_df.to_csv(output_portfolio, index=False)
    executor.save_trades(output_trades)

    print(f"📈 Final Portfolio Value: {result_df['PortfolioValue'].iloc[-1]:.2f}")
