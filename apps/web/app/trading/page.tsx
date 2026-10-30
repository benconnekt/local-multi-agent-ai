'use client';
import './trading.css';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {Activity,ArrowLeft,Bot,ChartNoAxesCombined,Clock3,Database,RefreshCw,ShieldAlert,ShieldCheck,Wallet} from 'lucide-react';
import ResearchLivePanel from '../../components/trading/ResearchLivePanel';
import ForexAgentOperations from '../../components/trading/ForexAgentOperations';

type Health={connected:boolean;service?:string;routeCount?:number;checkedAt?:string;error?:string};
const pairs=['EURUSD','GBPUSD','USDJPY'];
const agents=[['Price Action','Research integration pending'],['Technical Analysis','Research integration pending'],['News & Sentiment','Feed not connected'],['Risk Supervisor','Execution blocked'],['Decision Supervisor','NO_TRADE enforced by workflow']];
export default function TradingCommandCentre(){
 const [health,setHealth]=useState<Health|null>(null);const [loading,setLoading]=useState(false);const [last,setLast]=useState('');
 async function refresh(){setLoading(true);try{const r=await fetch('/api/trading/status',{cache:'no-store'});setHealth(await r.json() as Health);}catch{setHealth({connected:false,error:'Status check failed'});}finally{setLoading(false);setLast(new Date().toLocaleTimeString());}}
 useEffect(()=>{void refresh();},[]);
 return <main className="tr04"><div className="tr04-wrap">
 <header className="tr04-top"><div><Link href="/" className="tr04-back"><ArrowLeft size={15}/> Local Agent Studio</Link><div className="tr04-kicker">FOREX RESEARCH / TR-04</div><h1>Trading Command Centre</h1><p>Operational workspace for research, simulation and agent oversight.</p></div><div className="tr04-status"><span className="tr04-block"><ShieldAlert size={15}/> NO_TRADE</span><span className="tr04-muted">Research only · uncertified</span></div></header>
 <section className="tr04-banner"><ShieldCheck size={22}/><div><strong>Execution is disabled</strong><p>No broker order routes, practice orders, trade approval or execution controls are exposed in this interface. All strategy results remain uncertified.</p></div></section>
 <div className="tr04-grid tr04-kpis"><article><span>Research universe</span><strong>3 pairs</strong><small>EURUSD · GBPUSD · USDJPY</small></article><article><span>Decision gate</span><strong>NO_TRADE</strong><small>Fail-closed</small></article><article><span>Paper portfolio</span><strong>Not connected</strong><small>No invented P&amp;L</small></article><article><span>Backend status</span><strong>{health===null?'Checking…':health.connected?'Reachable':'Unavailable'}</strong><small>{health?.connected?'Local FastAPI OpenAPI responds':'Read-only connectivity check'}</small></article></div>
 <div className="tr04-grid tr04-main"><section className="tr04-card"><div className="tr04-heading"><h2><ChartNoAxesCombined size={19}/> Market watchlist</h2><span>Data integration pending</span></div><div className="tr04-table"><div className="tr04-tr tr04-th"><span>Instrument</span><span>Historical data</span><span>Research gate</span></div>{pairs.map(pair=><div className="tr04-tr" key={pair}><strong>{pair}</strong><span><Database size={14}/> Imported locally*</span><span className="tr04-no">NO_TRADE</span></div>)}</div><p className="tr04-foot">*Based on the previously reported OANDA import. This page does not verify files or fetch live prices.</p></section>
 <section className="tr04-card"><div className="tr04-heading"><h2><Bot size={19}/> Agent operations</h2><span>Configuration preview</span></div><div className="tr04-agent-list">{agents.map(([name,status])=><div key={name}><span className="tr04-agent-dot"/><strong>{name}</strong><small>{status}</small></div>)}</div><p className="tr04-foot">Agent states are labels, not observed runtime activity. Event-stream integration is next.</p></section>
 <section className="tr04-card"><div className="tr04-heading"><h2><Wallet size={19}/> Simulated portfolio</h2><span>Not connected</span></div><div className="tr04-empty"><Wallet size={28}/><strong>No simulated positions loaded</strong><p>Portfolio equity, drawdown and performance will appear only after a trusted simulation API is integrated.</p></div></section>
 <section className="tr04-card"><div className="tr04-heading"><h2><Activity size={19}/> System &amp; readiness</h2><button onClick={()=>void refresh()} disabled={loading} className="tr04-refresh"><RefreshCw size={15}/>{loading?'Checking…':'Refresh'}</button></div><div className="tr04-check"><span>Local FastAPI</span><strong className={health?.connected?'tr04-ok':'tr04-warn'}>{health===null?'Checking':health.connected?'Reachable':'Unavailable'}</strong></div><div className="tr04-check"><span>OpenAPI routes exposed</span><strong>{health?.connected?health.routeCount:'—'}</strong></div><div className="tr04-check"><span>Historical data certification</span><strong className="tr04-warn">Pending</strong></div><div className="tr04-check"><span>Independent strategy certification</span><strong className="tr04-warn">Pending</strong></div><div className="tr04-check"><span>Broker order execution</span><strong>Disabled</strong></div><p className="tr04-foot"><Clock3 size={13}/> Last checked: {last||'Not yet'} · No automatic polling</p></section></div>
 <ResearchLivePanel />
 <ForexAgentOperations />
 <footer className="tr04-footer">TR-04.1 · UI foundation + loopback-only backend connectivity · No live prices, fabricated agent runs or trade execution.</footer>
 </div></main>;
}
