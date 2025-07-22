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
ENDPOINT_DAYTRADE = "/rwd/zh/trading/exchange/MI_DAY_TRADING"  # Day trading stats

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
    Fetch day trading statistics for a single date.
    """
    params = {"date": date.strftime("%Y%m%d"), "response": "json"}
    js = _get_json(TWSE_BASE + ENDPOINT_DAYTRADE, params, retry=retry, retry_wait=retry_wait)
    if not js:
        return None
    df = pd.DataFrame(js.get("data", []), columns=js.get("fields", []))
    if df.empty:
        return None
    df["date"] = date
    return df
