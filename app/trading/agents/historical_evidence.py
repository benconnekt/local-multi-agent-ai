"""Checksum-validated, UNCERTIFIED historical observations for qualitative research only."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean
from app.trading.data.catalogue import discover

DATA_ROOT = Path(__file__).resolve().parents[3] / 'data' / 'forex'
PAIRS = {'EURUSD', 'GBPUSD', 'USDJPY'}


def build_historical_evidence(instrument: str, *, directory: Path | None = None) -> dict:
    if instrument not in PAIRS:
        raise ValueError('Unsupported instrument')
    # discover() checks metadata, checksum, candle schema, timestamps and ordering.
    datasets = [d for d in discover(directory or DATA_ROOT)
                if d['instrument'] == instrument and d['source'] == 'oanda_v20'
                and d['timeframe'] == 'H1' and d['data_kind'] == 'historical_real']
    if not datasets:
        raise ValueError('No checksum-validated OANDA H1 historical dataset available')
    datasets.sort(key=lambda d: (d['last_timestamp'], d['id']))
    # Use one source dataset to avoid overlapping candles / accidental stitching.
    dataset = datasets[-1]
    candles = dataset['candles']
    if len(candles) < 30:
        raise ValueError('Insufficient historical H1 candles (minimum 30)')
    rows = candles[-60:]
    closes = [float(c.close) for c in rows]
    highs = [float(c.high) for c in rows]
    lows = [float(c.low) for c in rows]
    as_of = dataset['last_timestamp']
    # No forecast, win probability, entry or signal. Pure deterministic observations.
    evidence = {
        'data_kind': 'historical_real', 'not_live': True,
        'validation_scope': 'dataset checksum and candle schema only',
        'quality_certified': False, 'strategy_eligible': False,
        'instrument': instrument, 'timeframe': 'H1', 'observations': len(rows),
        'first_observation_utc': rows[0].timestamp.isoformat(),
        'last_observation_utc': rows[-1].timestamp.isoformat(),
        'last_close': round(closes[-1], 6),
        'first_close': round(closes[0], 6),
        'observed_close_change': round(closes[-1] - closes[0], 6),
        'observed_high': round(max(highs), 6),
        'observed_low': round(min(lows), 6),
        'sma_20_observed': round(mean(closes[-20:]), 6),
        'sma_30_observed': round(mean(closes[-30:]), 6),
        'last_close_minus_sma_20': round(closes[-1] - mean(closes[-20:]), 6),
        'sma_20_minus_sma_30': round(mean(closes[-20:]) - mean(closes[-30:]), 6),
        'indicator_coverage': {'sma_20_observed': 20, 'sma_30_observed': 30},
        'missing_indicators': ['RSI', 'MACD', 'ATR'],
        'interpretation_warning': 'Observed indicators only; no forecast or trading signal',
    }
    provenance = {
        'dataset_id': dataset['id'], 'provider': dataset['source'],
        'timeframe': 'H1', 'dataset_last_timestamp_utc': as_of,
        'quality_status': dataset['quality_status'],
        'historical_only': True, 'checksum_validated': True,
        'quality_certified': False, 'strategy_eligible': False,
    }
    return {'verified_context': {'price_action': evidence, 'technical': evidence}, 'provenance': provenance}
