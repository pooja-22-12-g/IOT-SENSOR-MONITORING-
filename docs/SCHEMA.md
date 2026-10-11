# IoT NoSQL schema

The system stores UCI Air Quality hours as MongoDB documents. One station hour becomes:

1. **13 `sensor_readings` documents** (one per channel) for `sensor_id + timestamp` queries
2. **1 `station_snapshots` document** with every channel together for the dashboard “current status”
3. **0 or more `alerts` documents** when a channel is missing, outside a threshold, spiking, or drifting

## `sensor_readings`

```json
{
  "device_id": "uci-air-quality-multisensor-1",
  "location": "Italian city roadside (UCI Air Quality 2004-2005)",
  "sensor_id": "PT08_S1",
  "sensor_name": "PT08.S1 tin oxide (CO targeted)",
  "channel_type": "metal_oxide",
  "target": "CO",
  "unit": "sensor_response",
  "timestamp": "2004-03-10T18:00:00",
  "hour_bucket": "2004-03-10T18:00:00",
  "day_bucket": "2004-03-10T00:00:00",
  "value": 1360.0,
  "is_missing": false,
  "anomaly": {
    "is_anomaly": false,
    "severity": "ok",
    "reasons": []
  }
}
```

## `station_snapshots`

One document per hour: `timestamp`, `channels.<sensor_id>`, `environment` (T, RH, AH), `anomaly_count`.

## `alerts`

Created only when `anomaly.is_anomaly` is true. Fields: `timestamp`, `sensor_id`, `severity`, `reasons`, `value`, `device_id`.

## `sensor_metadata`

Catalog plus drift baselines (median sensor/reference ratio and MAD) computed from the ingested CSV.

## Redis keys

| Key | Purpose |
| --- | --- |
| `iot:latest:{sensor_id}` | Last reading per channel |
| `iot:dashboard:summary` | Ingest counters |
| `iot:alerts:recent` | List of newest alerts |
| `iot:stats:{hour_bucket\|day_bucket}:...` | Cached aggregation JSON |
| `iot:replay:state` | Replay cursor |

TTL defaults to 60 seconds for aggregations.
