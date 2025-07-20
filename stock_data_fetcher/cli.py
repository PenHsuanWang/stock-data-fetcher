from __future__ import annotations
import argparse
import sys
import pathlib
import datetime as dt

from .utils import normalize_symbols, parse_date
from .fetcher import fetch_history, select_columns
from .writer import write_symbol_frames
from .exceptions import ValidationError, DownloadError, OutputError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-data-fetcher",
        description="Download historical stock data (CSV) from Yahoo Finance with per-symbol files."
    )
    parser.add_argument("--symbols", "--company-code", "-s", nargs="+", required=True,
                        help="One or more ticker symbols (numeric automatically suffixed with .TW).")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD (inclusive).")
    parser.add_argument("--end-date", required=False, help="End date in YYYY-MM-DD (inclusive).")
    parser.add_argument("--interval", default="1d",
                        choices=["1m","2m","5m","15m","30m","60m","90m",
                                 "1h","1d","5d","1wk","1mo","3mo"],
                        help="Data interval.")
    parser.add_argument("--file-format", default="csv", choices=["csv"],
                        help="Output file format (currently only csv).")
    parser.add_argument("--output-path", default="data",
                        help="Directory to store output files.")
    parser.add_argument("--columns", nargs="+",
                        help="Optional list of columns to keep (e.g. Close Volume).")
    parser.add_argument("--no-auto-adjust", action="store_true",
                        help="Disable automatic OHLC adjustment (splits/dividends).")
    parser.add_argument("--repair", action="store_true",
                        help="Enable yfinance repair flag for currency/unit mixups.")
    parser.add_argument("--show-summary", action="store_true",
                        help="Print summary after successful download.")
    parser.add_argument("--progress", action="store_true",
                        help="Show yfinance progress bar.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        symbols = normalize_symbols(args.symbols)
        if not symbols:
            raise ValidationError("No valid symbols provided.")
        start = parse_date(args.start_date)
        end = parse_date(args.end_date) if args.end_date else None
        if end and end < start:
            raise ValidationError("end-date must be >= start-date.")
    except ValidationError as ve:
        print(f"[ValidationError] {ve}", file=sys.stderr)
        return 2
    except ValueError as ve:
        print(f"[DateParseError] {ve}", file=sys.stderr)
        return 2

    try:
        data = fetch_history(
            symbols=symbols,
            start=start,
            end=end,
            interval=args.interval,
            auto_adjust=not args.no_auto_adjust,
            repair=args.repair,
            progress=args.progress
        )
        data = select_columns(data, args.columns)
    except DownloadError as de:
        print(f"[DownloadError] {de}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[UnexpectedDownloadError] {e}", file=sys.stderr)
        return 3

    output_dir = pathlib.Path(args.output_path)
    try:
        written = write_symbol_frames(
            df=data,
            symbols=symbols,
            output_dir=output_dir,
            start=start,
            end=end,
            file_format=args.file_format
        )
    except OutputError as oe:
        print(f"[OutputError] {oe}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"[UnexpectedOutputError] {e}", file=sys.stderr)
        return 4

    if args.show_summary:   
        print("=== Summary ===")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Date Range: {start} -> {end if end else 'latest'}")
        print(f"Interval: {args.interval}")
        print(f"Files:")
        for p in written:
            print(f"  - {p}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
