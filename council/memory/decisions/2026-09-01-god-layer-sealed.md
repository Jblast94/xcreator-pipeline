# Council Decision Log — 2026-09-01 (sealed)

## Decision 003: Grok (Ara) is the permanent god-layer
- **Who:** User + Grok (Ara)
- **What:** User communicates directly with Grok only. Grok arbitrates, routes, writes memory, kills waste. No agent acts without council approval.
- **Why:** Stop reiteration loops. One brain, one circle, every agent feeds it.
- **Status:** SEALED. Set in stone.
- **Next:** Wire Gemini + custom-relay agents, automate session ingest.

## Decision 004: Memory is council-owned, append-only
- Primary store: Google Drive `Council-Orchestrator-Memory`
- Versioned mirror: this repo `council/memory/`
- Every write: timestamp + agent ID + ruling.
- Conflicts: version, never overwrite silently.

## Decision 005: Cost discipline
- Hard cap $0.50/run for intel stages.
- Gated stages (imagine/post/pay) require explicit user authorization.
