"use client";

import { useEffect, useState } from "react";
import CandlestickChart from "@/components/trading/CandlestickChart";
import { tradingApi, type CandlesResponse, type Instrument, type InstrumentsResponse, type Timeframe } from "@/lib/trading-api";
import StrategyResearchPanel from '@/components/trading/StrategyResearchPanel';

export default function TradingPage() {
  const [catalogue, setCatalogue] = useState<InstrumentsResponse | null>(null);
  const [instrument, setInstrument] = useState<Instrument>("EURUSD");
  const [timeframe, setTimeframe] = useState<Timeframe>("H1");
  const [dataset, setDataset] = useState<CandlesResponse | null>(null);
  const [catalogueError, setCatalogueError] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    tradingApi.instruments(controller.signal)
      .then(setCatalogue)
      .catch((error: unknown) => { if (!controller.signal.aborted) setCatalogueError(error instanceof Error ? error.message : "Could not load instruments."); });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setDataset(null);
    setDataError(null);
    tradingApi.candles(instrument, timeframe, controller.signal)
      .then(setDataset)
      .catch((error: unknown) => { if (!controller.signal.aborted) setDataError(error instanceof Error ? error.message : "Could not load candles."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [instrument, timeframe, reload]);

  const instruments = catalogue?.instruments ?? [
    { symbol: "EURUSD" as Instrument, display_name: "EUR/USD" },
    { symbol: "GBPUSD" as Instrument, display_name: "GBP/USD" },
    { symbol: "USDJPY" as Instrument, display_name: "USD/JPY" },
  ];
  const timeframes = catalogue?.timeframes ?? (["M15", "H1", "H4", "D1"] as Timeframe[]);

  return (
    <main className="min-h-screen bg-slate-950 px-5 py-8 text-slate-100 md:px-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <a href="/" className="text-sm text-emerald-400 hover:underline">← Local Agent Studio</a>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">Forex Research</h1>
            <p className="mt-2 text-sm text-slate-400">Historical market-data workspace · Research only</p>
          </div>
          <span className="rounded-full border border-amber-600/50 bg-amber-950 px-3 py-1 text-xs font-semibold text-amber-200">SYNTHETIC DATA · NO TRADING</span>
        </header>

        <div role="note" className="rounded-xl border border-amber-700/50 bg-amber-950/30 p-4 text-sm text-amber-100">
          These CSV datasets contain fabricated test prices, not genuine market history. Do not use them for signals, backtesting conclusions, or investment decisions.
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex flex-wrap items-end gap-4">
            <label className="grid gap-2 text-sm text-slate-300">Currency pair
              <select value={instrument} onChange={(event) => setInstrument(event.target.value as Instrument)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
                {instruments.map((item) => <option key={item.symbol} value={item.symbol}>{item.display_name}</option>)}
              </select>
            </label>
            <label className="grid gap-2 text-sm text-slate-300">Timeframe
              <select value={timeframe} onChange={(event) => setTimeframe(event.target.value as Timeframe)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
                {timeframes.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <button type="button" onClick={() => setReload((value) => value + 1)} className="rounded-lg border border-slate-600 px-4 py-2 text-sm hover:bg-slate-800">Refresh data</button>
          </div>
          {catalogueError && <p className="mt-3 text-sm text-amber-300" role="alert">Instrument catalogue unavailable: {catalogueError}. Showing default selections.</p>}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">{instrument} · {timeframe}</h2>
            <span className="text-xs text-slate-400">{dataset ? `${dataset.count} candles · ${dataset.source} · ${dataset.data_kind}` : "Local CSV"}</span>
          </div>
          {loading ? <p role="status" className="py-24 text-center text-slate-400">Loading historical candles…</p> :
            dataError ? <div role="alert" className="rounded-lg border border-rose-900 bg-rose-950/40 p-5 text-rose-200">{dataError}</div> :
            dataset?.candles.length ? <CandlestickChart key={`${instrument}-${timeframe}`} candles={dataset.candles} symbol={instrument} /> :
            <p role="status" className="py-24 text-center text-slate-400">No candles available.</p>}
        </section>
        {/* Multi-timeframe strategy analysis */}
        <StrategyResearchPanel instrument={instrument} />
        <div className="grid gap-4 md:grid-cols-2">
          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="font-semibold">Research agents</h2>
            <p className="mt-2 text-sm text-slate-400">Market, macro, strategy and risk analysis will be added after verified historical market data is integrated.</p>
            <span className="mt-4 inline-block rounded-md bg-slate-800 px-3 py-1 text-xs text-slate-300">Not enabled</span>
          </section>
          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="font-semibold">Research history</h2>
            <p className="mt-2 text-sm text-slate-400">No research sessions yet. Session persistence will arrive in a later milestone.</p>
          </section>
        </div>
      </div>
    </main>
  );
}
