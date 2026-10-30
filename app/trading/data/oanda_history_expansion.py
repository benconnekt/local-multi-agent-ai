"""Read-only, bounded OANDA practice historical expansion. No order endpoints."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOST = 'https://api-fxpractice.oanda.com'
PAIRS = {'EURUSD':'EUR_USD','GBPUSD':'GBP_USD','USDJPY':'USD_JPY'}
STEPS = {'H1':timedelta(hours=1),'M15':timedelta(minutes=15)}
FIELDS = ('timestamp','open','high','low','close','volume')


def utc(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None: raise ValueError('Timezone-aware UTC bounds required')
    return dt.astimezone(timezone.utc)


def windows(start, end, granularity):
    start, end = utc(start), utc(end)
    if granularity not in STEPS or start >= end: raise ValueError('Invalid window')
    # M15: 14d <= 1344 bars; H1: 60d <= 1440 bars; below 5000 API limit.
    span = timedelta(days=14 if granularity == 'M15' else 60)
    cursor = start
    while cursor < end:
        following = min(cursor + span, end)
        yield cursor, following
        cursor = following


def parse(payload, pair, granularity, start, end):
    if payload.get('instrument') != PAIRS[pair] or payload.get('granularity') != granularity:
        raise ValueError('Provider instrument/timeframe mismatch')
    result = []
    for candle in payload.get('candles', []):
        if candle.get('complete') is not True: continue
        ts = utc(candle['time'])
        if not (start <= ts < end): continue
        mid = candle.get('mid')
        if not isinstance(mid, dict): raise ValueError('Missing midpoint OHLC')
        vals = [float(mid[k]) for k in ('o','h','l','c')]
        op, hi, lo, cl = vals
        if not all(math.isfinite(x) and x > 0 for x in vals) or not (lo <= min(op,cl) <= max(op,cl) <= hi):
            raise ValueError('Invalid candle OHLC')
        result.append(dict(zip(FIELDS,(ts.isoformat(),mid['o'],mid['h'],mid['l'],mid['c'],str(candle['volume'])))))
    if any(a['timestamp'] >= b['timestamp'] for a,b in zip(result,result[1:])):
        raise ValueError('Non-monotonic or duplicate candles')
    return result


def fetch(token, pair, granularity, start, end, *, opener=None):
    if pair not in PAIRS or granularity not in STEPS: raise ValueError('Unsupported pair/timeframe')
    start, end = utc(start), utc(end)
    if end <= start or end-start > timedelta(days=60): raise ValueError('Unbounded fetch window')
    query = urllib.parse.urlencode({'from':start.isoformat().replace('+00:00','Z'),
        'to':end.isoformat().replace('+00:00','Z'),'granularity':granularity,
        'price':'M','smooth':'false','includeFirst':'true'})
    url = f'{HOST}/v3/instruments/{PAIRS[pair]}/candles?{query}'
    req = urllib.request.Request(url, headers={'Authorization':f'Bearer {token}', 'Accept':'application/json'})
    try:
        with (opener or urllib.request.urlopen)(req,timeout=30) as response:
            payload=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'OANDA practice candle request failed: HTTP {exc.code}') from None
    return parse(payload,pair,granularity,start,end)


def encode(rows):
    buf=io.StringIO(newline='')
    writer=csv.DictWriter(buf,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return buf.getvalue().encode('utf-8')


def persist(rows, pair, granularity, directory, *, retrieved_at=None):
    if not rows: return None
    if pair not in PAIRS or granularity not in STEPS: raise ValueError('Unsupported pair/timeframe')
    first,last=rows[0]['timestamp'],rows[-1]['timestamp']
    stem=f'{pair}_{granularity}_{first[:10]}_{last[:10]}'
    csv_path=directory/f'{stem}.csv'; meta_path=directory/f'{stem}.json'
    raw=encode(rows); sha=hashlib.sha256(raw).hexdigest()
    if csv_path.exists() or meta_path.exists():
        if not csv_path.exists() or not meta_path.exists(): raise FileExistsError(f'Partial existing dataset {stem}')
        existing=json.loads(meta_path.read_text())
        if csv_path.read_bytes()!=raw or existing.get('csv_sha256')!=sha:
            raise FileExistsError(f'Conflicting existing dataset {stem}; refusing overwrite')
        return {'status':'existing_verified','stem':stem,'count':len(rows),'sha256':sha}
    directory.mkdir(parents=True,exist_ok=True)
    metadata={'provider':'oanda_v20','data_kind':'historical_real','environment':'practice',
        'api_host':HOST,'instrument':pair,'symbol':pair,'timeframe':granularity,
        'price_component':'mid','smoothed':False,'strategy_eligible':False,
        'quality_status':'imported_uncertified','count':len(rows),
        'first_timestamp':first,'last_timestamp':last,'csv_sha256':sha,
        'retrieved_at_utc':(retrieved_at or datetime.now(timezone.utc)).isoformat()}
    # Write metadata last; incomplete writes fail closed during catalogue discovery.
    with csv_path.open('xb') as file: file.write(raw)
    with meta_path.open('x',encoding='utf-8') as file: json.dump(metadata,file,indent=2);file.write('\n')
    return {'status':'created','stem':stem,'count':len(rows),'sha256':sha}


def expand(pair,granularity,start,end,directory,*,token=None,dry_run=False,fetcher=fetch):
    if pair not in PAIRS or granularity not in STEPS: raise ValueError('Unsupported pair/timeframe')
    start,end=utc(start),utc(end)
    if end > datetime.now(timezone.utc): raise ValueError('End date must not be in future')
    segments=list(windows(start,end,granularity))
    if not dry_run and not token: raise ValueError('OANDA_API_TOKEN required')
    records=[]
    for a,b in segments:
        if dry_run:
            records.append({'status':'planned','from_utc':a.isoformat(),'to_utc':b.isoformat()})
            continue
        rows=fetcher(token,pair,granularity,a,b)
        item=persist(rows,pair,granularity,directory)
        records.append({'from_utc':a.isoformat(),'to_utc':b.isoformat(),**(item or {'status':'no_complete_candles','count':0})})
    return {'decision':'NO_TRADE','research_only':True,'quality_certified':False,
        'research_signal_eligible':False,'independently_certified':False,
        'instrument':pair,'provider':'oanda_v20','timeframe':granularity,
        'from_utc':start.isoformat(),'to_utc':end.isoformat(),
        'dry_run':dry_run,'segments':records,
        'warning':'Historical import only; not independent data certification or trading permission'}


def main():
    p=argparse.ArgumentParser(description='OANDA practice read-only historical candle expansion')
    p.add_argument('--from-utc',required=True,help='UTC ISO date/time, e.g. 2025-10-01T00:00:00Z')
    p.add_argument('--to-utc',required=True,help='Exclusive UTC end, e.g. 2026-10-01T00:00:00Z')
    p.add_argument('--directory',type=Path,default=Path('data/forex/historical_oanda'))
    p.add_argument('--pairs',nargs='+',choices=PAIRS,default=list(PAIRS))
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    token=os.environ.get('OANDA_API_TOKEN')
    for pair in args.pairs:
        for tf in STEPS:
            result=expand(pair,tf,args.from_utc,args.to_utc,args.directory,token=token,dry_run=args.dry_run)
            counts={s:sum(x['status']==s for x in result['segments']) for s in ('created','existing_verified','planned','no_complete_candles')}
            print(pair,tf,counts,'NO_TRADE')
    print('Finished. Import remains UNCERTIFIED. Do not enable strategy signals.')

if __name__=='__main__':main()
