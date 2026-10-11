"""Sensor metadata for the UCI Air Quality dataset.

Thresholds below are not invented: they are the 95th and 99th percentiles
of valid (non -200) values computed from data/AirQualityUCI.csv in this repo
(9,357 hourly rows). Missing values in the original file are tagged -200.
"""

from __future__ import annotations

from typing import Any

MISSING_SENTINEL = -200.0

# Channel definitions. "metal_oxide" = PT08.* device sensors.
# "reference" = certified analyzer ground truth. "environment" = T/RH/AH.
SENSORS: dict[str, dict[str, Any]] = {
    "CO_GT": {
        "column": "CO(GT)",
        "name": "CO reference analyzer",
        "target": "CO",
        "channel_type": "reference",
        "unit": "mg/m^3",
        "warn_high": 4.9,
        "crit_high": 6.8,
        "warn_low": None,
        "crit_low": None,
    },
    "PT08_S1": {
        "column": "PT08.S1(CO)",
        "name": "PT08.S1 tin oxide (CO targeted)",
        "target": "CO",
        "channel_type": "metal_oxide",
        "unit": "sensor_response",
        "warn_high": 1508.0,
        "crit_high": 1707.0,
        "warn_low": 647.0,
        "crit_low": None,
        "reference_sensor_id": "CO_GT",
    },
    "NMHC_GT": {
        "column": "NMHC(GT)",
        "name": "NMHC reference analyzer",
        "target": "NMHC",
        "channel_type": "reference",
        "unit": "ug/m^3",
        "warn_high": 660.0,
        "crit_high": 840.0,
        "warn_low": None,
        "crit_low": None,
    },
    "C6H6_GT": {
        "column": "C6H6(GT)",
        "name": "Benzene reference analyzer",
        "target": "C6H6",
        "channel_type": "reference",
        "unit": "ug/m^3",
        "warn_high": 24.6,
        "crit_high": 34.3,
        "warn_low": None,
        "crit_low": None,
    },
    "PT08_S2": {
        "column": "PT08.S2(NMHC)",
        "name": "PT08.S2 titania (NMHC targeted)",
        "target": "NMHC",
        "channel_type": "metal_oxide",
        "unit": "sensor_response",
        "warn_high": 1420.0,
        "crit_high": 1649.0,
        "warn_low": 383.0,
        "crit_low": None,
        "reference_sensor_id": "C6H6_GT",
    },
    "NOX_GT": {
        "column": "NOx(GT)",
        "name": "NOx reference analyzer",
        "target": "NOx",
        "channel_type": "reference",
        "unit": "ppb",
        "warn_high": 693.0,
        "crit_high": 1001.0,
        "warn_low": None,
        "crit_low": None,
    },
    "PT08_S3": {
        "column": "PT08.S3(NOx)",
        "name": "PT08.S3 tungsten oxide (NOx targeted)",
        "target": "NOx",
        "channel_type": "metal_oxide",
        "unit": "sensor_response",
        "warn_high": 1291.0,
        "crit_high": 1664.0,
        "warn_low": 322.0,
        "crit_low": None,
        "reference_sensor_id": "NOX_GT",
        "inverse_to_reference": True,
    },
    "NO2_GT": {
        "column": "NO2(GT)",
        "name": "NO2 reference analyzer",
        "target": "NO2",
        "channel_type": "reference",
        "unit": "ug/m^3",
        "warn_high": 200.0,
        "crit_high": 246.0,
        "warn_low": None,
        "crit_low": None,
    },
    "PT08_S4": {
        "column": "PT08.S4(NO2)",
        "name": "PT08.S4 tungsten oxide (NO2 targeted)",
        "target": "NO2",
        "channel_type": "metal_oxide",
        "unit": "sensor_response",
        "warn_high": 2029.0,
        "crit_high": 2365.0,
        "warn_low": 551.0,
        "crit_low": None,
        "reference_sensor_id": "NO2_GT",
    },
    "PT08_S5": {
        "column": "PT08.S5(O3)",
        "name": "PT08.S5 indium oxide (O3 targeted)",
        "target": "O3",
        "channel_type": "metal_oxide",
        "unit": "sensor_response",
        "warn_high": 1761.0,
        "crit_high": 2094.0,
        "warn_low": 221.0,
        "crit_low": None,
    },
    "T": {
        "column": "T",
        "name": "Temperature",
        "target": "T",
        "channel_type": "environment",
        "unit": "C",
        "warn_high": 34.5,
        "crit_high": 39.3,
        "warn_low": None,
        "crit_low": -1.9,
    },
    "RH": {
        "column": "RH",
        "name": "Relative humidity",
        "target": "RH",
        "channel_type": "environment",
        "unit": "%",
        "warn_high": 77.9,
        "crit_high": 82.9,
        "warn_low": 9.2,
        "crit_low": None,
    },
    "AH": {
        "column": "AH",
        "name": "Absolute humidity",
        "target": "AH",
        "channel_type": "environment",
        "unit": "g/m^3",
        "warn_high": 1.7256,
        "crit_high": 1.9624,
        "warn_low": 0.1847,
        "crit_low": None,
    },
}

DEVICE_ID = "uci-air-quality-multisensor-1"
LOCATION = "Italian city roadside (UCI Air Quality 2004-2005)"
COLUMN_TO_SENSOR_ID = {meta["column"]: sensor_id for sensor_id, meta in SENSORS.items()}


def sensor_list() -> list[dict[str, Any]]:
    return [{"sensor_id": sid, **meta} for sid, meta in SENSORS.items()]
