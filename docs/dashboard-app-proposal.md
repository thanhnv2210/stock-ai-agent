# Proposal: Stock AI Dashboard

**Date**: 2026-06-02
**Status**: Proposed
**Author**: Claude Code

---

## 1. Overview

A local web application to visualise and verify the analysis data produced by the `stock-ai-agent` daily pipeline. Reads directly from the existing `tradingdb` PostgreSQL database (`stock_ai` schema) — no changes to the pipeline are needed.

---

## 2. Template Selection

**Template B — Next.js Full-Stack**

| Criterion | Rationale |
|---|---|
| No separate AI service | Data display only — no Claude API calls needed |
| Needs DB access | Reads directly from existing `tradingdb` via Drizzle ORM |
| Consistent with workspace | Matches `career-growth-copilot`, `algo-coach-ai`, `communication-ai-assistant` |
| Server Components | Next.js App Router lets DB queries run server-side — no extra API hops for read-only views |

Template C (multi-process) is not needed since there is no Python AI service.

---

## 3. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js 16 + App Router | Consistent with workspace |
| Styling | TailwindCSS v4 + shadcn/ui | New York style, zinc base |
| ORM | Drizzle ORM | Mirror existing `stock_ai` schema as read-only types |
| Database | PostgreSQL — existing `tradingdb:54320` | `stock_ai` schema, read-only |
| Charting | `lightweight-charts` (TradingView) | Purpose-built for OHLCV candlestick + indicator overlays |
| Port | **3006** | Gap between `freelancer-copilot` (3005) and `ai-operations-portal` (3007) |

---

## 4. Application Name & Paths

```
App name  : stock-ai-dashboard
Directory : /Users/ThanhNguyen/AI_WS/stock-ai-dashboard
Port      : 3006
```

---

## 5. Database — Existing Tables (read-only)

All tables live in `tradingdb` under the `stock_ai` schema. Drizzle schema will mirror them as read-only — no migrations run against this DB.

| Table | Used for |
|---|---|
| `stock_ai.signal_history` | Main data source — every signal from every pipeline run |
| `stock_ai.signals` | Latest signal per symbol (current view) |
| `stock_ai.ohlcv_factors` | Price + SMA5/20, RSI14, MACD data for charts |
| `stock_ai.watchlist` | Holdings / potential lists |
| `stock_ai.symbol_groups` | Which symbols were processed per run date |

---

## 6. Pages & Features

### 6.1 Dashboard — `/`

Today's pipeline run at a glance.

- **Summary bar**: total symbols processed, BUY count, SELL count, HOLD count, run date
- **Signal cards** grouped by group name (holdings → potential → nasdaq_top_turnover)
  - Each card: symbol, signal badge (BUY=green / SELL=red / HOLD=grey), price
  - Clicking a symbol navigates to Symbol Detail
- **Run history selector**: dropdown to switch between past run dates (from `signal_history`)

### 6.2 Signal History — `/history`

Full audit trail for verification.

- **Filters**: group name, signal type (BUY/SELL/HOLD), symbol search, date range picker
- **Table columns**: run date, analysis date, symbol, group, signal, price
- **Sort**: default newest first; sortable by any column
- **Export**: CSV download of current filtered view
- Clicking a symbol row navigates to Symbol Detail

### 6.3 Symbol Detail — `/symbol/[ticker]`

Full technical analysis view for one symbol.

- **Header**: ticker, latest signal badge, latest price, group membership
- **Chart panel** (TradingView lightweight-charts):
  - Candlestick chart (OHLC from `ohlcv_factors`)
  - SMA 5 and SMA 20 overlays
  - BUY/SELL signal markers on the candlestick
  - Sub-panel: RSI 14 with overbought (70) / oversold (30) lines
  - Sub-panel: MACD line + signal line + histogram
- **Date range selector**: 1M / 3M / 6M / 1Y / All
- **Signal history table**: all past signals for this symbol (from `signal_history`)

### 6.4 Watchlist — `/watchlist`

View the current holdings and potential lists.

- **Two tabs**: Holdings | Potential
- **Table per tab**: symbol, date added, latest signal, latest price
- **Read-only view** — mutations (add/remove) are done via SQL directly for now

---

## 7. Project Structure

```
stock-ai-dashboard/
├── CLAUDE.md
├── .env
├── .env.example
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout, ThemeProvider, font-size FOUC script
│   │   ├── page.tsx                 # Dashboard
│   │   ├── history/
│   │   │   └── page.tsx             # Signal History
│   │   ├── symbol/
│   │   │   └── [ticker]/
│   │   │       └── page.tsx         # Symbol Detail
│   │   ├── watchlist/
│   │   │   └── page.tsx             # Watchlist
│   │   └── api/
│   │       ├── signals/route.ts     # GET /api/signals?run_date=&group=&signal=
│   │       ├── history/route.ts     # GET /api/history?symbol=&from=&to=&signal=
│   │       ├── symbol/[ticker]/
│   │       │   ├── ohlcv/route.ts   # GET OHLCV + factors for charting
│   │       │   └── signals/route.ts # GET signal history for symbol
│   │       └── watchlist/route.ts   # GET holdings + potential
│   ├── db/
│   │   ├── index.ts                 # Drizzle client (read-only connection to tradingdb)
│   │   └── schema.ts                # Mirror of stock_ai tables as Drizzle types
│   ├── components/
│   │   ├── nav/
│   │   │   ├── sidebar.tsx
│   │   │   └── topbar.tsx
│   │   ├── dashboard/
│   │   │   ├── signal-card.tsx
│   │   │   └── group-section.tsx
│   │   ├── history/
│   │   │   ├── history-table.tsx
│   │   │   └── history-filters.tsx
│   │   ├── symbol/
│   │   │   ├── ohlcv-chart.tsx      # lightweight-charts wrapper
│   │   │   └── signal-history-table.tsx
│   │   └── watchlist/
│   │       └── watchlist-table.tsx
│   ├── services/
│   │   ├── signals.service.ts
│   │   ├── history.service.ts
│   │   ├── ohlcv.service.ts
│   │   └── watchlist.service.ts
│   └── lib/
│       └── utils.ts
```

---

## 8. Environment Config

```bash
# .env
DATABASE_URL=postgresql://admin:admin@localhost:54320/tradingdb
```

No `ANTHROPIC_API_KEY` needed — no AI calls.

---

## 9. Build Order

Follow the runbook's recommended sequence:

1. **Scaffold** — `pnpm create next-app` with App Router + Tailwind + TypeScript
2. **Install deps** — shadcn/ui, Drizzle ORM, lightweight-charts
3. **DB schema** — mirror `stock_ai` tables as read-only Drizzle types (no `db:generate` / `db:migrate` — schema is externally owned)
4. **Services** — one service file per table; all functions are `SELECT` only
5. **API routes** — thin wrappers over services
6. **Layout** — sidebar with nav links, ThemeProvider (dark/light + font-size S/M/L per runbook pattern)
7. **Dashboard page** — signal cards grouped by group name
8. **History page** — filterable table + CSV export
9. **Symbol detail page** — lightweight-charts OHLCV + indicators + signal markers
10. **Watchlist page** — holdings/potential tabs

---

## 10. ADR Decisions

### ADR-001 — Template B (Next.js) over Template C (multi-process)

**Context**: App is purely a data viewer — reads from `tradingdb`, no AI inference needed.
**Decision**: Use Next.js full-stack. Server Components handle DB queries directly, eliminating a Python FastAPI service layer.
**Trade-off**: If AI features are added later (e.g., signal explanation via Claude), an API route can be added to the same Next.js app without restructuring.

### ADR-002 — lightweight-charts over Recharts for financial data

**Context**: Need candlestick charts, indicator sub-panels (RSI, MACD), and signal markers.
**Decision**: Use TradingView's `lightweight-charts` — built specifically for financial time series; handles large datasets efficiently, supports sub-panels and overlay series natively.
**Trade-off**: Requires a React wrapper component (`useEffect` + imperative API) since it is not a React-native library.

### ADR-003 — Read-only Drizzle schema (no migrations)

**Context**: `tradingdb` is owned and managed by the `stock-ai-agent` pipeline. The dashboard must not alter the schema.
**Decision**: Define Drizzle table types to match `stock_ai.*` for type-safe queries, but never run `db:generate` or `db:migrate` from this app.
**Trade-off**: Schema changes in the pipeline must be manually reflected in `src/db/schema.ts`.

---

## 11. zshrc Functions

```zsh
# Stock AI Dashboard
STOCK_DASH_DIR="/Users/ThanhNguyen/AI_WS/stock-ai-dashboard"
STOCK_DASH_PID_FILE="/tmp/stock-ai-dashboard.pid"
STOCK_DASH_PORT=3006

stock-dash-start() {
  echo "Starting Stock AI Dashboard..."
  lsof -ti tcp:$STOCK_DASH_PORT | xargs kill -9 2>/dev/null
  rm -f "$STOCK_DASH_PID_FILE"
  (cd "$STOCK_DASH_DIR" && pnpm dev > /tmp/stock-ai-dashboard.log 2>&1 &)
  echo $! > "$STOCK_DASH_PID_FILE"
  echo "Stock AI Dashboard started — http://localhost:$STOCK_DASH_PORT"
  echo "Logs: tail -f /tmp/stock-ai-dashboard.log"
}

stock-dash-stop() {
  echo "Stopping Stock AI Dashboard..."
  lsof -ti tcp:$STOCK_DASH_PORT | xargs kill -9 2>/dev/null && echo "Stopped." || echo "Not running."
  rm -f "$STOCK_DASH_PID_FILE"
}

stock-dash-restart() { stock-dash-stop && sleep 1 && stock-dash-start; }
stock-dash-logs() { tail -f /tmp/stock-ai-dashboard.log; }

stock-dash-status() {
  if [[ -f "$STOCK_DASH_PID_FILE" ]] && kill -0 "$(cat $STOCK_DASH_PID_FILE)" 2>/dev/null; then
    echo "Stock AI Dashboard is running (PID $(cat $STOCK_DASH_PID_FILE)) — http://localhost:$STOCK_DASH_PORT"
  else
    echo "Stock AI Dashboard is not running."
    rm -f "$STOCK_DASH_PID_FILE"
  fi
}
```

---

## 12. workspace-app-registry.md Entry

```
| 3006 | stock-ai-dashboard | `AI_WS/stock-ai-dashboard` | Next.js 16 + TailwindCSS v4 + Drizzle ORM | `pnpm dev` (alias: `stock-dash-start`) |
```

Favicon concept: candlestick bar chart — 3 bars with wicks (green / red / grey), accent **Emerald `#10b981`**.

---

## 13. CLAUDE.md Template for the New App

```markdown
# CLAUDE.md

## Project Overview
Local dashboard to view and verify stock signal analysis data produced by the stock-ai-agent pipeline.

## Tech Stack
- Framework: Next.js 16 + App Router
- Styling: TailwindCSS v4 + shadcn/ui (New York, zinc)
- ORM: Drizzle ORM (read-only — never run db:generate or db:migrate)
- Database: PostgreSQL — tradingdb on localhost:54320, stock_ai schema
- Charting: lightweight-charts (TradingView)

## Ports
- Frontend: 3006

## Key Conventions
- All DB access is read-only — SELECT queries only, no INSERT/UPDATE/DELETE
- Service functions live in src/services/, one file per domain
- API routes are thin wrappers — no business logic in route.ts files
- Chart components use useEffect + imperative lightweight-charts API

## Do Not
- Run pnpm db:generate or pnpm db:migrate — schema is owned by stock-ai-agent
- Add write endpoints to the DB
- Install the Anthropic SDK unless a specific AI feature is scoped and approved
```

---

## 14. Open Questions

| Question | Default if not answered |
|---|---|
| Should the watchlist page allow adding/removing symbols from the DB? | Read-only for now; SQL directly |
| Date range for OHLCV chart default view | Last 6 months |
| Should signal markers show on the candlestick or as a separate panel? | Overlay on candlestick (coloured triangles) |
| Mobile-responsive or desktop-only? | Desktop-only (local tool) |
