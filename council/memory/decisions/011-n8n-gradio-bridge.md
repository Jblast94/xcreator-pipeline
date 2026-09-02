# Decision 011 — n8n as the Gradio Bridge

**Date:** 2026-09-01
**Status:** SEALED
**Author:** Council (Grok orchestrator)

## Ruling

n8n is the official bridge between the council outbox and the Hugging Face Gradio Space poster.

- Grok Bot (and other agents) drop drafts into `grok-bot-outbox`.
- n8n polls every 15 minutes, pulls pending drafts, fires them through the Gradio Space `/gradio_api/call/post` endpoint.
- Gradio Space handles OAuth 1.0a signing, daily cap (5), spacing (45 min + jitter), and returns tweet ID.
- n8n logs the result back to `pipeline-state`.
- No direct Grok-to-HF posting. n8n is the single write path.

## Why

- Keeps posting logic out of the AI layer (no rate-limit bleed).
- n8n gives retry, backoff, and error workflows for free.
- Gradio Space stays a pure API endpoint — no auth logic duplicated.
- If HF or X changes, only the Space or the n8n node changes, not the council.

## Workflow

- File: `n8n/council-x-poster.json` (SDK source in repo)
- Validated: yes (4 warnings on credential placeholders — expected until real tokens wired)
- Cadence: every 15 min
- Error handling: continueRegularOutput on post + log nodes so one failure doesn't kill the run

## Next

1. User links HF account (currently anonymous MCP).
2. User deploys Gradio Space with the poster code.
3. User pastes real Space URL + tokens into n8n placeholders.
4. Activate workflow.
5. First real post requires human review for 7 days.
