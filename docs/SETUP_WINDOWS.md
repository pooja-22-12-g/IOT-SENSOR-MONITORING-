# Windows setup

This machine already has **Python 3.13**. **Node.js is not installed**, so the React dashboard cannot be started until you install it. MongoDB and Redis are required only for the live demo; automated tests use in-memory substitutes.

## 1. Python backend (required for tests)

In PowerShell, from the project folder:

```powershell
cd "C:\Users\91733\OneDrive\Desktop\iot sensor monitoring system"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
pytest
```

If execution policy blocks the venv script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Dataset

`data\AirQualityUCI.csv` is the UCI Air Quality file (semicolon separated, `-200` = missing).  
`data\sample_48h.csv` is the first 48 real hours, used by tests.

Analyze without databases:

```powershell
cd backend
python scripts\analyze.py
```

## 3. MongoDB and Redis for the live API

Option A — Docker Desktop, then from the project root:

```powershell
docker compose up -d
```

Option B — native installs

- MongoDB Community Server: https://www.mongodb.com/try/download/community  
- Redis: [Memurai](https://www.memurai.com/) on Windows, or Redis in WSL / Docker  

Copy environment defaults:

```powershell
copy .env.example .env
```

Ingest (fails with a JSON error if MongoDB is down; it will not pretend to succeed):

```powershell
cd backend
python scripts\ingest.py
```

Optional small ingest for a quicker demo:

```powershell
python scripts\ingest.py ..\data\sample_48h.csv
```

Start the API:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/api/status  
`mongo_connected` / `redis_connected` are real ping results.

## 4. Node.js dashboard

Install the LTS installer from https://nodejs.org then:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173  
The Vite dev server proxies `/api` to port 8000.

## 5. Demo flow

1. Ingest CSV  
2. Start FastAPI  
3. Start the dashboard  
4. Click **Start replay** — the UI advances one historical hour every two seconds  
5. Click **Run benchmark** and copy the measured milliseconds into your report
