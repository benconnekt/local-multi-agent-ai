'use client';
import OandaPracticeMonitor from './OandaPracticeMonitor';
import { useCallback, useEffect, useState } from 'react';
type Agent = {id:string; name:string; role:string; status:string; capability:string};
type Event = {id?:string;event_id?:string; agent_id:string; status:string; timestamp:string; duration_ms:number; summary:string};
type Run = {run_id:string; instrument:string; status:string; created_at:string; events:Event[]; findings:Record<string,{status:string;summary:string}>; report:null|{decision:string}; provenance?:{dataset_id:string;dataset_last_timestamp_utc:string;quality_status:string;historical_only:boolean}|null; error:null|string};
type Snapshot = {registry:{agents:Agent[]}; readiness:{orchestrator_connected:boolean;event_store_connected:boolean;activity_store:string}; runs:{runs:Run[]}};
export default function ForexAgentOperations() {
  const [data,setData] = useState<Snapshot|null>(null);
  const [instrument,setInstrument] = useState('EURUSD');
  const [evidenceMode,setEvidenceMode] = useState<'none'|'historical'>('none');
  const [error,setError] = useState<string|null>(null);
  const [submitting,setSubmitting] = useState(false);
  const refresh = useCallback(async (signal?:AbortSignal) => {
    try {
      const paths=['agents','agents/readiness','agents/runs'];
      const responses=await Promise.all(paths.map(p=>fetch(`/api/trading/forex/${p}`,{cache:'no-store',signal})));
      if(responses.some(r=>!r.ok)) throw Error('Forex research API unavailable');
      const [registry,readiness,runs]=await Promise.all(responses.map(r=>r.json()));
      if(!signal?.aborted) {setData({registry,readiness,runs});setError(null);}
    } catch(e) {if(!signal?.aborted)setError(e instanceof Error?e.message:'Refresh failed');}
  },[]);
  useEffect(()=>{
    const controller=new AbortController();
    void refresh(controller.signal);
    const interval=setInterval(()=>{if(!document.hidden) void refresh(controller.signal);},3000);
    return ()=>{controller.abort();clearInterval(interval);};
  },[refresh]);
  const active=data?.runs.runs.some(r=>r.status==='queued'||r.status==='running')??false;
  async function start() {
    setSubmitting(true);setError(null);
    try {
      const response=await fetch('/api/trading/forex/agents/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instrument,evidence_mode:evidenceMode})});
      if(!response.ok) throw Error(`Unable to start research (HTTP ${response.status})`);
      await refresh();
    } catch(e) {setError(e instanceof Error?e.message:'Run failed');}
    finally {setSubmitting(false);}
  }
  return <section className="tr04-card" aria-label="Forex agent operations" style={{marginTop:20}}>
    <div className="tr04-heading"><h2>Forex agent operations</h2><button className="tr04-refresh" onClick={()=>void refresh()}>Refresh</button></div>
    <p className="tr04-foot">Research-only · NO_TRADE · No broker execution. Activity is process-local and disappears on backend restart.</p>
    <div style={{display:'flex',gap:12,alignItems:'center',flexWrap:'wrap',marginBottom:16}}>
      <label htmlFor="forex-pair">Instrument</label>
      <select id="forex-pair" value={instrument} onChange={e=>setInstrument(e.target.value)}>{['EURUSD','GBPUSD','USDJPY'].map(p=><option key={p}>{p}</option>)}</select>
      <label htmlFor="forex-evidence-mode">Evidence</label>
      <select id="forex-evidence-mode" value={evidenceMode} onChange={e=>setEvidenceMode(e.target.value as 'none'|'historical')}>
        <option value="none">No evidence (baseline)</option>
        <option value="historical">OANDA historical H1 (uncertified)</option>
      </select>
      <button className="tr04-refresh" disabled={submitting||active} onClick={()=>void start()}>{submitting?'Starting…':active?'Research running…':'Start research'}</button>
    </div>
    {error&&<p role="alert">{error}</p>}
    {!data&&<p>Loading Forex operations…</p>}
    {data&&<>
      <p>Graph: {data.readiness.orchestrator_connected?'connected':'offline'} · Durable event store: {data.readiness.event_store_connected?'connected':'not connected'}</p>
      <div className="tr04-agent-list">{data.registry.agents.map(a=><div key={a.id}><strong>{a.name}</strong><small>{a.role} · {a.capability}</small></div>)}</div>
      <h3>Research runs</h3>
      {data.runs.runs.length===0?<p>No research runs yet.</p>:data.runs.runs.map(run=><article key={run.run_id} style={{borderTop:'1px solid currentColor',padding:'12px 0'}}>
        <strong>{run.instrument}</strong> · {run.status} · {run.report?.decision??'NO_TRADE'} <small>({run.created_at})</small>
        {run.provenance&&<p><strong>Historical evidence — NOT LIVE / NOT CERTIFIED:</strong> {run.provenance.dataset_id} · Last candle: {run.provenance.dataset_last_timestamp_utc} · {run.provenance.quality_status}</p>}
        {run.error&&<p role="alert">{run.error}</p>}{(run.status==='running'||run.status==='queued')&&<p role="status">Research {run.status} — waiting for agent results. Ollama stages may take several seconds.</p>}
        {Object.entries(run.findings).map(([agent,f])=><p key={agent}><strong>{agent}:</strong> {f.status} — {f.summary}{agent==='technical'&&run.provenance&&<small> · Historical observations; unverified commentary, not a signal</small>}</p>)}
        {run.events.length>0&&<details><summary>Agent execution events ({run.events.length})</summary><div style={{display:'grid',gap:8,padding:'12px 0'}}>{run.events.map((e,i)=><div key={e.event_id??e.id??`${run.run_id}-${e.agent_id??i}`} style={{display:'block',padding:'8px 10px',border:'1px solid currentColor',borderRadius:6,overflowWrap:'anywhere'}}><strong>{e.agent_id||'Unknown stage'}</strong> · {e.status||'unknown'} · {Number.isFinite(e.duration_ms)?`${e.duration_ms}ms`:'duration unavailable'}<div>{e.summary||'No execution summary supplied'}</div></div>)}</div></details>}
      </article>)}
    </>}
    <OandaPracticeMonitor />
  </section>;
}
