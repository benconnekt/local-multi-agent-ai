"""Read-only Dukascopy hourly tick archive importer (bid OHLC, UTC)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
import lzma
import math
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RECORD = struct.Struct('>IIIff')
SCALES = {'EURUSD': 100_000, 'GBPUSD': 100_000, 'USDJPY': 1_000}
BASE_URL = 'https://datafeed.dukascopy.com/datafeed'

class ImportErrorData(ValueError):
    pass

@dataclass(frozen=True)
class Tick:
    timestamp: datetime
    bid: float
    bid_volume: float


def decode_bi5(data: bytes, hour: datetime, symbol: str) -> list[Tick]:
    if hour.tzinfo is None or hour.utcoffset() != timedelta(0) or hour.minute or hour.second or hour.microsecond:
        raise ImportErrorData('Hour must be aligned to UTC')
    if symbol not in SCALES:
        raise ImportErrorData(f'Unsupported instrument: {symbol}')
    try:
        raw = lzma.decompress(data)
    except lzma.LZMAError as exc:
        raise ImportErrorData('Invalid BI5 compression') from exc
    if len(raw) % RECORD.size:
        raise ImportErrorData('Truncated BI5 tick record')
    ticks: list[Tick] = []
    previous = -1
    for millis, ask_int, bid_int, ask_volume, bid_volume in RECORD.iter_unpack(raw):
        if millis >= 3_600_000 or millis < previous:
            raise ImportErrorData('Out-of-order or out-of-hour tick')
        if bid_int <= 0 or ask_int < bid_int or not all(map(math.isfinite, (ask_volume, bid_volume))) or min(ask_volume, bid_volume) < 0:
            raise ImportErrorData('Invalid tick price or volume')
        previous = millis
        ticks.append(Tick(hour + timedelta(milliseconds=millis), bid_int / SCALES[symbol], float(bid_volume)))
    return ticks


def fetch_hour(symbol: str, hour: datetime, timeout: float = 15) -> bytes | None:
    if symbol not in SCALES:
        raise ImportErrorData('Unsupported instrument')
    if hour.tzinfo is None or hour.utcoffset() != timedelta(0) or (hour.minute, hour.second, hour.microsecond) != (0, 0, 0):
        raise ImportErrorData('Expected UTC-aligned hour')
    url = f'{BASE_URL}/{symbol}/{hour.year}/{hour.month - 1:02d}/{hour.day:02d}/{hour.hour:02d}h_ticks.bi5'
    try:
        with urlopen(Request(url, headers={'User-Agent': 'LocalAgentStudio-Research/1.0'}), timeout=timeout) as response:
            data = response.read(12_000_001)
            if len(data) > 12_000_000:
                raise ImportErrorData('Hourly archive exceeds size limit')
            return data
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise ImportErrorData(f'Provider HTTP {exc.code}') from exc
    except (URLError, TimeoutError) as exc:
        raise ImportErrorData(f'Provider connection failed: {exc}') from exc


def aggregate(ticks: list[Tick], minutes: int) -> list[dict]:
    if minutes not in (15, 60):
        raise ImportErrorData('Supported timeframes: M15, H1')
    buckets: dict[datetime, list[Tick]] = {}
    for tick in ticks:
        ts = tick.timestamp.astimezone(timezone.utc)
        start = ts.replace(minute=(ts.minute // minutes) * minutes if minutes == 15 else 0, second=0, microsecond=0)
        buckets.setdefault(start, []).append(tick)
    candles = []
    for start, group in sorted(buckets.items()):
        group.sort(key=lambda item: item.timestamp)
        prices = [item.bid for item in group]
        candles.append({'timestamp': start.isoformat().replace('+00:00', 'Z'), 'open': prices[0], 'high': max(prices), 'low': min(prices), 'close': prices[-1], 'volume': round(sum(item.bid_volume for item in group), 6)})
    return candles
