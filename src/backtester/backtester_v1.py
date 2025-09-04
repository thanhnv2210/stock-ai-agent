"""
backtester.py

Backtests a strategy with historical data and risk management.
Computes equity curve and performance metrics.
"""

import pandas as pd
from pathlib import Path
from src.agents.momentum_agent import MomentumAgent
from src.risk.risk_manager import RiskManager


class Backtester:
    def __init__(self, initial_cash: float = 100000):
        self.initial_cash = initial_cash

    def run_backtest(self, data_path: str) -> pd.DataFrame:
        """
        Run backtest pipeline:
        - Load data with factors
        - Generate signals
        - Apply risk manager
        """
        df = pd.read_csv(data_path)

        # Generate signals
        agent = MomentumAgent()
        df_signals = agent.generate_signals(df)

        # Apply risk
        risk = RiskManager()
        df_risk = risk.apply_risk(df_signals, self.initial_cash)

        return df_risk

    def save_results(self, df: pd.DataFrame, output_path: str):
        Path(output_path).parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Backtest results saved to {output_path}")

    @staticmethod
    def compute_metrics(df: pd.DataFrame) -> dict:
        """
        Compute performance metrics.
        """
        pnl = df["PnL"].sum()
        final_value = df["PortfolioValue"].iloc[-1]
        returns = df["PortfolioValue"].pct_change().dropna()
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if len(returns) > 1 else 0
        max_drawdown = ((df["PortfolioValue"].cummax() - df["PortfolioValue"]).max())

        metrics = {
            "TotalPnL": pnl,
            "FinalPortfolioValue": final_value,
            "SharpeRatio": sharpe,
            "MaxDrawdown": max_drawdown
        }
        return metrics


if __name__ == "__main__":
    input_file = "data/AAPL_factors.csv"
    output_file = "data/AAPL_backtest.csv"

    bt = Backtester()
    df_result = bt.run_backtest(input_file)
    bt.save_results(df_result, output_file)
    metrics = bt.compute_metrics(df_result)

    print("📊 Backtest Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.2f}")
