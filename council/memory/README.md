# Council Memory System

**Status:** SEALED 2026-09-01
**Location:** Google Drive `Council-Orchestrator-Memory` + this repo mirror
**Orchestrator / God-layer:** Grok (Ara) — permanent, direct line to user

## Purpose
Single source of truth for the multi-agent council. Every agent (Grok, Gemini, custom-relay) reads/writes here first. No more reiteration loops. One brain, one circle.

## Structure
- `decisions/` — Council rulings, routing choices, rejected outputs (append-only)
- `agents/` — Agent configs, capabilities, last-known state
- `sessions/` — Per-run context, prompts, merged outputs
- `pipeline-state/` — Current pipeline health, active jobs, cost logs

## Rules
1. Council (Grok) arbitrates before any agent acts.
2. Memory is append-only where possible; version on conflict.
3. All writes logged with timestamp + agent ID.
4. Hard cap: $0.50/run for intel stages. Gated stages require explicit authorization.
5. User talks to Grok only. Grok fans out.

## Registered Agents
- `grok-ara` — god-layer (wired)
- `gemini-council` — worker (pending wire)
- `custom-relay-boxes` — worker (pending wire)

## Next
- Wire Gemini endpoint + auth.
- Wire custom-relay endpoint.
- Automate session ingest (n8n / Automations) so runs auto-dump into `sessions/`.
- First council routing test.
