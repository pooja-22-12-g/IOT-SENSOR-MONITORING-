import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api";
import type { Alert, BucketStat, Dashboard, Reading, SensorMeta, Status } from "./types";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [sensors, setSensors] = useState<SensorMeta[]>([]);
  const [sensorId, setSensorId] = useState("PT08_S1");
  const [compareId, setCompareId] = useState("PT08_S2");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [hourly, setHourly] = useState<BucketStat[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [compare, setCompare] = useState<Record<string, Reading[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [benchmark, setBenchmark] = useState<string>("");
  const [playing, setPlaying] = useState(false);

  async function refresh() {
    try {
      const st = await api.status();
      setStatus(st);
      if (!st.mongo_connected) {
        setError(st.mongo_error || "MongoDB is not connected. Ingest data after MongoDB is running.");
        return;
      }
      const [sensorRes, dash, readingRes, hourRes, alertRes, cmp] = await Promise.all([
        api.sensors(),
        api.dashboard(),
        api.readings(sensorId, start || undefined, end || undefined),
        api.hourly(sensorId),
        api.alerts(sensorId),
        api.compare([sensorId, compareId]),
      ]);
      setSensors(sensorRes.sensors);
      setDashboard(dash);
      setReadings(readingRes.readings.slice().reverse());
      setHourly(hourRes.stats);
      setAlerts(alertRes.alerts);
      setCompare(cmp.series);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, [sensorId, compareId, start, end]);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      void api.replayTick().then(() => refresh());
    }, 2000);
    return () => window.clearInterval(id);
  }, [playing, sensorId, compareId, start, end]);

  const trend = useMemo(
    () =>
      readings.map((row) => ({
        time: row.timestamp.replace("T", " ").slice(0, 16),
        value: row.value,
      })),
    [readings],
  );

  const compareTrend = useMemo(() => {
    const a = compare[sensorId] || [];
    const b = compare[compareId] || [];
    const map = new Map<string, { time: string; a?: number | null; b?: number | null }>();
    a.forEach((row) => map.set(row.timestamp, { time: row.timestamp.replace("T", " ").slice(0, 16), a: row.value }));
    b.forEach((row) => {
      const current = map.get(row.timestamp) || { time: row.timestamp.replace("T", " ").slice(0, 16) };
      current.b = row.value;
      map.set(row.timestamp, current);
    });
    return Array.from(map.values()).sort((x, y) => x.time.localeCompare(y.time));
  }, [compare, sensorId, compareId]);

  const snapshot = dashboard?.latest_snapshot;
  const health = dashboard?.health || [];
  const anomalyCount = health.reduce((sum, item) => sum + (item.anomaly_rate || 0), 0);

  return (
    <div className="shell">
      <header className="header">
        <div>
          <h1>Real-Time IoT Sensor Monitoring</h1>
          <p className="muted">UCI Air Quality dataset replayed as hourly station readings</p>
        </div>
        <div className="pills">
          <span className={`pill ${status?.mongo_connected ? "ok" : "bad"}`}>
            MongoDB {status?.mongo_connected ? "connected" : "down"}
          </span>
          <span className={`pill ${status?.redis_connected ? "ok" : "bad"}`}>
            Redis {status?.redis_connected ? "connected" : "down"}
          </span>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="filters">
        <label>
          Sensor
          <select value={sensorId} onChange={(e) => setSensorId(e.target.value)}>
            {sensors.map((sensor) => (
              <option key={sensor.sensor_id} value={sensor.sensor_id}>
                {sensor.sensor_id} — {sensor.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Compare with
          <select value={compareId} onChange={(e) => setCompareId(e.target.value)}>
            {sensors.map((sensor) => (
              <option key={sensor.sensor_id} value={sensor.sensor_id}>
                {sensor.sensor_id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Start
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
        </label>
        <label>
          End
          <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
        </label>
        <button
          onClick={() => {
            void api.replayStart().then(() => {
              setPlaying(true);
              void refresh();
            });
          }}
        >
          Start replay
        </button>
        <button
          onClick={() => {
            setPlaying(false);
            void api.replayStop();
          }}
        >
          Pause
        </button>
        <button onClick={() => void refresh()}>Refresh</button>
        <button
          onClick={() => {
            void api.benchmark().then((body) => {
              if (!body.mongo_connected) {
                setBenchmark(body.error || "MongoDB is not connected");
                return;
              }
              setBenchmark(body.results.map((row) => `${row.name}: ${row.elapsed_ms} ms (n=${row.result_count})`).join(" | "));
            });
          }}
        >
          Run benchmark
        </button>
      </section>

      {benchmark && <p className="muted">{benchmark}</p>}

      <section className="grid">
        <article className="card">
          <h3>Current station time</h3>
          <div className="big">{snapshot?.timestamp?.replace("T", " ") || "—"}</div>
          <p className="muted">Replay cursor: {dashboard?.virtual_now || "latest ingested hour"}</p>
        </article>
        <article className="card">
          <h3>Environment</h3>
          <p>T {snapshot?.environment.T ?? "—"} °C</p>
          <p>RH {snapshot?.environment.RH ?? "—"} %</p>
          <p>AH {snapshot?.environment.AH ?? "—"}</p>
        </article>
        <article className="card">
          <h3>Anomaly count</h3>
          <div className="big">{dashboard?.alert_count ?? "—"}</div>
          <p className="muted">Stored alert documents. Window rates sum {anomalyCount.toFixed(2)}</p>
        </article>
        <article className="card">
          <h3>Hour anomalies now</h3>
          <div className="big">{snapshot?.anomaly_count ?? "—"}</div>
          <p className="muted">{dashboard?.reading_count ?? 0} readings stored</p>
        </article>
      </section>

      <section className="charts">
        <article className="card">
          <h2>Time-series trend ({sensorId})</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#1d4f91" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </article>
        <article className="card">
          <h2>Sensor comparison</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={compareTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="a" name={sensorId} stroke="#1d4f91" dot={false} />
              <Line type="monotone" dataKey="b" name={compareId} stroke="#c45c26" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="charts">
        <article className="card">
          <h2>Sensor health</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Sensor</th>
                <th>Score</th>
                <th>Status</th>
                <th>Missing</th>
                <th>Drift</th>
              </tr>
            </thead>
            <tbody>
              {health.map((row) => (
                <tr key={row.sensor_id}>
                  <td>{row.sensor_id}</td>
                  <td>{row.health_score ?? "—"}</td>
                  <td>{row.status}</td>
                  <td>{row.missing_rate ?? "—"}</td>
                  <td>{row.drift_rate ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
        <article className="card">
          <h2>Recent alerts</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Sensor</th>
                <th>Severity</th>
                <th>Reasons</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert, index) => (
                <tr key={`${alert.timestamp}-${alert.sensor_id}-${index}`}>
                  <td>{alert.timestamp.replace("T", " ")}</td>
                  <td>{alert.sensor_id}</td>
                  <td className={alert.severity === "critical" ? "crit" : "warn"}>{alert.severity}</td>
                  <td>{alert.reasons.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>

      <section className="card">
        <h2>Hourly statistics</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Bucket</th>
              <th>Avg</th>
              <th>Min</th>
              <th>Max</th>
              <th>Anomalies</th>
            </tr>
          </thead>
          <tbody>
            {hourly.slice(-12).map((row) => (
              <tr key={row.bucket}>
                <td>{String(row.bucket)}</td>
                <td>{row.avg.toFixed(2)}</td>
                <td>{row.min}</td>
                <td>{row.max}</td>
                <td>{row.anomaly_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
