from datetime import datetime

from app.parser import iter_station_rows, parse_number, parse_timestamp
from app.sensor_catalog import SENSORS


def test_parse_number_accepts_european_decimals():
    assert parse_number("2,6") == 2.6
    assert parse_number("0,7578") == 0.7578
    assert parse_number("1360") == 1360.0


def test_parse_uci_timestamp():
    assert parse_timestamp("10/03/2004", "18.00.00") == datetime(2004, 3, 10, 18, 0, 0)


def test_sample_file_has_real_first_hours(sample_csv):
    rows = list(iter_station_rows(sample_csv))
    assert len(rows) == 48
    first = rows[0]
    assert first["timestamp"] == datetime(2004, 3, 10, 18, 0, 0)
    assert first["channels"]["CO_GT"]["value"] == 2.6
    assert first["channels"]["PT08_S1"]["value"] == 1360.0
    assert set(first["channels"]) == set(SENSORS)


def test_missing_sentinel_in_sample(sample_csv):
    rows = list(iter_station_rows(sample_csv))
    # 11/03/2004 03.00.00 has NOx(GT) and NO2(GT) tagged -200 in the UCI file.
    night = next(row for row in rows if row["timestamp"] == datetime(2004, 3, 11, 3, 0, 0))
    assert night["channels"]["NOX_GT"]["is_missing"] is True
    assert night["channels"]["NO2_GT"]["is_missing"] is True
    assert night["channels"]["PT08_S1"]["is_missing"] is False
