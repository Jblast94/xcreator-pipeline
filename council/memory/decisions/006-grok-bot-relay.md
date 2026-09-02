# Decision 006 — Grok Bot as Drive-relay worker

**Date:** 2026-09-01
**Status:** SEALED

## Ruling
Grok Bot is registered as a council worker. Because it is currently rate-limited and we are not upgrading it, it operates exclusively through the Google Drive relay:

- Council writes tasks to `Council-Orchestrator-Memory/Agents/grok-bot-inbox/`
- Grok Bot polls, executes, writes results to `.../grok-bot-outbox/`
- Ara (orchestrator) reads the outbox and merges into memory.

No direct API calls to Grok Bot from the council until rate limits clear or an upgrade is authorized.

## Rationale
Keeps the pipeline circle intact without burning the rate budget. Drive is the shared bus — same pattern as the custom relay boxes.
