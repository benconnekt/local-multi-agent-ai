 'use client';
import { useState } from 'react';
type Trade = {id?:string;instrument?:string;currentUnits?:string;price?:string;unrealizedPL?:string;openTime?:string;stopLossOrder?:{price?:string};takeProfitOrder?:{price?:string}};
type Overview = {status:string;environment:string;reason?:string;account_id_masked?:string;account?:Record<string,string|null>;trades?:Trade[];positions?:unknown[];broker_execution_enabled:boolean};
export default function OandaPracticeMonitor() {
  const [data,setData]=useState<Overview|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  async function refresh() {
    setBusy(true);setError('');
    try {
      const r=await fetch('/api/trading/forex/agents/broker/overview',{cache:'no-store'});
      if(!r.ok) throw Error(`Broker monitor unavailable (HTTP ${r.status})`);
      setData(await r.json());
    } catch(e) {setError(e instanceof Error?e.message:'Unable to load broker account');}
    finally {setBusy(false);}
  }
  return <section className="tr04-card" aria-label="OANDA practice monitoring" style={{marginTop:20}}>
    <div className="tr04-heading"><h2>OANDA practice account · read-only</h2><button className="tr04-refresh" onClick={()=>void refresh()} disabled={busy}>{busy?'Loading…':'Refresh account'}</button></div>
    <p className="tr04-foot">Practice account only. No live account access, broker orders or close operations. Values are never simulated.</p>
    {error&&<p role="alert">{error}</p>}
    {!data&&!error&&<p>Click Refresh account to retrieve current OANDA practice positions.</p>}
    {data&&data.status!=='connected'&&<p role="status">{data.status}: {data.reason}</p>}
    {data?.status==='connected'&&<>
      <p>Account {data.account_id_masked} · {data.account?.currency} · Source: OANDA practice API</p>
      <div style={{display:'flex',gap:20,flexWrap:'wrap'}}>
        {([['Balance','balance'],['Equity (NAV)','NAV'],['Unrealised P/L','unrealizedPL'],['Margin available','marginAvailable']] as const).map(([label,key])=><div key={key}><small>{label}</small><div><strong>{data.account?.[key]??'—'}</strong></div></div>)}
      </div>
      <h3>Open trades ({data.trades?.length??0})</h3>
      {(data.trades?.length??0)===0?<p>No open practice trades.</p>:<div style={{overflowX:'auto'}}><table><thead><tr><th>Trade ID</th><th>Pair</th><th>Units</th><th>Entry</th><th>Unrealised P/L</th><th>SL</th><th>TP</th><th>Decision record</th></tr></thead><tbody>{data.trades?.map(t=><tr key={t.id}><td>{t.id}</td><td>{t.instrument}</td><td>{t.currentUnits}</td><td>{t.price}</td><td>{t.unrealizedPL}</td><td>{t.stopLossOrder?.price??'—'}</td><td>{t.takeProfitOrder?.price??'—'}</td><td>Not recorded — no entry score available</td></tr>)}</tbody></table></div>}
      <p>Open aggregated positions: {data.positions?.length??0}. Trades and positions are different OANDA objects.</p>
    </>}
    <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:12}}>
      <button disabled title="Not authorised">Close Trade</button>
      <button disabled title="Not authorised">Close Selected</button>
      <button disabled title="Not authorised">Close All</button>
    </div>
    <p className="tr04-foot">Trade explanation and entry/current scores will only appear when a verified decision record exists.</p>
  </section>;
}
