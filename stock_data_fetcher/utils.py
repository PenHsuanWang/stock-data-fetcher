from __future__ import annotations
import re
import datetime as dt
from typing import Iterable, List

_NUMERIC_TW = re.compile(r"^\d{3,6}$")  # typical numeric ticker length for TW markets


def normalize_symbols(raw: Iterable[str], auto_tw: bool = True) -> List[str]:
    """
    Normalize user-provided symbols:
    - Trim whitespace
    - If numeric and auto_tw enabled, append '.TW'
    - Preserve order and uniqueness
    """
    seen = set()
    result: List[str] = []
    for s in raw:
        s2 = s.strip()
        if not s2:
            continue
        if auto_tw and _NUMERIC_TW.match(s2):
            s2 = s2 + ".TW"
        if s2 not in seen:
            seen.add(s2)
            result.append(s2)
    return result


def parse_date(date_str: str) -> dt.date:
    """Parse YYYY-MM-DD into date."""
    return dt.datetime.strptime(date_str, "%Y-%m-%d").date()


def format_date_for_filename(d: dt.date | None) -> str:
    """Return YYYYMMDD or 'latest' if None."""
    return d.strftime("%Y%m%d") if d else "latest"
