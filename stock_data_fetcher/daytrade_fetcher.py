from __future__ import annotations
import datetime as dt
from typing import Iterable
import pandas as pd

from .twse_api import fetch_daytrade_single

DAYTRADE_COL_MAP = {
    "證券代號": "code",
    "證券名稱": "name",
    "當日沖銷交易成交股數": "daytrade_volume",
    "當日沖銷交易買進成交股數": "daytrade_buy_volume",
    "當日沖銷交易賣出成交股數": "daytrade_sell_volume",
    "全部成交股數": "total_volume",
    "當日沖銷比率(%)": "daytrade_ratio_pct",
}


def collect_daytrade(dates: Iterable[dt.date], retry: int = 0, retry_wait: int = 3) -> pd.DataFrame:
    """Collect day trading statistics across dates. Logs missing dates and coerces numerics safely."""
    frames = []
    missing = []
    for d in dates:
        df = fetch_daytrade_single(d, retry=retry, retry_wait=retry_wait)
        if df is not None:
            frames.append(df)
        else:
            missing.append(d)
    if missing:
        print(f"[WARN] No daytrade data for dates: {[x.isoformat() for x in missing]}")
    if not frames:
        return pd.DataFrame()

    dt_df = pd.concat(frames, ignore_index=True)
    dt_df = dt_df.rename(columns={k: v for k, v in DAYTRADE_COL_MAP.items() if k in dt_df.columns})

    # Ensure a single 'code' column exists
    if "code" not in dt_df.columns:
        if "code_dt" in dt_df.columns:
            dt_df.rename(columns={"code_dt": "code"}, inplace=True)
        elif "證券代號" in dt_df.columns:
            dt_df.rename(columns={"證券代號": "code"}, inplace=True)

    # Safe numeric conversions
    for c in ["daytrade_volume", "daytrade_buy_volume", "daytrade_sell_volume", "total_volume"]:
        if c in dt_df.columns:
            dt_df[c] = pd.to_numeric(
                dt_df[c].astype(str).str.replace(",", "", regex=False),
                errors="coerce"
            ).astype("Int64")

    if "daytrade_ratio_pct" in dt_df.columns:
        dt_df["daytrade_ratio"] = pd.to_numeric(
            dt_df["daytrade_ratio_pct"].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False),
            errors="coerce"
        ) / 100.0

    return dt_df
