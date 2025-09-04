"""
backtester.py

Supports multiple symbols for backtesting:
- Loads factor data for each symbol
- Runs momentum agent and risk manager
- Combines results into one portfolio
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict
from src.agents.momentum_agent import MomentumAgent
from src.risk.risk_manager import RiskManager


class Backtester:
    def __init__(self, initial_cash: float = 100000):
        self.initial_cash = initial_cash

    def run_symbol_backtest(self, symbol: str, data_path: str) -> pd.DataFrame:
        """
        Backtest for a single symbol.
        """
        df = pd.read_csv(data_path)
        agent = MomentumAgent()
        df_signals = agent.generate_signals(df)

        risk = RiskManager()
        df_result = risk.apply_risk(df_signals, self.initial_cash / len(self.symbols))  # Split cash equally
        df_result["Symbol"] = symbol
        return df_result

    def run_portfolio_backtest(self, symbol_files: Dict[str, str]) -> pd.DataFrame:
        """
        Backtest a portfolio of multiple symbols.
        :param symbol_files: Dict of {symbol: csv_path}
        :return: Combined DataFrame of portfolio performance
        """
        self.symbols = list(symbol_files.keys())
        all_results = []

        for symbol, file_path in symbol_files.items():
            print(f"🔍 Backtesting {symbol}...")
            df_symbol = self.run_symbol_backtest(symbol, file_path)
            all_results.append(df_symbol)

        combined = pd.concat(all_results)
        portfolio = self._aggregate_portfolio(combined)
        return portfolio

    def _aggregate_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates portfolio value across multiple symbols.
        """
        portfolio = (
            df.groupby("Date")["PortfolioValue"]
            .sum()
            .reset_index()
            .rename(columns={"PortfolioValue": "TotalPortfolioValue"})
        )
        return portfolio

    def save_results(self, df: pd.DataFrame, output_path: str):
        Path(output_path).parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Portfolio results saved to {output_path}")

    @staticmethod
    def compute_metrics(df: pd.DataFrame) -> dict:
        """
        Compute performance metrics for portfolio.
        """
        final_value = df["TotalPortfolioValue"].iloc[-1]
        returns = df["TotalPortfolioValue"].pct_change().dropna()
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if len(returns) > 1 else 0
        max_drawdown = ((df["TotalPortfolioValue"].cummax() - df["TotalPortfolioValue"]).max())

        metrics = {
            "FinalPortfolioValue": final_value,
            "SharpeRatio": sharpe,
            "MaxDrawdown": max_drawdown
        }
        return metrics


if __name__ == "__main__":
    # Example usage
    symbol_files = {
        "AAPL": "data/AAPL_factors.csv",
        "MSFT": "data/MSFT_factors.csv",
        "GOOG": "data/GOOG_factors.csv"
    }

    bt = Backtester()
    df_portfolio = bt.run_portfolio_backtest(symbol_files)
    bt.save_results(df_portfolio, "data/portfolio_backtest.csv")
    metrics = bt.compute_metrics(df_portfolio)

    print("📊 Portfolio Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.2f}")
