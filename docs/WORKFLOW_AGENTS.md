# xcreator-pipeline — Agent Workflow (LOCKED)

> Version 1.0 — 2026-09-01. This is the source of truth. Do not deviate without an explicit user decision.

## Goal
Ingest trending data → decide what to post → generate character-aligned content → draft final copy → post → monetize. **Ingestion and analytics are the spine.** Generation and posting are downstream and must not run until the intel is solid.

## Hard rules
- **Grok-only.** No Qwen, no RunPod, no external generators. Grok Imagine Image 2.0 for images, Grok text models for analysis/drafting.
- **One orchestrator.** Dockhand (or the DeepSeek harness) owns compose/deploy. Hauser agents own everything else. No second control plane.
- **No database yet.** Everything lands in `/data/runs/<date>/` as JSON + images + manifest. Postgres/Supabase comes in Phase 2.
- **Hard cost cap:** $0.50 per daily run. Every cent logged in `cost.json`.
- **No payments in Phase 1.** Stripe Link / Linktree Commerce is Phase 2, only after 3 clean days of intel.
- **Monetization is not limited to Linktree.** Any popular social offer, product, or trend that can be monetized is fair game. The matcher picks whatever converts.
- **Notifications:** email + device app notification. Keep it simple.

## Pipeline stages

### Stage 1 — INGEST (TrendScout)
- **Owner:** TrendScout agent (Grok Bot / Hauser worker)
- **Input:** X trends via `x_search` (no paid API), plus optional Reddit/public feeds later.
- **Niches (starting set, editable):** AI tools, side hustle, content creation, affiliate marketing, and whatever is spiking.
- **Output:** `/data/runs/<date>/trends.json` — ranked list of topics with score, velocity, sample posts, entities, sentiment.
- **Rule:** This stage MUST succeed before any generation. If ingest fails, the run aborts and emails the failure.

### Stage 2 — ANALYZE (Analyst)
- **Owner:** Analyst agent
- **Input:** `trends.json`
- **Job:** Score each trend for monetizability (margin potential, audience fit, shelf life). Match to character persona + any available offers (Linktree or otherwise).
- **Output:** `/data/runs/<date>/matches.json` — top 3–5 trends with matched offer angle, suggested hook, confidence.
- **Rule:** Only fresh trends (under 48h) are eligible. Stale = flagged, not used.

### Stage 3 — GENERATE (ImagineWorker) — Phase 1.5, gated
- **Owner:** ImagineWorker
- **Trigger:** Only after Stage 2 produces a match above threshold.
- **Input:** character reference + matched trend angle
- **Tool:** Grok Imagine Image 2.0 only
- **Output:** `/data/runs/<date>/assets/` — images + `manifest.json` (prompt, trend_id, cost, timestamp)
- **Rule:** Gallery-first. No SillyTavern. No RunPod.

### Stage 4 — DRAFT (Copywriter)
- **Owner:** Copywriter agent (Grok Bot)
- **Input:** matches + assets
- **Output:** `/data/runs/<date>/drafts/` — caption, hashtags, CTA, link placeholder. Final write happens here.
- **Rule:** One draft per matched trend. Short, hook-first, CTA-last.

### Stage 5 — POST (Poster) — Phase 2, gated
- **Owner:** Poster agent
- **Trigger:** Manual approval for the first 3 days, then autonomous.
- **Output:** post live on X (and Telegram group later). Result logged to `posts.json`.

### Stage 6 — MONETIZE (Phase 2)
- Stripe Link wallet + Linktree Commerce (or any offer API). Only after 3 clean intel days.
- Every click/sale writes back so the matcher learns what converts.

## Agent roster & responsibilities

| Agent | Role | Owns | Must NOT touch |
|---|---|---|---|
| **Orchestrator** (Dockhand / DeepSeek harness) | Control plane | compose files, deploys, one OmniRoute instance | content, posting, memory writes |
| **TrendScout** | Ingest | X/Reddit scrape, `trends.json` | generation, posting |
| **Analyst** | Analyze | scoring, matching, `matches.json` | raw scraping, image gen |
| **ImagineWorker** | Generate | Grok Imagine calls, assets | trends, drafts, posting |
| **Copywriter** | Draft | captions, CTAs, `drafts/` | scraping, generation params |
| **Poster** | Publish | X/Telegram posts, `posts.json` | anything before Stage 4 approval |
| **QA** | Smoke test | daily health check, cost log | business logic |
| **Payments** (Phase 2) | Monetize | Stripe Link, Linktree, conversion logging | everything else |

## Daily automation
- **Schedule:** 08:00 America/New_York, daily.
- **Runs:** Stage 1 → Stage 2 only. Stages 3–6 gated.
- **Notification:** email + device app.
- **Cap:** $0.50/run, logged.
- **On failure:** email the error, do not retry blindly, open/update the matching GitHub issue.

## Phase gates
1. **Phase 1 (now):** Ingest + Analyze + daily email. Prove the intel loop for 3 days.
2. **Phase 1.5:** Add Imagine generation on matched trends.
3. **Phase 2:** Add posting + payments. Autonomous after approval.

## Non-goals (for now)
- No Qwen, no RunPod, no SillyTavern as primary.
- No second orchestrator.
- No database until Phase 2.
- No over-engineering. Small, replaceable pieces.
