# TR-03A.8 compatibility fix

Repairs three regressions seen in the existing test suite:
- Legacy Yahoo catalogue tests use an isolated temporary directory, not a folder named `historical_real`. Yahoo datasets are now accepted from any directory except `historical_oanda`, while metadata and SHA-256 checks remain intact.
- The API accepts older minimal catalogue entries that omit `first_timestamp`, using `None` rather than raising `KeyError`.

Only two files are changed. OANDA provenance validation and research-only NO_TRADE policy remain unchanged.

From repository root after committing changes:

```sh
unzip -o ~/Downloads/TR-03A8-compatibility-fix.zip -d .
uv run pytest tests/trading/test_dataset_catalogue.py tests/trading/test_strategy_route.py tests/trading/test_tr03a8_integration.py -v
uv run pytest -q
```
