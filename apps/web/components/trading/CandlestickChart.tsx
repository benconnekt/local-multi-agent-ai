"use client";

import { useMemo, useState } from "react";
import type { Candle } from "@/lib/trading-api";

type Props = { candles: Candle[]; symbol: string };
const WIDTH = 960;
const HEIGHT = 380;
const LEFT = 72;
const RIGHT = 20;
const TOP = 22;
const BOTTOM = 44;

export default function CandlestickChart({ candles, symbol }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const visible = useMemo(() => candles.slice(-120), [candles]);
  const plotted = useMemo(() => {
    if (!visible.length) return null;
    const low = Math.min(...visible.map((c) => c.low));
    const high = Math.max(...visible.map((c) => c.high));
    const padding = Math.max((high - low) * 0.08, high * 0.00001);
    const min = low - padding;
    const max = high + padding;
    const chartWidth = WIDTH - LEFT - RIGHT;
    const chartHeight = HEIGHT - TOP - BOTTOM;
    const y = (price: number) => TOP + ((max - price) / (max - min)) * chartHeight;
    const slot = chartWidth / visible.length;
    return { min, max, y, slot, chartWidth, chartHeight };
  }, [visible]);

  if (!plotted) return <p role="status" className="text-sm text-slate-400">No candles to display.</p>;

  const decimals = symbol.endsWith("JPY") ? 3 : 5;
  const activeIndex = selected !== null && selected < visible.length ? selected : visible.length - 1;
  const active = visible[activeIndex];
  const fmt = (n: number) => n.toFixed(decimals);
  const { min, max, y, slot, chartHeight } = plotted;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-300" aria-live="polite">
        <span>{new Date(active.timestamp).toLocaleString("en-GB", { timeZone: "UTC" })} UTC</span>
        <span>O <b className="text-white">{fmt(active.open)}</b></span>
        <span>H <b className="text-white">{fmt(active.high)}</b></span>
        <span>L <b className="text-white">{fmt(active.low)}</b></span>
        <span>C <b className="text-white">{fmt(active.close)}</b></span>
        <span>Volume <b className="text-white">{active.volume ?? "N/A"}</b></span>
      </div>
      <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-950 p-2">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="min-w-[620px] w-full" role="img" aria-label={`${symbol} candlestick chart showing ${visible.length} synthetic candles`}>
          {Array.from({ length: 5 }, (_, i) => {
            const price = max - ((max - min) * i) / 4;
            const py = y(price);
            return (
              <g key={i}>
                <line x1={LEFT} x2={WIDTH - RIGHT} y1={py} y2={py} stroke="#334155" strokeDasharray="4 5" />
                <text x={LEFT - 8} y={py + 4} textAnchor="end" fontSize="12" fill="#94a3b8">{fmt(price)}</text>
              </g>
            );
          })}
          {visible.map((c, i) => {
            const cx = LEFT + slot * (i + 0.5);
            const rising = c.close >= c.open;
            const color = rising ? "#34d399" : "#fb7185";
            const bodyTop = Math.min(y(c.open), y(c.close));
            const bodyHeight = Math.max(1.5, Math.abs(y(c.open) - y(c.close)));
            const bodyWidth = Math.max(2, Math.min(slot * 0.64, 14));
            return (
              <g key={`${c.timestamp}-${i}`} onMouseEnter={() => setSelected(i)} onFocus={() => setSelected(i)} tabIndex={0} role="button" aria-label={`Candle ${i + 1}: ${c.timestamp}, close ${fmt(c.close)}`}>
                <line x1={cx} x2={cx} y1={y(c.high)} y2={y(c.low)} stroke={color} strokeWidth="1.5" />
                <rect x={cx - bodyWidth / 2} y={bodyTop} width={bodyWidth} height={bodyHeight} fill={color} rx="1" />
                <rect x={cx - slot / 2} y={TOP} width={slot} height={chartHeight} fill="transparent" />
                <title>{`${c.timestamp} | O ${fmt(c.open)} H ${fmt(c.high)} L ${fmt(c.low)} C ${fmt(c.close)}`}</title>
              </g>
            );
          })}
          {[0, Math.floor((visible.length - 1) / 2), visible.length - 1].map((index, i) => {
            const c = visible[index];
            return <text key={i} x={LEFT + slot * (index + 0.5)} y={HEIGHT - 15} textAnchor="middle" fontSize="11" fill="#94a3b8">{new Date(c.timestamp).toISOString().slice(0, 16).replace("T", " ")}</text>;
          })}
        </svg>
      </div>
      <p className="text-xs text-slate-400">Showing the latest {visible.length} of {candles.length} candles. Hover or focus a candle to inspect its values. All timestamps are UTC.</p>
    </div>
  );
}
