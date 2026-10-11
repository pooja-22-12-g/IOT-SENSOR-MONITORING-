export type SensorMeta = {
  sensor_id: string;
  name: string;
  target: string;
  channel_type: string;
  unit: string;
};

export type Anomaly = {
  is_anomaly: boolean;
  severity: string;
  reasons: string[];
};

export type Reading = {
  sensor_id: string;
  sensor_name: string;
  timestamp: string;
  value: number | null;
  unit: string;
  is_missing: boolean;
  anomaly: Anomaly;
  cache_hit?: boolean;
};

export type Health = {
  sensor_id: string;
  name: string;
  health_score: number | null;
  status: string;
  missing_rate: number | null;
  anomaly_rate: number | null;
  drift_rate: number | null;
  sample_count: number;
};

export type Alert = {
  timestamp: string;
  sensor_id: string;
  severity: string;
  reasons: string[];
  value: number | null;
};

export type BucketStat = {
  sensor_id: string;
  bucket: string;
  avg: number;
  min: number;
  max: number;
  count: number;
  anomaly_count: number;
};

export type Dashboard = {
  latest_snapshot: {
    timestamp: string;
    anomaly_count: number;
    environment: { T: number | null; RH: number | null; AH: number | null };
    channels: Record<string, { value: number | null; is_missing: boolean; anomaly: Anomaly; unit: string }>;
  } | null;
  alert_count: number;
  reading_count: number;
  health: Health[];
  virtual_now: string | null;
};

export type Status = {
  mongo_connected: boolean;
  mongo_error: string | null;
  redis_connected: boolean;
  redis_error: string | null;
};
