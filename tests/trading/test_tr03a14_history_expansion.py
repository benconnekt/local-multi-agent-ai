from datetime import datetime, timezone
import json
import pytest
from app.trading.data.oanda_history_expansion import windows, parse, persist, expand

UTC=timezone.utc

def test_windows_bounded_and_contiguous():
    start=datetime(2025,1,1,tzinfo=UTC);end=datetime(2025,3,1,tzinfo=UTC)
    for tf in ('M15','H1'):
        parts=list(windows(start,end,tf))
        assert parts[0][0]==start and parts[-1][1]==end
        assert all(a<b for a,b in parts)
        assert all(x[1]==y[0] for x,y in zip(parts,parts[1:]))

def test_parse_complete_and_exclusive_end():
    payload={'instrument':'EUR_USD','granularity':'M15','candles':[
        {'time':'2025-01-01T00:00:00Z','complete':True,'mid':{'o':'1','h':'2','l':'0.5','c':'1.5'},'volume':2},
        {'time':'2025-01-01T00:15:00Z','complete':True,'mid':{'o':'1','h':'2','l':'0.5','c':'1.5'},'volume':2}]}
    rows=parse(payload,'EURUSD','M15',datetime(2025,1,1,tzinfo=UTC),datetime(2025,1,1,0,15,tzinfo=UTC))
    assert len(rows)==1

def test_persist_idempotent_and_conflict_fail_closed(tmp_path):
    row={'timestamp':'2025-01-01T00:00:00+00:00','open':'1','high':'2','low':'0.5','close':'1.5','volume':'2'}
    assert persist([row],'EURUSD','M15',tmp_path)['status']=='created'
    assert persist([row],'EURUSD','M15',tmp_path)['status']=='existing_verified'
    with pytest.raises(FileExistsError):persist([{**row,'close':'1.6'}],'EURUSD','M15',tmp_path)
    meta=json.loads(next(tmp_path.glob('*.json')).read_text())
    assert meta['provider']=='oanda_v20' and meta['strategy_eligible'] is False

def test_dry_run_never_fetches(tmp_path):
    def forbidden(*args):raise AssertionError('Network called')
    result=expand('USDJPY','H1','2025-01-01T00:00:00Z','2025-01-05T00:00:00Z',tmp_path,dry_run=True,fetcher=forbidden)
    assert result['decision']=='NO_TRADE' and all(x['status']=='planned' for x in result['segments'])
    assert not list(tmp_path.iterdir())

def test_no_token_fail_closed(tmp_path):
    with pytest.raises(ValueError,match='OANDA_API_TOKEN'):
        expand('GBPUSD','M15','2025-01-01T00:00:00Z','2025-01-02T00:00:00Z',tmp_path)
