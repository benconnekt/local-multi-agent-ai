"use client";

export type OpportunityScore = {
  score: number | null;
  rating: "A" | "B" | "C" | "D" | "UNRATED";
  complete: boolean;
  eligible: boolean;
  decision: "BUY" | "SELL" | "NO_TRADE";
  reasons: string[];
  factors: Array<{
    name: string;
    weight: number;
    points: number | null;
    available: boolean;
    explanation: string;
    source: string | null;
  }>;
  scoring_version: string;
  probability_calibrated: boolean;
  research_only: boolean;
};

const LABELS: Record<string, string> = {
  market_structure: "Market structure & trend",
  price_action: "Price action & entry",
  timeframe_alignment: "Multi-timeframe alignment",
  momentum_volatility: "Momentum & volatility",
  macro_sentiment: "Macro news & sentiment",
};

export default function OpportunityScorecard({ score }: { score: OpportunityScore | null | undefined }) {
  if (!score) return (
    <section className="mt-4 rounded-xl border border-slate-700 p-4" aria-label="Opportunity score">
      <h3 className="font-semibold">Opportunity scoring</h3>
      <p className="mt-2 text-sm text-slate-400">Scoring evidence has not been connected to this report.</p>
    </section>
  );
  return (
    <section className="mt-4 rounded-xl border border-slate-700 p-4" aria-label="Opportunity score">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold">Opportunity scoring</h3>
        <strong className="text-lg">{score.score === null ? "UNRATED" : `${score.score.toFixed(2)} / 100 · ${score.rating}`}</strong>
      </div>
      <p className="mt-1 text-xs text-slate-400">Heuristic research rating, not a calibrated probability or trade recommendation.</p>
      <dl className="mt-4 space-y-3">
        {score.factors.map(factor => (
          <div key={factor.name} className="rounded-lg border border-slate-800 p-3">
            <div className="flex justify-between gap-3 text-sm">
              <dt>{LABELS[factor.name] ?? factor.name}</dt>
              <dd>{factor.points === null ? "Unavailable" : `${factor.points.toFixed(2)} / ${factor.weight}`}</dd>
            </div>
            {factor.points !== null && (
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-label={LABELS[factor.name] ?? factor.name} aria-valuenow={factor.points} aria-valuemin={0} aria-valuemax={factor.weight}>
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(factor.points / factor.weight) * 100}%` }} />
              </div>
            )}
            <p className="mt-2 text-xs text-slate-400">{factor.explanation}</p>
            {factor.source && <p className="mt-1 break-all text-xs text-slate-500">Source: {factor.source}</p>}
          </div>
        ))}
      </dl>
      {score.reasons.length > 0 && (
        <div className="mt-4 text-sm text-amber-200">
          <p className="font-medium">Restrictions</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">{score.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
        </div>
      )}
      <p className="mt-3 text-xs text-slate-400">Scoring eligibility: {score.eligible ? "Eligible for strategy review" : "Not eligible"}. Final decision: {score.decision}. Research only.</p>
    </section>
  );
}
