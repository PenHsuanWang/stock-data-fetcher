from __future__ import annotations
import datetime as dt
from typing import Sequence, Optional
import yfinance as yf
import pandas as pd

from .exceptions import DownloadError


def fetch_history(
    symbols: Sequence[str],
    start: dt.date,
    end: Optional[dt.date],
    interval: str = "1d",
    auto_adjust: bool = True,
    repair: bool = False,
    progress: bool = False,
    group_by: str = "ticker",
    threads: bool = True,
) -> pd.DataFrame:
    """
    Fetch historical price data using yfinance.download.

    Notes:
      - yfinance treats 'end' as exclusive; we add +1 day to make it inclusive logically.
      - Supports multi-ticker download for efficiency.
    """
    yf_end = (end + dt.timedelta(days=1)).isoformat() if end else None
    data = yf.download(
        tickers=" ".join(symbols),
        start=start.isoformat(),
        end=yf_end,
        interval=interval,
        auto_adjust=auto_adjust,
        repair=repair,
        progress=progress,
        group_by=group_by,
        threads=threads,
    )
    if data is None or data.empty:
        raise DownloadError("No data returned (possibly invalid symbols, date span, or rate limit).")
    return data


def select_columns(df: pd.DataFrame, columns: list[str] | None) -> pd.DataFrame:
    """
    Optionally select columns from (possibly multi-index) DataFrame.
    """
    if not columns:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        # Build list of (ticker, column) pairs preserving order
        keep = [(lvl0, c) for lvl0 in df.columns.levels[0] for c in columns if (lvl0, c) in df.columns]
        return df.loc[:, keep]
    else:
        # Single symbol case
        existing = [c for c in columns if c in df.columns]
        return df[existing]
