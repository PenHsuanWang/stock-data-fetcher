# stock-data-fetcher

A Python CLI tool for efficiently downloading historical stock data from Yahoo Finance using the **yfinance** library. It creates **individual CSV files per symbol** with a consistent naming pattern:

```
<SYMBOL>_<START>_<END>.csv
```

Dates formatted as `YYYYMMDD`; if `END` is omitted, defaults to `latest`.

---

## Table of Contents

1. [Features](#features)
2. [Why Use stock-data-fetcher?](#why-use-stock-data-fetcher)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [CLI Usage](#cli-usage)
6. [Examples](#examples)
7. [File Naming](#file-naming)
8. [Adjusted Prices & Data Repair](#adjusted-prices--data-repair)
9. [TWSE Data Integration](#twse-data-integration)
10. [Architecture](#architecture)
11. [Module Overview](#module-overview)
12. [Data Flow](#data-flow)
13. [Error Handling](#error-handling)
14. [Column Filtering](#column-filtering)
15. [Inclusive Date Handling](#inclusive-date-handling)
16. [CLI Argument Reference](#cli-argument-reference)
17. [Testing](#testing)
18. [Packaging (PEP 621)](#packaging-pep-621)
19. [Performance](#performance)
20. [Roadmap](#roadmap)
21. [Contributing](#contributing)
22. [License](#license)
23. [Disclaimer](#disclaimer)
24. [Licensing Compliance](#licensing-compliance)

---

## Features

* **Batch Downloads**: Efficient multi-symbol downloads via threaded `yfinance.download`.
* **Symbol Normalization**: Automatically appends `.TW` to numeric Taiwan tickers.
* **Inclusive End Dates**: Compensates for yfinance's exclusive end-date behavior.
* **Custom Column Selection**: Download only needed columns (e.g., `Close Volume`).
* **Standardized CSV Output**: Predictable naming convention for downstream automation.
* **Adjusted Prices**: Default OHLC adjustment for dividends and splits (`auto_adjust`).
* **Data Repair Option**: Fixes known data anomalies (`--repair`).
* **Structured Errors & Exit Codes**: Robust error handling for automation workflows.
* **TWSE Institutional & Day-Trading Data**: Optional download of Taiwan Stock Exchange institutional (T86) flows and day-trade stats, with merge support (`--twse-t86`, `--twse-daytrade`, `--merge-twse`).
* **Modern Python Packaging**: Follows PEP 621 (`pyproject.toml`) standards.

---

## Why Use stock-data-fetcher?

Manually writing scripts to repeatedly download data is error-prone and inefficient. This CLI encapsulates best practices for data retrieval, consistent file naming, data integrity, and convenience—ideal for analysts, traders, and ML engineers.

---

## Installation

```bash
pip install stock-data-fetcher
```

Development installation:

```bash
pip install -e .
```

Python ≥3.10, dependencies: `yfinance`, `pandas`, `numpy`.

---

## Quick Start

```bash
stock-data-fetcher --symbols AAPL MSFT --start-date 2025-01-01 --end-date 2025-01-31 --show-summary
```

---

## CLI Usage

Use `--help` for detailed usage:

```bash
stock-data-fetcher --help
```

---

## Examples

**Single Taiwan stock (`2330` → `2330.TW`):**

```bash
stock-data-fetcher --symbols 2330 --start-date 2025-01-01 --end-date 2025-07-18
```

**Multiple symbols, selected columns:**

```bash
stock-data-fetcher -s AAPL GOOGL --start-date 2025-03-01 --end-date 2025-03-15 --columns Close Volume
```

**Disable adjustment, enable repair:**

```bash
stock-data-fetcher -s AAPL --start-date 2025-01-01 --no-auto-adjust --repair
```

**Custom directory:**

```bash
stock-data-fetcher -s AAPL MSFT --start-date 2025-04-01 --output-path data_out
```

**Fetch and merge TWSE institutional and day-trading data:**

```bash
stock-data-fetcher --symbols 2330 --start-date 2024-12-01 --end-date 2024-12-05 \
  --provider twse --twse-t86 --twse-daytrade --merge-twse
```

---

## File Naming

Generated files follow this pattern:

```
<SYMBOL>_<YYYYMMDD_START>_<YYYYMMDD_END>.csv
```

If `END` is omitted, `latest` is used.

---

## Adjusted Prices & Data Repair

* Default behavior (`auto_adjust=True`) adjusts OHLC prices.
* `--no-auto-adjust` retrieves raw exchange data.
* `--repair` corrects known currency/unit anomalies.

---

## TWSE Data Integration

The CLI can pull **supplementary data** from the Taiwan Stock Exchange:

* **Institutional investors (T86)** — per‑stock buy/sell volumes for foreign investors, dealers, and investment trusts.
* **Market aggregate funds (BFI82U)** — overall institutional fund flows.
* **Day trading stats (TWTB4U)** — daily day‑trading volume and ratios.

Enable these via:

```bash
--twse-t86        # T86 institutional flows
--twse-daytrade   # Day-trading statistics
--merge-twse      # Merge TWSE data with price files
```

When using TWSE data, set `--provider twse` and ensure `--intended-use private_research` to satisfy licence checks.

---

## Architecture

| Module          | Purpose                                |
| --------------- | -------------------------------------- |
| `cli.py`        | Command-line interaction, flow control |
| `utils.py`      | Symbol normalization, date parsing     |
| `fetcher.py`    | Batched data retrieval                 |
| `writer.py`     | CSV serialization                      |
| `exceptions.py` | Structured error handling              |

---

## Module Overview

* **cli.py:** Argument parsing, error handling.
* **utils.py:** Symbol/date normalization.
* **fetcher.py:** Fetches historical data (`yfinance.download`).
* **writer.py:** Writes data to CSV.
* **exceptions.py:** Custom exceptions (`ValidationError`, `DownloadError`, `OutputError`).

---

## Data Flow

CLI → Validation → Normalization → Data Fetching → Optional Column Filtering → CSV Writing → Summary Output.

---

## Error Handling

Exit codes indicate error type clearly:

* **2:** Validation errors (arguments, dates)
* **3:** Data retrieval errors (rate limits, invalid symbols)
* **4:** File system/output errors
* **5:** Licensing violations (data‑usage not permitted for chosen provider/intended‑use)

---

## Column Filtering

Use `--columns` to select specific columns, minimizing disk and memory use.

---

## Inclusive Date Handling

Internally adds one day to the end-date to include it (compensating for `yfinance` behavior).

---

## CLI Argument Reference

| Argument           | Required | Description                                            |
| ------------------ | -------- | ------------------------------------------------------ |
| `--symbols`, `-s`  | Yes      | Stock symbols (auto `.TW` for numeric).                |
| `--start-date`     | Yes      | Inclusive start date (`YYYY-MM-DD`).                   |
| `--end-date`       | No       | Inclusive end date (`YYYY-MM-DD`), defaults to latest. |
| `--interval`       | No       | Data frequency (`1d`, `1wk`, etc.).                    |
| `--provider`        | No       | Data source provider (`yahoo` \| `twse`). Defaults to `yahoo`. |
| `--intended-use`    | No       | Your planned use of the data (`private_research` \| `redistribute` \| `commercial`). |
| `--file-format`    | No       | Output format (`csv`; `parquet` planned).              |
| `--output-path`    | No       | Directory to save CSV files.                           |
| `--columns`        | No       | Columns to retain (e.g., `Close Volume`).              |
| `--no-auto-adjust` | No       | Disable adjusted OHLC prices.                          |
| `--repair`         | No       | Fix data anomalies.                                    |
| `--show-summary`   | No       | Show download summary after completion.                |
| `--progress`       | No       | Display progress bar during download.                  |
| `--twse-t86`       | No       | Fetch TWSE institutional investor (T86) data.          |
| `--twse-daytrade`  | No       | Fetch TWSE day-trading statistics (TWTB4U).            |
| `--merge-twse`     | No       | Merge TWSE data with price files per symbol.          |

---

## Testing

Unit tests cover key functions: symbol normalization, filename generation, and CLI parsing.

---

## Packaging (PEP 621)

Uses modern Python packaging standards (PEP 621), specified in `pyproject.toml`.

---

## Performance

Optimized for multi-symbol downloads using threading; optional column subsetting reduces resource usage.

---

## Roadmap

* Parquet and JSON support
* Retry mechanism with exponential backoff
* Options chain downloads
* Metadata manifest creation
* Caching and incremental downloads

---

## Contributing

Contributions are welcome:

* Keep modular structure intact.
* Write unit tests and maintain documentation.
* Reflect changes in CLI arguments and package metadata.

---

## License

Licensed under MIT. Note: Yahoo Finance data usage governed by Yahoo’s terms.

---

## Disclaimer

This tool is **not affiliated with or endorsed by Yahoo Finance**. Data provided is informational only; verify with official sources before making investment decisions.

---

## Licensing Compliance

By default the tool downloads from Yahoo Finance (`--provider yahoo`) which allows personal and redistributable use
under Yahoo’s terms.  
When `--provider twse` is selected the CLI enforces a **licence check**: only the `private_research`
intended‑use is permitted out‑of‑the‑box.  Any attempt to download TWSE data for `redistribute` or `commercial`
purposes will exit with code **5**.  
If you hold a valid TWSE market‑data agreement you may extend the policy matrix in `licensing.py`
to whitelist your use‑case.

*This simple guard is **not** a legal opinion—always verify your licences before publication.*

---
