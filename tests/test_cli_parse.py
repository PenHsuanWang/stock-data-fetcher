from stock_data_fetcher.cli import build_parser

def test_cli_help_parse():
    parser = build_parser()
    args = parser.parse_args([
        "--symbols","2330","--start-date","2025-01-01",
        "--end-date","2025-01-05"
    ])
    assert args.start_date == "2025-01-01"
