import type { Candle, Instrument, Timeframe } from './trading-api';

export type HistoricalDataset = {
  id: string;
  instrument: Instrument;
  timeframe: Timeframe;
  source: 'yahoo_finance';
  data_kind: 'historical_real';
  quality_status: string;
  retrieved_at_utc: string | null;
  count: number;
  first_timestamp: string;
  last_timestamp: string;
};
export type HistoricalDatasetCandles = HistoricalDataset & { candles: Candle[] };
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');

async function readJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal, cache: 'no-store' });
  if (!response.ok) throw new Error(`Historical data request failed (HTTP ${response.status})`);
  return response.json() as Promise<T>;
}
export const historicalApi = {
  datasets: (signal?: AbortSignal) => readJson<{datasets: HistoricalDataset[]}>('/trading/datasets', signal),
  candles: (id: string, signal?: AbortSignal) =>
    readJson<HistoricalDatasetCandles>(`/trading/datasets/${encodeURIComponent(id)}/candles`, signal),
};
