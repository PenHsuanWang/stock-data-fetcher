import datetime as dt
from stock_data_fetcher.writer import generate_filename

def test_generate_filename():
    start = dt.date(2025,1,1)
    end = dt.date(2025,7,18)
    fn = generate_filename("2330.TW", start, end)
    assert fn == "2330.TW_20250101_20250718.csv"
