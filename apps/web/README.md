# Local Agent Studio — Frontend Foundation

A Next.js + TypeScript frontend for the local LangGraph agent platform.

## What works

- Responsive dark dashboard with Engineering and Forex Research workspaces
- Workspace-specific agent directory and search
- Task draft composer, in-session task list and deletion
- Approvals, settings and activity placeholders that clearly identify missing backend services
- Forex research workspace isolated from engineering; no live trading

**Important:** All agent information is static role configuration. Tasks are in-memory drafts, cleared on refresh. There is no backend connection, real execution, persisted storage, market feed, trading advice, or broker integration. The UI deliberately does not simulate passed QA checks.

## Install in existing repository

From the repository root, copy this folder to `apps/web` (preserving its contents). The Python backend remains unchanged.

```bash
mkdir -p apps/web
cp -R /path/to/local-agent-studio-frontend/. apps/web/
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:3000

## Checks

```bash
npm run typecheck
npm run lint
npm run build
```

## Suggested next integration

1. Define a typed backend contract for agents, tasks, approvals and immutable event IDs.
2. Add an authenticated local API gateway and SSE/WebSocket event feed.
3. Connect task submission only after explicit execution permissions and workspace isolation are enforced.
4. Bind QA status to trusted evidence and source hashes; never trust LLM-reported pass strings.
5. Keep Forex research/paper trading separate, with explicit opt-in before any broker integration.

## Security considerations

This is a frontend foundation, not a production-secure deployment. Do not expose it publicly without authentication, authorisation, CSRF protections where applicable, rate limiting, audit controls and a hardened API boundary. Local binding to 127.0.0.1 does not by itself secure a privileged backend.
