"""Run from repository root: uv run python generate_robustness_reports.py"""
import json
from pathlib import Path
from app.trading.research.robustness import analyse_ledger

SOURCE = Path('reports/trading')
DEST = SOURCE / 'robustness'
DEST.mkdir(parents=True, exist_ok=True)
for pair in ('eurusd', 'gbpusd', 'usdjpy'):
    source = SOURCE / f'{pair}_trade_ledger.json'
    export = json.loads(source.read_text(encoding='utf-8'))
    report = analyse_ledger(export)
    path = DEST / f'{pair}_robustness.json'
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(pair.upper(), 'holdout:', report['split']['holdout'],
          'sample_sufficient:', report['sample_sufficient'],
          'validation_pass:', report['validation_pass'], 'file:', path)
