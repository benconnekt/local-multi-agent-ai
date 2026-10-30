import { NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
export async function GET() {
  const base = process.env.LOCAL_AGENT_API_URL || 'http://127.0.0.1:8000';
  // Local-only allowlist: never forward requests to arbitrary hosts.
  let url: URL;
  try { url = new URL(base); } catch { return NextResponse.json({connected:false,error:'Invalid backend URL'}, {status:503}); }
  if (!['127.0.0.1','localhost','::1'].includes(url.hostname) || !['http:','https:'].includes(url.protocol) || url.username || url.password) {
    return NextResponse.json({connected:false,error:'Backend must be loopback'}, {status:503});
  }
  try {
    const response = await fetch(new URL('/openapi.json', url), {cache:'no-store',signal:AbortSignal.timeout(3000)});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const json = await response.json() as {paths?:Record<string,unknown>; info?:{title?:string}};
    return NextResponse.json({connected:true,service:json.info?.title ?? 'FastAPI',routeCount:Object.keys(json.paths ?? {}).length, checkedAt:new Date().toISOString()}, {headers:{'Cache-Control':'no-store'}});
  } catch {return NextResponse.json({connected:false,error:'Backend unreachable or OpenAPI unavailable',checkedAt:new Date().toISOString()}, {headers:{'Cache-Control':'no-store'}});}
}
