# Session 2026-09-01 — n8n Gradio Bridge

User proposed routing the Gradio Space through n8n instead of direct MCP calls.

Council validated the approach:
- n8n polls outbox every 15 min
- Fires Gradio `/gradio_api/call/post`
- Logs results back to pipeline-state
- Workflow SDK code validated (4 expected placeholder warnings)
- Decision 011 sealed
- Files committed: decision doc, n8n JSON, pipeline-state v1.3

Blockers remain: HF MCP still anonymous, Gradio Space not deployed, real tokens not wired.
Cost: $0.00
