import type { Alert, BucketStat, Dashboard, Reading, SensorMeta, Status } from "./types";

const API = "";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail?.error || body.detail || response.statusText);
  }
  return body as T;
}

async function postJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { method: "POST" });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail?.error || body.detail || response.statusText);
  }
  return body as T;
}

export const api = {
  status: () => getJson<Status>("/api/status"),
  sensors: () => getJson<{ sensors: SensorMeta[] }>("/api/sensors"),
  dashboard: () => getJson<Dashboard>("/api/dashboard"),
  readings: (sensorId: string, start?: string, end?: string) => {
    const params = new URLSearchParams({ sensor_id: sensorId, limit: "240" });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    return getJson<{ readings: Reading[] }>(`/api/readings?${params.toString()}`);
  },
  hourly: (sensorId: string) =>
    getJson<{ stats: BucketStat[] }>(`/api/stats/hourly?sensor_id=${encodeURIComponent(sensorId)}`),
  alerts: (sensorId?: string) => {
    const params = new URLSearchParams({ limit: "40" });
    if (sensorId) params.set("sensor_id", sensorId);
    return getJson<{ alerts: Alert[] }>(`/api/alerts?${params.toString()}`);
  },
  compare: (ids: string[]) =>
    getJson<{ series: Record<string, Reading[]> }>(`/api/compare?sensor_ids=${ids.join(",")}`),
  benchmark: () =>
    getJson<{ mongo_connected: boolean; error: string | null; results: { name: string; elapsed_ms: number; result_count: number }[] }>(
      "/api/benchmark",
    ),
  replayStart: () => postJson("/api/replay/start"),
  replayStop: () => postJson("/api/replay/stop"),
  replayTick: () => postJson("/api/replay/tick"),
};
