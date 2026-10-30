
"use client";

import { useEffect, useState } from "react";
import type { Instrument } from "@/lib/trading-api";
import OpportunityScorecard, {
  type OpportunityScore,
} from "./OpportunityScorecard";

type Decision = "BUY" | "SELL" | "NO_TRADE";
type Timeframe = "H4" | "H1" | "M15";

type DatasetInfo = {
  id?: string;
  timeframe?: string;
  source?: string;
  quality_status: string;
  count: number;
  last_timestamp?: string;
};

type Report = {
  instrument: string;
  decision: Decision;
  reason: string;
  research_only: boolean;
  quality_certified: boolean;
  missing_timeframes: string[];
  datasets: Record<string, DatasetInfo>;
  entry: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  risk_fraction: number;
  reward_to_risk: number | null;
  indicators: Record<string, number> | null;
  as_of_utc?: string | null;
  opportunity_score?: OpportunityScore | null;
};

const BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

const TIMEFRAMES: Timeframe[] = ["H4", "H1", "M15"];

function getDatasets(
  report: Report,
  timeframe: Timeframe
): DatasetInfo[] {
  return Object.entries(report.datasets ?? {})
    .filter(([key, dataset]) => {
      return dataset.timeframe === timeframe || key === timeframe;
    })
    .map(([key, dataset]) => ({
      ...dataset,
      id: dataset.id ?? key,
    }));
}

function DatasetStatus({
  timeframe,
  report,
}: {
  timeframe: Timeframe;
  report: Report;
}) {
  const datasets = getDatasets(report, timeframe);
  const isMissing = report.missing_timeframes.includes(timeframe);

  if (timeframe === "H4" && datasets.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
        <p className="font-medium text-slate-200">H4</p>
        <p className="mt-1 text-xs text-slate-400">
          Derived from H1
        </p>
        <p className="mt-1 text-xs text-amber-300">
          {report.quality_certified
            ? "Check derived-candle provenance"
            : "Not certified"}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
      <p className="font-medium text-slate-200">{timeframe}</p>

      {datasets.length > 0 ? (
        <div className="mt-2 space-y-2">
          {datasets.map((dataset) => (
            <div key={dataset.id}>
              <p className="text-xs text-slate-300">
                {dataset.count} candles
              </p>
              <p className="mt-1 break-words text-xs text-slate-400">
                {dataset.quality_status}
              </p>
              {dataset.source && (
                <p className="mt-1 text-xs text-slate-500">
                  Source: {dataset.source}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-xs text-amber-300">
          {isMissing ? "Missing historical data" : "Unavailable"}
        </p>
      )}
    </div>
  );
}

export default function StrategyResearchPanel({
  instrument,
}: {
  instrument: Instrument;
}) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    setReport(null);
    setError("");
    setLoading(true);

    async function loadReport() {
      try {
        const response = await fetch(
          `${BASE}/trading/strategy/analyse?instrument=${encodeURIComponent(instrument)}`,
          {
            signal: controller.signal,
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Strategy API returned HTTP ${response.status}`
          );
        }

        const data = (await response.json()) as Report;

        if (!controller.signal.aborted) {
          setReport(data);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load strategy research"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadReport();

    return () => controller.abort();
  }, [instrument]);

  return (
    <section
      className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
      aria-label="Strategy research"
      aria-busy={loading}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold text-slate-100">
          Multi-timeframe strategy research · {instrument}
        </h2>

        <span className="rounded-md border border-amber-700 px-3 py-1 text-sm text-amber-200">
          {loading
            ? "Checking…"
            : error
              ? "Unavailable"
              : report?.decision ?? "Unavailable"}
        </span>
      </div>

      <p className="mt-2 text-sm text-slate-400">
        H4 trend · H1 pullback · M15 confirmation
        {" · "}
        Research only, no orders
      </p>

      {loading && (
        <div role="status" className="mt-5 animate-pulse space-y-3">
          <div className="h-4 w-3/4 rounded bg-slate-800" />
          <div className="h-20 rounded bg-slate-800" />
          <span className="sr-only">
            Loading strategy research
          </span>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-4 text-sm text-rose-300">
          {error}
        </p>
      )}

      {report && !loading && (
        <div className="mt-5 space-y-5">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Strategy assessment
            </h3>

            <p className="mt-2 text-sm text-amber-100">
              {report.reason}
            </p>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-slate-200">
              Historical data readiness
            </h3>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {TIMEFRAMES.map((timeframe) => (
                <DatasetStatus
                  key={timeframe}
                  timeframe={timeframe}
                  report={report}
                />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-700 p-3">
            <p className="text-sm text-slate-300">
              Data quality:{" "}
              <strong
                className={
                  report.quality_certified
                    ? "text-emerald-300"
                    : "text-amber-300"
                }
              >
                {report.quality_certified
                  ? "Certified"
                  : "Not certified"}
              </strong>
            </p>

            <p className="mt-2 text-xs text-slate-400">
              No entry, stop-loss or take-profit is authorised
              until the historical data, strategy and risk
              gates have all passed.
            </p>
          </div>

          <div className="border-t border-slate-800 pt-5">
            <h3 className="mb-3 text-sm font-semibold text-slate-200">
              Trade opportunity scoring
            </h3>

            {report.opportunity_score ? (
              <OpportunityScorecard
                score={report.opportunity_score}
              />
            ) : (
              <div
                className="rounded-lg border border-slate-700 bg-slate-800/40 p-4"
                role="status"
              >
                <p className="font-medium text-amber-200">
                  UNRATED
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  Opportunity scoring is not available from
                  the API yet. No score or confidence rating
                  has been inferred.
                </p>
              </div>
            )}
          </div>

          <p className="text-xs text-slate-500">
            Opportunity ratings are heuristic research
            assessments, not probabilities of success or
            trading recommendations.
          </p>
        </div>
      )}
    </section>
  );
}
