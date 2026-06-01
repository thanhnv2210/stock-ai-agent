"""
nasdaq_screener.py

Fetches the top-N NASDAQ stocks by daily dollar turnover (volume × price)
using the yfinance screener API.

Strategy: pull the top 200 most-active stocks globally (predefined query),
filter to NASDAQ exchanges (NMS / NCM / NGM), then rank by dollar turnover.

Controlled by env var:
  NASDAQ_TOP_N  - number of symbols to return (default: 20)
"""

import os

import pandas as pd
from yfinance.screener import screen

_NASDAQ_EXCHANGES = {"NMS", "NCM", "NGM"}
_SCREENER_POOL = 200   # fetch this many most-actives before filtering


def fetch_nasdaq_top_by_turnover(n: int | None = None) -> list[str]:
    """
    Return the top-n NASDAQ symbols ranked by dollar turnover (volume × price).

    Fetches the top _SCREENER_POOL most-active stocks, keeps only NASDAQ-listed
    ones, computes dollar turnover, and returns the top-n by that metric.
    """
    if n is None:
        n = int(os.getenv("NASDAQ_TOP_N", "20"))

    result = screen("most_actives", count=_SCREENER_POOL)
    df = pd.DataFrame(result["quotes"])

    nasdaq_df = df[df["exchange"].isin(_NASDAQ_EXCHANGES)].copy()
    nasdaq_df["turnover"] = nasdaq_df["regularMarketVolume"] * nasdaq_df["regularMarketPrice"]
    nasdaq_df = nasdaq_df.sort_values("turnover", ascending=False).head(n)

    return nasdaq_df["symbol"].tolist()
