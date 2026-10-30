"""Read-only OANDA v20 candle probe. Does not modify dataset or place orders."""
import json
import os
import urllib.request
import urllib.error

TOKEN = os.environ.get('OANDA_API_TOKEN') or os.environ.get('OANDA_ACCESS_TOKEN')
ENV = os.environ.get('OANDA_ENVIRONMENT', 'practice').lower()
if ENV != 'practice':
    raise SystemExit('Safety stop: this diagnostic only permits OANDA_ENVIRONMENT=practice')
if not TOKEN:
    raise SystemExit('Set OANDA_API_TOKEN or OANDA_ACCESS_TOKEN in your shell; do not paste it into chat.')
url = ('https://api-fxpractice.oanda.com/v3/instruments/GBP_USD/candles'
       '?price=M&granularity=M15&from=2025-12-21T22%3A00%3A00Z'
       '&to=2025-12-21T23%3A00%3A00Z&includeFirst=true')
request = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
except urllib.error.HTTPError as exc:
    raise SystemExit(f'OANDA HTTP {exc.code}: {exc.read(500).decode(errors="replace")}') from exc
for candle in data.get('candles', []):
    print(json.dumps({'time': candle.get('time'), 'complete': candle.get('complete'), 'mid': candle.get('mid'), 'volume': candle.get('volume')}, sort_keys=True))
print('Read-only probe complete. No imported files changed.')
