# Real-Time IoT Sensor Monitoring System

College project: store UCI Air Quality sensor hours in MongoDB, cache hot statistics in Redis, flag abnormal readings, and replay history on a React dashboard.

## What is already in this folder

| Path | Role |
| --- | --- |
| `data/AirQualityUCI.csv` | Real UCI dataset |
| `backend/` | FastAPI, ingest, anomaly, health, benchmarks |
| `frontend/` | React + TypeScript + Vite + Recharts dashboard |
| `docs/` | Schema, indexes, Windows setup |
| `docker-compose.yml` | Optional MongoDB + Redis |

## Features

1. Time-series ingest of each UCI hour  
2. MongoDB documents + indexes on `timestamp` and `sensor_id`  
3. Redis latest-reading / stats / alert cache  
4. Threshold, missing, spike, and drift checks  
5. Health scores (completeness, stability, drift)  
6. Historical replay as a moving “virtual now”  
7. Dashboard: status, charts, alerts, comparison, filters  
8. Query timing endpoint (only reports times from a real/injected database)  
9. Pytest suite that does **not** need live MongoDB/Redis  

## Quick start (tests — no MongoDB)

Python 3.13 is enough:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
pytest
```

## Live demo

MongoDB and Redis must actually be running. See [docs/SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md).

```powershell
python backend\scripts\ingest.py
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then install Node.js and run `npm install` + `npm run dev` in `frontend/`.

`GET /api/status` tells you honestly whether MongoDB and Redis answered `ping`.

## Project mapping

| Deliverable | Where |
| --- | --- |
| IoT NoSQL schema | `docs/SCHEMA.md`, `backend/app/schema.py` |
| MongoDB ingest | `backend/scripts/ingest.py`, `backend/app/ingest.py` |
| Redis cache | `backend/app/cache.py` |
| Query/index analysis | `docs/QUERY_INDEXING.md` |
| Alert/anomaly module | `backend/app/anomaly.py`, `backend/app/health.py` |
| Dashboard | `frontend/src/App.tsx` |

## Dataset note

The UCI file uses `;` separators and comma decimals. Ground-truth gases are `CO(GT)`, `NMHC(GT)`, `C6H6(GT)`, `NOx(GT)`, `NO2(GT)`. `PT08.S1`–`S5` are the metal-oxide sensors. Warning/critical limits in `backend/app/sensor_catalog.py` are the 95th and 99th percentiles of **valid** values in `data/AirQualityUCI.csv`, not made-up numbers.
