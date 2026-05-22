# MCP Architecture — xCreator Pipeline

## Connected MCP Servers

| Server | Type | Purpose | Tools |
|--------|------|---------|-------|
| **grok** | stdio | Grok chat, vision, image/video gen | `mcp_grok_chat`, `mcp_grok_generate_image`, `mcp_grok_web_search`, `mcp_grok_x_search`, `mcp_grok_grok_agent` |
| **image-turbo** | HTTP | Free HF Space image gen | `mcp_image_turbo_z_image_turbo_generate_image` |
| **firered-edit** | HTTP | Free HF Space image editing | `mcp_firered_edit_firebred_image_edit_1_0_fast_infer` |
| **runpod-docs** | HTTP | RunPod documentation | `mcp_runpod_docs_query_docs_filesystem_runpod_documentation` |
| **xai-docs** | HTTP | xAI Developer documentation | `mcp_xai_docs_list_doc_pages`, `mcp_xai_docs_get_doc_page`, `mcp_xai_docs_search_docs` |

## Key Findings (from xAI docs research)

1. **xAI does NOT expose posting to X** — Grok can search/read X but cannot write
2. **xAI Remote MCP** allows Grok to connect TO external MCP servers (not the reverse)
3. **xAI Docs MCP** is public, no auth required — docs search only
4. **Multi-agent** via `grok-4.20-multi-agent` — internal agents with search + code exec
5. **Grok Build** (`grok-build-0.1`) — coding agent via ACP protocol

## Posting Architecture

```
[Dashboard / Cron Job]
    │
    ├── xurl (X Premium API) ──→ Post, reply, media upload
    │   Requires: OAuth 2.0 app in X Developer Portal
    │
    └── Playwright (Browser) ──→ Post as human
        Requires: Saved session cookies
        Auth: python3 playwright_post.py --login --handle USERNAME
```

## Config Location

`~/.hermes/config.yaml` — `mcp_servers:` section

Add new MCP servers:
```yaml
mcp_servers:
  my-server:
    url: https://example.com/mcp
    timeout: 60
    connect_timeout: 15
    enabled: true
```
