import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
const DEFAULT_BACKEND = 'http://127.0.0.1:8000';
type Context = { params: Promise<{ path: string[] }> };
function upstreamUrl(path: string[]): URL | null {
  const suffix = path.join('/');
  if (!['agents', 'agents/activity', 'agents/readiness', 'agents/runs', 'agents/broker/overview', 'agents/lab/overview', 'agents/lab/indicators', 'agents/lab/diagnostics', 'agents/lab/historical/datasets', 'agents/lab/historical/backtest'].includes(suffix) &&
      !(path.length === 3 && path[0] === 'agents' && path[1] === 'runs' && /^[a-f0-9-]{36}$/.test(path[2]))) return null;
  const origin = new URL(process.env.FOREX_API_ORIGIN ?? DEFAULT_BACKEND);
  if (!['http:', 'https:'].includes(origin.protocol) || origin.username || origin.password) throw Error('Invalid origin');
  return new URL(`/api/v1/trading/${suffix}`, origin);
}
async function proxy(path: string[], method: 'GET' | 'POST', request: NextRequest) {
  let url: URL | null;
  try { url = upstreamUrl(path); } catch { return NextResponse.json({error: 'Invalid FOREX_API_ORIGIN'}, {status: 500}); }
  if (!url || (method === 'POST' && !['agents/runs', 'agents/lab/indicators', 'agents/lab/diagnostics', 'agents/lab/historical/datasets', 'agents/lab/historical/backtest'].includes(path.join('/')))) return NextResponse.json({error: 'Not found'}, {status: 404});
  try {
    const body = method === 'POST' ? await request.text() : undefined;
    if (body && body.length > 1500000) return NextResponse.json({error: 'Request too large'}, {status: 413});
    const upstream = await fetch(url, {method, body, headers: body ? {'Content-Type': 'application/json'} : {}, cache: 'no-store', signal: AbortSignal.timeout(path.join('/') === 'agents/lab/historical/backtest' ? 120000 : 8000)});
    const data = await upstream.json();
    return NextResponse.json(data, {status: upstream.status, headers: {'Cache-Control': 'no-store'}});
  } catch { return NextResponse.json({error: 'Forex API unreachable'}, {status: 503}); }
}
export async function GET(request: NextRequest, context: Context) { return proxy((await context.params).path, 'GET', request); }
export async function POST(request: NextRequest, context: Context) { return proxy((await context.params).path, 'POST', request); }
