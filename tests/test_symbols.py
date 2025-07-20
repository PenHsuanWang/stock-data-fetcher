from stock_data_fetcher.utils import normalize_symbols

def test_numeric_tw_suffix():
    assert normalize_symbols(["2330", "AAPL", "2330"]) == ["2330.TW", "AAPL"]
