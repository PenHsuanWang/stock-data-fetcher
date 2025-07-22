from __future__ import annotations
import datetime as dt
import logging
import time
from typing import Optional, Dict, Any, List
import requests
import pandas as pd

logger = logging.getLogger(__name__)

TWSE_BASE = "https://www.twse.com.tw"
# Endpoints (CSV/JSON). We request JSON where possible for stability.
ENDPOINT_T86 = "/rwd/zh/fund/T86"        # Institutional investors by stock
ENDPOINT_BFI82U = "/rwd/zh/fund/BFI82U"  # Market aggregate
# Official "Objects for Day Trading" daily report (TWTB4U). JSON is available; CSV (open_data) as fallback.
ENDPOINT_DAYTRADE = "/exchangeReport/TWTB4U"

DEFAULT_TIMEOUT = 10


def _get_json(url: str, params: Dict[str, Any], retry: int = 0, retry_wait: int = 3) -> Optional[Dict[str, Any]]:
    """Generic GET returning JSON dict or None."""
    for attempt in range(retry + 1):
        try:
            r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            js = r.json()
            if js.get("stat") != "OK":
                logger.warning("Non-OK status from %s params=%s stat=%s", url, params, js.get("stat"))
                return None
            return js
        except Exception as exc:
            logger.warning("Request failed (%s/%s): %s", attempt + 1, retry + 1, exc)
            if attempt < retry:
                time.sleep(retry_wait)
    return None


def fetch_t86_single(date: dt.date, retry: int = 0, retry_wait: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch T86 (institutional investors by stock) for a single date.
    Returns a DataFrame or None if unavailable.
    """
    params = {"date": date.strftime("%Y%m%d"), "selectType": "ALL", "response": "json"}
    js = _get_json(TWSE_BASE + ENDPOINT_T86, params, retry=retry, retry_wait=retry_wait)
    if not js:
        return None
    df = pd.DataFrame(js.get("data", []), columns=js.get("fields", []))
    if df.empty:
        return None
    df["date"] = date
    return df


def fetch_bfi82u_single(date: dt.date, retry: int = 0, retry_wait: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch market aggregate institutional funds (BFI82U).
    """
    params = {"dayDate": date.strftime("%Y%m%d"), "type": "ALL", "response": "json"}
    js = _get_json(TWSE_BASE + ENDPOINT_BFI82U, params, retry=retry, retry_wait=retry_wait)
    if not js:
        return None
    df = pd.DataFrame(js.get("data", []), columns=js.get("fields", []))
    if df.empty:
        return None
    df["date"] = date
    return df


def fetch_daytrade_single(date: dt.date, retry: int = 0, retry_wait: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch day trading statistics (TWTB4U) for a single date.

    Strategy:
      1) Try JSON endpoint:  /exchangeReport/TWTB4U?date=YYYYMMDD&response=json
      2) If JSON not OK (stat != OK) or 404, fallback to CSV open_data endpoint.
      3) Return None on weekends/holidays (TWSE returns no data; we quietly skip).
    """
    # Skip weekends quickly to avoid useless requests
    if date.weekday() >= 5:
        return None

    params_json = {"date": date.strftime("%Y%m%d"), "response": "json"}
    js = _get_json(TWSE_BASE + ENDPOINT_DAYTRADE, params_json, retry=retry, retry_wait=retry_wait)

    df: Optional[pd.DataFrame] = None
    if js:
        tmp = pd.DataFrame(js.get("data", []), columns=js.get("fields", []))
        if not tmp.empty:
            df = tmp

    # Fallback to CSV if JSON failed or returned empty
    if df is None or df.empty:
        csv_url = f"{TWSE_BASE}{ENDPOINT_DAYTRADE}?response=open_data&date={date.strftime('%Y%m%d')}"
        try:
            tmp = pd.read_csv(csv_url)
            if not tmp.empty:
                df = tmp
        except Exception as exc:
            logger.warning("CSV fallback failed for daytrade %s: %s", date, exc)
            return None

    if df is None or df.empty:
        return None

    df["date"] = date
    return df
