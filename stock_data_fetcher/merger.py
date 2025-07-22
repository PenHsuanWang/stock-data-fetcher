from __future__ import annotations
import pandas as pd
from typing import Optional


def merge_price_institution_daytrade(
    price_df: pd.DataFrame,
    inst_df: Optional[pd.DataFrame],
    daytrade_df: Optional[pd.DataFrame],
    symbol: str,
    date_col: str = "Date"
) -> pd.DataFrame:
    """
    Merge price data with institutional (per-stock net flows) and day-trade stats.
    Assumes price_df has a DateTimeIndex or a date column. Symbol matching is case-sensitive to provided 'symbol'.
    """
    df = price_df.copy()
    # Normalize date column
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col]).dt.date
    elif df.index.name and "date" in df.index.name.lower():
        df[date_col] = df.index.date
    else:
        raise ValueError("Cannot locate date column in price frame.")

    # Filter institutional rows for symbol
    if inst_df is not None and not inst_df.empty:
        inst_sub = inst_df[inst_df.get("code") == symbol].copy()
        if "date" in inst_sub.columns:
            inst_sub["date"] = pd.to_datetime(inst_sub["date"]).dt.date
        df = df.merge(
            inst_sub.drop(columns=["name"], errors="ignore"),
            left_on=date_col,
            right_on="date",
            how="left",
            suffixes=("", "_inst")
        ).drop(columns=["date"], errors="ignore")

    if daytrade_df is not None and not daytrade_df.empty:
        dt_sub = daytrade_df[daytrade_df.get("code") == symbol].copy()
        if "date" in dt_sub.columns:
            dt_sub["date"] = pd.to_datetime(dt_sub["date"]).dt.date
        df = df.merge(
            dt_sub.drop(columns=["name"], errors="ignore"),
            left_on=date_col,
            right_on="date",
            how="left",
            suffixes=("", "_dt")
        ).drop(columns=["date"], errors="ignore")

    # Derive ratios if possible
    vol_col_candidates = [c for c in df.columns if c.lower() in ("volume", "vol")]
    vol_col = vol_col_candidates[0] if vol_col_candidates else None
    if vol_col and "foreign_net" in df.columns and df[vol_col].notna().any():
        df["foreign_net_ratio"] = df["foreign_net"] / df[vol_col]
    if vol_col and "daytrade_volume" in df.columns and df[vol_col].notna().any():
        df["daytrade_volume_ratio"] = df["daytrade_volume"] / df[vol_col]

    return df
