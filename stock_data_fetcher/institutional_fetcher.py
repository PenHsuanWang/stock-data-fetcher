from __future__ import annotations
import datetime as dt
from typing import Iterable, Optional, Tuple
import pandas as pd

from .twse_api import fetch_t86_single, fetch_bfi82u_single

# Column mapping dictionaries (Chinese -> English)
T86_COL_MAP = {
    "證券代號": "code",
    "證券名稱": "name",
    "外資及陸資(不含外資自營商)買進股數": "foreign_buy",
    "外資及陸資(不含外資自營商)賣出股數": "foreign_sell",
    "外資及陸資(不含外資自營商)買賣超股數": "foreign_net",
    "外資自營商買進股數": "foreign_dealer_buy",
    "外資自營商賣出股數": "foreign_dealer_sell",
    "外資自營商買賣超股數": "foreign_dealer_net",
    "投信買進股數": "it_buy",
    "投信賣出股數": "it_sell",
    "投信買賣超股數": "it_net",
    "自營商買進股數(自行買賣)": "dealer_self_buy",
    "自營商賣出股數(自行買賣)": "dealer_self_sell",
    "自營商買賣超股數(自行買賣)": "dealer_self_net",
    "自營商買進股數(避險)": "dealer_hedge_buy",
    "自營商賣出股數(避險)": "dealer_hedge_sell",
    "自營商買賣超股數(避險)": "dealer_hedge_net",
    "三大法人買賣超股數": "three_investors_net"
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
    missing = []
    for d in dates:
        df = fetch_t86_single(d, retry=retry, retry_wait=retry_wait)
        if df is not None:
            frames.append(df)
        else:
            missing.append(d)
    if missing:
        print(f"[WARN] No T86 data for dates: {[x.isoformat() for x in missing]}")
    if not frames:
        return pd.DataFrame()
    t86 = pd.concat(frames, ignore_index=True)
    t86 = t86.rename(columns={k: v for k, v in T86_COL_MAP.items() if k in t86.columns})
    # Remove thousands separators and convert numeric columns
    numeric_cols = [
        "foreign_buy","foreign_sell","foreign_net",
        "foreign_dealer_buy","foreign_dealer_sell","foreign_dealer_net",
        "it_buy","it_sell","it_net",
        "dealer_self_buy","dealer_self_sell","dealer_self_net",
        "dealer_hedge_buy","dealer_hedge_sell","dealer_hedge_net",
        "three_investors_net"
    ]
    for c in numeric_cols:
        if c in t86.columns:
            t86[c] = pd.to_numeric(
                t86[c].astype(str).str.replace(",", "", regex=False),
                errors="coerce"
            ).astype("Int64")
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
