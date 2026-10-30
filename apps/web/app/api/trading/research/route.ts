import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
const PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY'] as const;
const API = (process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const ALLOWED = new Set(['http://127.0.0.1:8000/api/v1', 'http://localhost:8000/api/v1']);

type Result = { instrument: string; available: boolean; http_status?: number; data?: Record<string, unknown>; error?: string };
async function read(pair: typeof PAIRS[number]): Promise<Result> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`${API}/trading/strategy/analyse?instrument=${pair}&provider=oanda_v20`, { cache: 'no-store', signal: controller.signal });
    if (!response.ok) return { instrument: pair, available: false, http_status: response.status, error: `HTTP ${response.status}` };
    const payload: unknown = await response.json();
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return { instrument: pair, available: false, error: 'Invalid API response' };
    const data = payload as Record<string, unknown>;
    const safe = data.decision === 'NO_TRADE' && data.research_only === true && data.quality_certified === false && data.research_signal_eligible === false && data.independently_certified === false;
    if (!safe) return { instrument: pair, available: false, error: 'Research safety contract mismatch: response withheld' };
    return { instrument: pair, available: true, data };
  } catch { return { instrument: pair, available: false, error: 'Research endpoint unavailable or timed out' }; }
  finally { clearTimeout(timeout); }
}
export async function GET() {
  if (!ALLOWED.has(API)) return NextResponse.json({ error: 'Only approved loopback FastAPI endpoints are permitted' }, { status: 503 });
  const results = await Promise.all(PAIRS.map(read));
  return NextResponse.json({ decision: 'NO_TRADE', research_only: true, quality_certified: false, research_signal_eligible: false, independently_certified: false, provider: 'oanda_v20', results }, { headers: { 'Cache-Control': 'no-store' } });
}
