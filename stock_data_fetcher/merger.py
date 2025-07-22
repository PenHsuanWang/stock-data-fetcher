from __future__ import annotations
import pandas as pd
from typing import Optional

def _strip_symbol_suffix(symbol: str) -> str:
    """Get the numeric code part only, e.g., '2330.TW' → '2330'."""
    return str(symbol).split('.')[0].strip()

def merge_price_institution_daytrade(
    price_df: pd.DataFrame,
    inst_df: Optional[pd.DataFrame],
    daytrade_df: Optional[pd.DataFrame],
    symbol: str,
    date_col: str = "Date"
) -> pd.DataFrame:
    """
    Merge price data with institutional (per-stock net flows) and day-trade stats.
    Handles symbol with or without .TW suffix.
    """
    # Make a copy and ensure date_col is datetime.date
    df = price_df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col]).dt.date
    elif df.index.name and "date" in (df.index.name or "").lower():
        df[date_col] = df.index.date
    elif hasattr(df.index, "date"):
        df[date_col] = df.index.date
    else:
        raise ValueError("Cannot locate date column in price frame.")

    code_numeric = _strip_symbol_suffix(symbol)

    # -- Institutional data --
    if inst_df is not None and not inst_df.empty:
        # try to find a usable code column
        possible_code_cols = [c for c in inst_df.columns if c in ("code", "證券代號") or "代號" in c]
        code_col = possible_code_cols[0] if possible_code_cols else None
        if code_col:
            inst_codes = inst_df[code_col].astype(str).str.strip()
            inst_sub = inst_df[inst_codes == code_numeric].copy()
        else:
            inst_sub = inst_df.iloc[0:0].copy()
        if "date" in inst_sub.columns:
            inst_sub["date"] = pd.to_datetime(inst_sub["date"]).dt.date
        df = df.merge(
            inst_sub.drop(columns=["name"], errors="ignore"),
            left_on=date_col,
            right_on="date",
            how="left",
            suffixes=("", "_inst")
        ).drop(columns=["date"], errors="ignore")

    # -- Daytrade data --
    if daytrade_df is not None and not daytrade_df.empty:
        possible_code_cols_dt = [c for c in daytrade_df.columns if c in ("code", "code_dt", "證券代號") or "代號" in c]
        code_col_dt = possible_code_cols_dt[0] if possible_code_cols_dt else None
        if code_col_dt:
            dt_codes = daytrade_df[code_col_dt].astype(str).str.strip()
            dt_sub = daytrade_df[dt_codes == code_numeric].copy()
        else:
            dt_sub = daytrade_df.iloc[0:0].copy()
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