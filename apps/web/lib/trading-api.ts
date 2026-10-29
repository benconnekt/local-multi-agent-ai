export type Instrument = "EURUSD" | "GBPUSD" | "USDJPY";
export type Timeframe = "M15" | "H1" | "H4" | "D1";
export type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
};
export type InstrumentsResponse = {
  instruments: { symbol: Instrument; display_name: string }[];
  timeframes: Timeframe[];
};
export type CandlesResponse = {
  instrument: Instrument;
  timeframe: Timeframe;
  source: "local_csv";
  data_kind: "synthetic";
  count: number;
  candles: Candle[];
};

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal, cache: "no-store" });
  if (!response.ok) {
    if (response.status === 404) throw new Error("No historical CSV dataset exists for this instrument and timeframe.");
    if (response.status === 422) throw new Error("The requested market data is invalid or failed validation.");
    throw new Error(`Market data request failed (HTTP ${response.status}).`);
  }
  return (await response.json()) as T;
}

export const tradingApi = {
  instruments: (signal?: AbortSignal) => getJson<InstrumentsResponse>("/trading/instruments", signal),
  candles: (instrument: Instrument, timeframe: Timeframe, signal?: AbortSignal) =>
    getJson<CandlesResponse>(`/trading/candles?instrument=${encodeURIComponent(instrument)}&timeframe=${encodeURIComponent(timeframe)}`, signal),
};
