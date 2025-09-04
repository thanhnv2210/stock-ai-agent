"""
risk_manager.py

Implements position sizing, stop-loss, and take-profit rules.
"""

import pandas as pd


class RiskManager:
    def __init__(self, max_position_pct: float = 0.1, stop_loss_pct: float = 0.05, take_profit_pct: float = 0.1):
        """
        :param max_position_pct: Maximum fraction of portfolio per trade
        :param stop_loss_pct: Stop loss threshold (e.g., 0.05 = 5%)
        :param take_profit_pct: Take profit threshold (e.g., 0.1 = 10%)
        """
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def apply_risk(self, df: pd.DataFrame, initial_cash: float = 100000) -> pd.DataFrame:
        """
        Apply risk rules to generate position sizes and PnL.
        Expects columns: Date, Close, Signal
        """
        df = df.copy()
        df["PositionSize"] = 0
        df["Cash"] = initial_cash
        df["PortfolioValue"] = initial_cash
        df["PnL"] = 0
        current_position = 0
        entry_price = 0

        for i, row in df.iterrows():
            signal = row["Signal"]
            price = row["Close"]

            # Entry rules
            if signal == 1 and current_position == 0:
                # Buy max allowed
                current_position = (self.max_position_pct * initial_cash) / price
                entry_price = price
            elif signal == -1 and current_position > 0:
                # Sell all
                df.at[i, "PnL"] = current_position * (price - entry_price)
                current_position = 0
                entry_price = 0

            # Apply stop-loss
            if current_position > 0 and price <= entry_price * (1 - self.stop_loss_pct):
                df.at[i, "PnL"] = current_position * (price - entry_price)
                current_position = 0
                entry_price = 0

            # Apply take-profit
            if current_position > 0 and price >= entry_price * (1 + self.take_profit_pct):
                df.at[i, "PnL"] = current_position * (price - entry_price)
                current_position = 0
                entry_price = 0

            df.at[i, "PositionSize"] = current_position
            df.at[i, "PortfolioValue"] = df.at[i, "Cash"] + current_position * price

        return df
