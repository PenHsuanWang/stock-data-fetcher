from __future__ import annotations
import pathlib
import datetime as dt
import pandas as pd
from typing import Iterable
from .exceptions import OutputError
from .utils import format_date_for_filename


def ensure_dir(path: pathlib.Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def generate_filename(symbol: str, start: dt.date, end: dt.date | None, ext: str = "csv") -> str:
    """
    Filename pattern: <SYMBOL>_<START>_<END>.<ext>
    - START, END formatted as YYYYMMDD
    - END 'latest' if None
    """
    return f"{symbol}_{format_date_for_filename(start)}_{format_date_for_filename(end)}.{ext}"


def write_symbol_frames(
    df: pd.DataFrame,
    symbols: Iterable[str],
    output_dir: pathlib.Path,
    start: dt.date,
    end: dt.date | None,
    file_format: str = "csv",
    include_index: bool = True,
) -> list[pathlib.Path]:
    """
    Split multi-ticker DataFrame and write one file per symbol.
    Returns list of written file paths.
    """
    ensure_dir(output_dir)
    written = []

    for sym in symbols:
        if isinstance(df.columns, pd.MultiIndex):
            if sym not in df.columns.levels[0]:
                continue
            sub = df[sym]
        else:
            # Single ticker scenario: entire frame
            sub = df
        filename = generate_filename(sym, start, end, ext=file_format)
        filepath = output_dir / filename
        try:
            if file_format == "csv":
                sub.to_csv(filepath, index=include_index)
            else:
                raise OutputError(f"Unsupported file format requested: {file_format}")
        except Exception as e:
            raise OutputError(f"Failed to write {filepath}: {e}") from e
        written.append(filepath)
    return written
