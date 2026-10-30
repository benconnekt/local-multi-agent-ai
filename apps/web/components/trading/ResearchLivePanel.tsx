"use client";
import { useCallback, useEffect, useState } from 'react';

type Item = { instrument: string; available: boolean; http_status?: number; data?: Record<string, unknown>; error?: string };
type Snapshot = { decision: 'NO_TRADE'; research_only: true; results: Item[] };
const stringValue = (value: unknown): string => typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' ? String(value) : 'Not reported';
export default function ResearchLivePanel() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true); setError('');
    try {
      const response = await fetch('/api/trading/research', { cache: 'no-store', signal });
      if (!response.ok) throw new Error(`Research request failed (HTTP ${response.status})`);
      const data: Snapshot = await response.json();
      if (data.decision !== 'NO_TRADE' || data.research_only !== true || !Array.isArray(data.results)) throw new Error('Research safety contract mismatch');
      setSnapshot(data);
    } catch (cause) { if (!signal?.aborted) { setError(cause instanceof Error ? cause.message : 'Unable to load research'); setSnapshot(null); } }
    finally { if (!signal?.aborted) setLoading(false); }
  }, []);
  useEffect(() => { const controller = new AbortController(); void refresh(controller.signal); return () => controller.abort(); }, [refresh]);
  return <section aria-label="Live research" style={{padding:20,border:'1px solid #526070',borderRadius:12,marginTop:20}}>
    <div style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'center'}}><h2 style={{margin:0}}>Research API · OANDA historical</h2><button type="button" disabled={loading} onClick={() => void refresh()}>{loading ? 'Loading…' : 'Refresh research'}</button></div>
    <p>Read-only historical research. Every accepted response must explicitly enforce NO_TRADE and uncertified status. No order execution.</p>
    {error && <p role="alert">{error}</p>}
    {!snapshot && !error && <p>Loading research results…</p>}
    {snapshot?.results.map(item => <article key={item.instrument} style={{borderTop:'1px solid #526070',padding:'12px 0'}}>
      <strong>{item.instrument}</strong> · <span>{item.available ? 'Research available' : 'Unavailable'}</span> · <strong>NO_TRADE</strong>
      {item.available ? <div><p>Decision: {stringValue(item.data?.decision)} · Quality certified: {stringValue(item.data?.quality_certified)} · Signal eligible: {stringValue(item.data?.research_signal_eligible)}</p><details><summary>Inspect verified API response</summary><pre style={{overflowX:'auto',whiteSpace:'pre-wrap'}}>{JSON.stringify(item.data,null,2)}</pre></details></div> : <p>{item.error || 'Not available'}</p>}
    </article>)}
    <small>Manual refresh only. No fabricated prices, trades, agent runs or performance figures.</small>
  </section>;
}
