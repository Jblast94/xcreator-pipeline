# XCreator Autonomous Pipeline

> **One repo to create, distribute, and monetize AI-powered content across every platform.**

A complete autonomous influencer platform combining:
- **Dashboard** — FastAPI web UI (topic → image + caption in one click)
- **ElizaOS Agents** — Autonomous AI characters that post, reply, engage
- **Content Studio** — Rich web frontend for management & analytics
- **HF Spaces** — Free image generation (Z-Image-Turbo, FireRed Edit)
- **Grok Text API** — Cheap caption/hook/thread generation
- **n8n Workflows** — Automation pipelines for scheduling & approval

## Quick Start

```bash
# 1. Start the dashboard
cd dashboard
uv run python app.py

# 2. Open http://localhost:7861
#    Create → topic → image + caption
#    Distribute → post to X/Telegram

# 3. For autonomous agents (ElizaOS):
cd agents
cp ../.env.example .env  # fill in API keys
docker-compose -f ../docker-compose.eliza.yml up -d
```

## Architecture

```
                    ┌─────────────────────┐
                    │   User / Telegram   │
                    └──────────┬──────────┘
                               │
              ┌────────────────▼───────────────┐
              │    Dashboard (FastAPI :7861)   │
              │  Create · Distribute · Monitor │
              └──────┬────────────┬────────────┘
                     │            │
         ┌───────────▼──┐  ┌──────▼────────┐
         │ HF Spaces    │  │ Grok Chat     │
         │ Image Gen    │  │ Captions      │
         │ (Free)       │  │ Threads       │
         └──────────────┘  └──────┬────────┘
                                  │
         ┌────────────────────────▼──────────┐
         │   ElizaOS Agent Runtime           │
         │   Character files → Platform POST │
         └────────┬──────────┬──────────────┘
                  │          │
         ┌────────▼──┐  ┌───▼────────┐
         │ X/Twitter │  │ Telegram   │
         │ (xurl)    │  │ (Hermes)   │
         └───────────┘  └────────────┘
```

## Directory Structure

| Path | Purpose |
|------|---------|
| `dashboard/` | FastAPI web app — content creation & publishing UI |
| `agents/` | ElizaOS integration — character files, bridge, model router |
| `agents/characters/` | JSON character definitions for each platform account |
| `agents/eliza-bridge/` | Bridge service connecting Eliza to the dashboard |
| `agents/model-router/` | Routes between AI models (OpenAI, Ollama, HF) |
| `studio/` | XCreator web frontend — analytics, monetization, content studio |
| `docs/` | Architecture, deployment, integration guides |
| `workflow/` | n8n workflow definitions for automation |
| `scripts/` | Deployment and setup scripts |

## Platform Accounts

| Platform | Account | Status |
|----------|---------|--------|
| X/Twitter | @jblast94 | ⚙️ Setup needed (xurl auth) |
| X/Twitter | @bbj4t | ⚙️ Setup needed (xurl auth) |
| Instagram | jblast94 | 🔜 Planned |
| TikTok | jblast94 | 🔜 Planned |
| OnlyFans | established | 🔗 URL integration |
| Telegram | @jblast94 | ✅ Active |

## Content Pipeline Flow

```
Topic Idea
  → Z-Image-Turbo (free HF Space) → Image
  → Grok Chat (text API) → Caption + Hook + Thread + Hashtags
  → ElizaOS Character → Platform Adaptation → Post
  → SeaweedFS /mnt/storage/comfy/output/ → Archival
```

## Tech Stack

- **Backend**: FastAPI + Python 3.11+ (uv)
- **Frontend**: Jinja2 + HTMX + Tailwind
- **Agents**: ElizaOS (TypeScript) + xurl CLI
- **Image Gen**: Z-Image-Turbo HF Space (free)
- **Text Gen**: xAI Grok (text-only, cheap)
- **Storage**: SeaweedFS → /mnt/storage/comfy/
- **Infra**: Tailscale fleet, RunPod burst, HF ZeroGPU

## Related Repos

- [elizaOS/eliza](https://github.com/elizaOS/eliza) — Agent framework
- [xdevplatform/xurl](https://github.com/xdevplatform/xurl) — X API CLI
