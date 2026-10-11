# Query and indexing analysis

## Indexes (created by the ingest script)

| Collection | Index | Why |
| --- | --- | --- |
| `sensor_readings` | `{sensor_id: 1, timestamp: -1}` | Latest and range queries for one sensor |
| `sensor_readings` | `{timestamp: -1}` | Station-wide time scans |
| `sensor_readings` | `{sensor_id: 1, anomaly.is_anomaly: 1, timestamp: -1}` | Sensor-wise violations |
| `sensor_readings` | `{anomaly.is_anomaly: 1, timestamp: -1}` | Global anomaly lists |
| `station_snapshots` | `{timestamp: -1}` | Current station status |
| `alerts` | `{timestamp: -1}` and `{sensor_id: 1, timestamp: -1}` | Recent alerts panel |

Without `{sensor_id, timestamp}` MongoDB would scan every channel document to draw one chart. The compound index matches the dashboard filter exactly.

## Aggregations

Hourly and daily statistics use `$match` → `$group` on `hour_bucket` / `day_bucket`. Those bucket fields are stored at ingest time so the pipeline does not recompute dates.

## Redis

Repeated dashboard polls read `iot:latest:*` and cached `/api/stats/*` payloads. A cache miss falls back to MongoDB. `/api/status` reports Redis as disconnected when `PING` fails; the API still serves MongoDB data.

## Benchmarks

`GET /api/benchmark` times five real queries with `time.perf_counter`:

1. latest PT08.S1 reading  
2. last 168 PT08.S1 hours  
3. recent alerts  
4. hourly aggregation  
5. daily aggregation  

If MongoDB is down the endpoint returns `mongo_connected: false` and an empty `results` list. It does not invent timings. Run it after ingesting data and paste the JSON into your report.
