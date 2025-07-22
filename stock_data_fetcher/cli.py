from __future__ import annotations
import argparse
import sys
import pathlib
import datetime as dt

from .utils import normalize_symbols, parse_date, format_date_for_filename
from .fetcher import fetch_history, select_columns
from .writer import write_symbol_frames, generate_filename
from .exceptions import ValidationError, DownloadError, OutputError

# TWSE fetchers and merger
from .institutional_fetcher import collect_t86
from .daytrade_fetcher import collect_daytrade
from .merger import merge_price_institution_daytrade

# ---------------------------------------------------------------------------
# Simple licensing policy (extendable)
# ---------------------------------------------------------------------------

class LicenseError(Exception):
    """Raised when intended use is not permitted for the chosen provider."""

_LICENCE_MATRIX = {
    ("yahoo", "private_research"): True,
    ("yahoo", "redistribute"): True,
    ("yahoo", "commercial"): True,
    ("twse", "private_research"): True,
    ("twse", "redistribute"): False,
    ("twse", "commercial"): False,
}

def check_license(provider: str, use_case: str) -> None:
    """Raise LicenseError if the provider/use_case combination is disallowed."""
    if not _LICENCE_MATRIX.get((provider, use_case), False):
        raise LicenseError(
            f"Use-case '{use_case}' is not permitted for provider '{provider}'. "
            "See TWSE terms or modify the policy matrix if you possess a licence."
        )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-data-fetcher",
        description=(
            "Download historical stock data (CSV) from Yahoo Finance or TWSE with per‑symbol files, "
            "including a basic licensing check."
        )
    )
    parser.add_argument("--symbols", "--company-code", "-s", nargs="+", required=True,
                        help="One or more ticker symbols (numeric automatically suffixed with .TW).")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD (inclusive).")
    parser.add_argument("--end-date", required=False, help="End date in YYYY-MM-DD (inclusive).")
    parser.add_argument("--interval", default="1d",
                        choices=["1m","2m","5m","15m","30m","60m","90m",
                                 "1h","1d","5d","1wk","1mo","3mo"],
                        help="Data interval.")
    parser.add_argument("--provider", default="yahoo", choices=["yahoo", "twse"],
                        help="Data provider backend (default: yahoo).")
    parser.add_argument("--intended-use", default="private_research",
                        choices=["private_research", "redistribute", "commercial"],
                        help="Declare how you will use the data for a basic licence check.")
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
    # New flags for TWSE integration and merging
    parser.add_argument("--twse-t86", action="store_true",
                        help="Fetch TWSE institutional (T86) data for the date range.")
    parser.add_argument("--twse-daytrade", action="store_true",
                        help="Fetch TWSE daytrade stats for the date range.")
    parser.add_argument("--merge-twse", action="store_true",
                        help="After fetch, merge Yahoo price and TWSE data by date per symbol and save as merged CSV.")
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
        check_license(args.provider, args.intended_use)
    except LicenseError as le:
        print(f"[LicenseError] {le}", file=sys.stderr)
        return 5

    # 1. Fetch Yahoo Finance price data (always)
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

    # 2. Optionally fetch TWSE data (T86 / daytrade)
    date_range = []
    if args.twse_t86 or args.twse_daytrade or args.merge_twse:
        if end:
            n_days = (end - start).days + 1
            date_range = [start + dt.timedelta(days=i) for i in range(n_days)]
        else:
            # If no end-date, fetch till today (inclusive)
            today = dt.date.today()
            n_days = (today - start).days + 1
            date_range = [start + dt.timedelta(days=i) for i in range(n_days)]
    t86_df = None
    daytrade_df = None
    if args.twse_t86:
        t86_df = collect_t86(date_range)
    if args.twse_daytrade:
        daytrade_df = collect_daytrade(date_range)

    # 3. Optionally merge and write merged output
    merged_written = []
    if args.merge_twse and (args.twse_t86 or args.twse_daytrade):
        import pandas as pd
        for symbol in symbols:
            symbol_csv = output_dir / generate_filename(symbol, start, end, ext=args.file_format)
            if not symbol_csv.exists():
                print(f"[MergeWarning] Price file not found for symbol {symbol}: {symbol_csv}", file=sys.stderr)
                continue
            price_df = pd.read_csv(symbol_csv, parse_dates=["Date"])
            merged_df = merge_price_institution_daytrade(
                price_df=price_df,
                inst_df=t86_df,
                daytrade_df=daytrade_df,
                symbol=symbol,
                date_col="Date"
            )
            merged_file = output_dir / f"{symbol}_TWSE_MERGED_{format_date_for_filename(start)}_{format_date_for_filename(end)}.csv"
            merged_df.to_csv(merged_file, index=False)
            merged_written.append(merged_file)

    # 4. Summary
    if args.show_summary:
        print("=== Summary ===")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Provider: {args.provider}")
        print(f"Date Range: {start} -> {end if end else 'latest'}")
        print(f"Interval: {args.interval}")
        print(f"Files:")
        for p in written:
            print(f"  - {p}")
        if merged_written:
            print(f"Merged TWSE/Yahoo output files:")
            for p in merged_written:
                print(f"  - {p}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())