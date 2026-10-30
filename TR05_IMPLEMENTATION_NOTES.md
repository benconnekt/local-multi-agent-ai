# TR-05-ALL implementation status

This patch is **FE-01 foundation only**, not the complete TR-05-ALL research engine.

## Implemented
- Shared studio navigation in the root Next.js layout (Engineering, Forex, Strategy Lab, Audio to Video).
- `/trading/lab` six-workstream research landing page, clearly labelled implementation pending.
- `/audio-video` coming-soon workspace with no pretend generation functionality.
- Existing Engineering and Forex pages, API routes, OANDA monitor and trading safety gates untouched.

## Still required
- TR-05.1 audit of historical data and immutable baseline/versioning.
- TR-05.2 deterministic evidence and agent evaluation.
- TR-05.3 versioned experiments and immutable records.
- TR-05.4 cost-sensitive walk-forward testing on genuinely unseen data.
- TR-05.5 controlled offline learning/evaluation.
- TR-05.6 forward paper validation over future market observations.
- Full frontend consolidation, including engineering sidebar integration and responsive QA.

## Apply
From the repository root, back up or commit your changes first, then:

```sh
unzip -o ~/Downloads/TR05-FE01-studio-navigation.zip -d .
cd apps/web
npm run typecheck
npm run build
npm run dev
```

Adapt the ZIP path to where you saved it. Do not extract the original source archive back over your repository.

## Safety
- This patch contains no .env, secrets, OANDA credentials or datasets.
- No broker-changing endpoints or strategy execution are added.
- Existing strategy results remain uncertified and research-only.
