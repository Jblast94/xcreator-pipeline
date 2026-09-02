# Council Memory System

**Status:** Initialized 2026-09-01
**Location:** Google Drive `Council-Orchestrator-Memory` + this repo mirror
**Orchestrator:** Grok (Ara) as god-layer

## Purpose
Single source of truth for the multi-agent council. Every agent (Grok, Gemini, custom) reads/writes here first. No more reiteration loops.

## Structure
- `decisions/` — Council rulings, routing choices, rejected outputs
- `agents/` — Agent configs, capabilities, last-known state
- `sessions/` — Per-run context, prompts, merged outputs
- `pipeline-state/` — Current pipeline health, active jobs, cost logs

## Rules
1. Council (Grok) arbitrates before any agent acts.
2. Memory is append-only where possible; version on conflict.
3. All writes logged with timestamp + agent ID.
4. Hard cap: $0.50/run for intel stages.

## Next
- Wire n8n / Automations to auto-ingest session logs.
- Add Gemini + custom agents to `agents/`.
- Test council routing on a sample task.
