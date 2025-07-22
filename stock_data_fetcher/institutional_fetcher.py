from __future__ import annotations
import datetime as dt
from typing import Iterable, Optional, Tuple
import pandas as pd

from .twse_api import fetch_t86_single, fetch_bfi82u_single

# Column mapping dictionaries (Chinese -> English)
T86_COL_MAP = {
    "證券代號": "code",
    "證券名稱": "name",
    "外陸資買進股數": "foreign_buy",
    "外陸資賣出股數": "foreign_sell",
    "外陸資買賣超股數": "foreign_net",
    "投信買進股數": "it_buy",
    "投信賣出股數": "it_sell",
    "投信買賣超股數": "it_net",
    "自營商買進股數": "dealer_buy",
    "自營商賣出股數": "dealer_sell",
    "自營商買賣超股數": "dealer_net",
}

BFI82U_COL_MAP = {
    "單位名稱": "unit",
    "買進金額": "buy_value",
    "賣出金額": "sell_value",
    "買賣差額": "net_value",
}


def collect_t86(
    dates: Iterable[dt.date],
    retry: int = 0,
    retry_wait: int = 3
) -> pd.DataFrame:
    """Loop over dates collecting T86 data; returns concatenated DataFrame (may be empty)."""
    frames = []
    for d in dates:
        df = fetch_t86_single(d, retry=retry, retry_wait=retry_wait)
        if df is not None:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    t86 = pd.concat(frames, ignore_index=True)
    t86 = t86.rename(columns={k: v for k, v in T86_COL_MAP.items() if k in t86.columns})
    # Remove thousands separators and convert numeric columns
    for c in ["foreign_buy","foreign_sell","foreign_net","it_buy","it_sell",
              "it_net","dealer_buy","dealer_sell","dealer_net"]:
        if c in t86.columns:
            t86[c] = t86[c].astype(str).str.replace(",", "", regex=False).astype("Int64")
    return t86


def collect_bfi82u(
    dates: Iterable[dt.date],
    retry: int = 0,
    retry_wait: int = 3
) -> pd.DataFrame:
    """Loop over dates collecting BFI82U market aggregate funds data."""
    frames = []
    for d in dates:
        df = fetch_bfi82u_single(d, retry=retry, retry_wait=retry_wait)
        if df is not None:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    bfi = pd.concat(frames, ignore_index=True)
    bfi = bfi.rename(columns={k: v for k, v in BFI82U_COL_MAP.items() if k in bfi.columns})
    # Numeric conversion
    for c in ["buy_value", "sell_value", "net_value"]:
        if c in bfi.columns:
            bfi[c] = bfi[c].astype(str).str.replace(",", "", regex=False).astype("Int64")
    return bfi
