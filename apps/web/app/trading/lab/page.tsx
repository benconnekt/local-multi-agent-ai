'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';

type Overview = {pairs:string[];strategies:{id:string;version:string;status:string;description:string}[];workstreams:Record<string,string>;limitations:string[];validation_pass:boolean};
type Diagnostics = Record<string,unknown>;
const base='/api/trading/forex/agents/lab';
export default function StrategyLab(){
  const [overview,setOverview]=useState<Overview|null>(null);
  const [error,setError]=useState('');
  const [ledger,setLedger]=useState('[]');
  const [cost,setCost]=useState('0');
  const [report,setReport]=useState<Diagnostics|null>(null);
  const [busy,setBusy]=useState(false);
  const [pair,setPair]=useState('EURUSD');
  const [spread,setSpread]=useState('0');
  const [slippage,setSlippage]=useState('0');
  const [historical,setHistorical]=useState<Record<string,any>|null>(null);
  const [datasets,setDatasets]=useState<Record<string,any>|null>(null);
  const [historyBusy,setHistoryBusy]=useState(false);
  useEffect(()=>{fetch(`${base}/historical/datasets`,{cache:'no-store'}).then(r=>r.json()).then(setDatasets).catch(()=>{})},[]);
  async function runHistorical(){setHistoryBusy(true);setError('');setHistorical(null);try{
    const response=await fetch(`${base}/historical/backtest`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instrument:pair,spread:Number(spread),slippage:Number(slippage)})});
    const data=await response.json();if(!response.ok)throw Error(data.detail||JSON.stringify(data));setHistorical(data);
  }catch(e){setError(String(e))}finally{setHistoryBusy(false)}}

  useEffect(()=>{fetch(`${base}/overview`,{cache:'no-store'}).then(async r=>{if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json()}).then(setOverview).catch(e=>setError(String(e)))},[]);
  async function analyse(){setBusy(true);setError('');setReport(null);try{
    const parsed:unknown=JSON.parse(ledger);if(!Array.isArray(parsed))throw Error('Ledger must be a JSON array');
    const response=await fetch(`${base}/diagnostics`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ledger:parsed,cost_r:Number(cost)})});
    const data=await response.json();if(!response.ok)throw Error(JSON.stringify(data));setReport(data);
  }catch(e){setError(String(e))}finally{setBusy(false)}}
  const card:React.CSSProperties={background:'#15212e',border:'1px solid #344252',borderRadius:12,padding:18};
  return <main style={{maxWidth:1150,margin:'0 auto',padding:'32px 22px 90px',color:'#e5edf4'}}>
    <p style={{color:'#81d3b5',letterSpacing:2,fontSize:12}}>FOREX / TR-05 RESEARCH</p>
    <h1>Strategy Intelligence Lab</h1>
    <p style={{color:'#afc2d0'}}>Research diagnostics and strategy proposals. No verified trading edge, no broker orders, no automatic strategy promotion.</p>
    <div role="status" style={{...card,background:'#2c281c',borderColor:'#77613a',margin:'22px 0'}}><strong>NO_TRADE · Research only · Independent certification pending</strong></div>
    {error&&<p role="alert" style={{color:'#ffb5b5',overflowWrap:'anywhere'}}>{error}</p>}
    <section style={{...card,marginBottom:24}} aria-label="Automated historical backtest">
      <h2>Automated OANDA historical research</h2>
      <p style={{color:'#afc2d0'}}>Run the frozen baseline against imported historical H1/M15 candles. This is a retrospective simulation, not independently certified and not a live signal.</p>
      <p>Imported dataset records: {datasets?.datasets?.length ?? 'Loading…'} · Provider: OANDA practice history</p>
      <div style={{display:'flex',gap:12,flexWrap:'wrap',alignItems:'end'}}>
        <label>Pair<select value={pair} onChange={e=>setPair(e.target.value)} style={{display:'block',padding:9,marginTop:6}}>{['EURUSD','GBPUSD','USDJPY'].map(p=><option key={p} value={p}>{p}</option>)}</select></label>
        <label>Spread (price units)<input type="number" min="0" max="0.1" step="0.00001" value={spread} onChange={e=>setSpread(e.target.value)} style={{display:'block',padding:9,marginTop:6,width:145}}/></label>
        <label>Slippage (price units)<input type="number" min="0" max="0.1" step="0.00001" value={slippage} onChange={e=>setSlippage(e.target.value)} style={{display:'block',padding:9,marginTop:6,width:145}}/></label>
        <button type="button" disabled={historyBusy} onClick={runHistorical} style={{background:'#7faf9a',color:'#101a1c',border:0,borderRadius:8,padding:'12px 18px'}}>{historyBusy?'Running historical backtest…':'Run historical backtest'}</button>
      </div>
      {historical&&<div style={{marginTop:18}}>
        <p><strong>Audit: {historical.audit?.audit_pass?'Reconciliation passed':'Reconciliation failed'}</strong> · Independent certification: NO</p>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:10}}>{[['Simulated',historical.simulated],['Wins',historical.wins],['Losses',historical.losses],['Unresolved',historical.unresolved],['Win rate',historical.win_rate==null?'N/A':(historical.win_rate*100).toFixed(1)+'%'],['Expectancy (R)',historical.expectancy_r==null?'N/A':historical.expectancy_r.toFixed(3)],['Total (R)',historical.total_r],['Max drawdown (R)',historical.max_drawdown_r]].map(([label,value])=><div key={String(label)} style={{...card,padding:12}}><small>{label}</small><p style={{fontSize:20,marginBottom:0}}>{String(value)}</p></div>)}</div>
        <h3>Historical hypothetical trades</h3>
        <div style={{overflowX:'auto'}}><table style={{width:'100%',textAlign:'left',borderSpacing:'12px 8px'}}><thead><tr><th>Signal UTC</th><th>Direction</th><th>Outcome</th><th>R</th></tr></thead><tbody>{(historical.trades??[]).map((t:any,i:number)=><tr key={i}><td>{t.signal_time_utc}</td><td>{t.direction}</td><td>{t.simulation?.outcome}</td><td>{t.simulation?.r_multiple??'Unresolved'}</td></tr>)}</tbody></table></div>
        {historical.trades_truncated&&<p>Showing first 200 trades only.</p>}
        <details><summary>Dataset IDs, audit warnings and raw research diagnostics</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify({...historical,trades:undefined},null,2)}</pre></details>
      </div>}
    </section>
    <section aria-label="Strategy versions" style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(230px,1fr))',gap:12}}>
      {overview?.strategies.map(s=><article key={s.id} style={card}><small style={{color:'#81d3b5'}}>{s.version}</small><h2 style={{fontSize:18}}>{s.id.replaceAll('_',' ')}</h2><p>{s.description}</p><small>{s.status}</small></article>)}
      {!overview&&!error&&<p>Loading research catalogue…</p>}
    </section>
    <section style={{...card,marginTop:24}} aria-label="Audited ledger diagnostics">
      <h2>Historical ledger diagnostics</h2>
      <p style={{color:'#afc2d0'}}>Paste a chronological array of audited hypothetical trades with signal_time_utc, outcome and r_multiple. No results are generated until you provide data. Cost is an assumed R deduction per resolved trade.</p>
      <label htmlFor="ledger-json">Trade ledger JSON</label>
      <textarea id="ledger-json" spellCheck={false} value={ledger} onChange={e=>setLedger(e.target.value)} rows={7} style={{width:'100%',marginTop:8,background:'#0b1420',color:'#e5edf4',border:'1px solid #526478',borderRadius:8,padding:12,fontFamily:'monospace'}} />
      <div style={{display:'flex',gap:14,alignItems:'end',marginTop:14,flexWrap:'wrap'}}><label>Assumed cost (R per trade)<input type="number" min="0" max="5" step="0.01" value={cost} onChange={e=>setCost(e.target.value)} style={{display:'block',padding:9,marginTop:6,width:160}}/></label><button type="button" disabled={busy} onClick={analyse} style={{background:'#7faf9a',color:'#101a1c',border:0,borderRadius:8,padding:'12px 18px',cursor:'pointer'}}>{busy?'Analysing…':'Analyse ledger'}</button></div>
      {report&&<div style={{marginTop:18}}><h3>Retrospective diagnostic · not certified</h3><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',background:'#0b1420',padding:16,borderRadius:8}}>{JSON.stringify(report,null,2)}</pre></div>}
    </section>
    <section style={{marginTop:24}}><h2>Implementation and validation gates</h2><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:12}}>{Object.entries(overview?.workstreams??{}).map(([id,status])=><article key={id} style={card}><strong>{id}</strong><p style={{color:'#afc2d0'}}>{status.replaceAll('_',' ')}</p></article>)}</div></section>
    <p style={{marginTop:28}}><Link href="/trading" style={{color:'#81d3b5'}}>Back to Trading Command Centre</Link></p>
  </main>
}
