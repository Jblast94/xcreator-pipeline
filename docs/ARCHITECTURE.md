# Architecture — XCreator Autonomous Pipeline

## High-Level Design

**Goal:** An autonomous content factory. Human enters topic → AI generates image + copy → posts to platforms → tracks performance → optimizes.

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                          │
│  Telegram (DM) · Dashboard (Web :7861) · CLI (Hermes)     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    LAYER 1: ORCHESTRATOR                    │
│                   content_gen.py (Python)                   │
│                                                            │
│  create_content_piece(topic, platform, tone)                │
│    → generate_image_turbo(prompt)  [HF Space, free]        │
│    → generate_caption(topic)       [Grok, cheap text]      │
│    → generate_hashtags(topic)      [Grok, cheap text]      │
│    → make_thread(topic)            [Grok, cheap text]      │
│    → adapt_for_platforms(piece)                             │
│    → save to /mnt/storage/comfy/output/                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    LAYER 2: ELIZA AGENTS                    │
│               agents/characters/*.json                      │
│                                                            │
│  Character Files define:                                    │
│  - Personality (bio, lore, style, topics)                   │
│  - Platform clients (twitter, telegram, discord)            │
│  - Model preferences (OpenAI, Ollama, Grok)                 │
│  - Posting schedule & tone                                  │
│                                                            │
│  Eliza Bridge Service connects agents → platform APIs       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    LAYER 3: PUBLISHING                      │
│                                                            │
│  X/Twitter:    xurl CLI (OAuth 2.0)                        │
│  Telegram:     Hermes send_message()                        │
│  Instagram:    🔜 Planned                                   │
│  TikTok:       🔜 Planned                                   │
│  OnlyFans:     🔜 API Integration                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    LAYER 4: STORAGE & INFRA                 │
│                                                            │
│  /mnt/storage/comfy/ — SeaweedFS (distributed, persistent)  │
│    ├── output/     ← All generated images/videos             │
│    ├── input/      ← Source images for editing               │
│    ├── models/     ← ComfyUI checkpoints, LoRAs             │
│    └── workflows/  ← ComfyUI workflow JSONs                  │
│                                                            │
│  Tailscale fleet for cross-node communication               │
│  RunPod/Vast.ai for GPU burst                                │
│  HF ZeroGPU for free inference                               │
└─────────────────────────────────────────────────────────────┘
```

## Backend Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Image gen | HF Spaces (free) | Zero cost. Z-Image-Turbo is fast + uncensored |
| Text gen | Grok chat only | $0.15/M tokens, way cheaper than image gen |
| Agent framework | ElizaOS | Built-in Twitter/Discord/TG clients, character system |
| CLI tool | xurl | Official X CLI, OAuth 2.0, maintained by X team |
| Dashboard | FastAPI+HTMX | Lightweight, no JS framework needed |
| Storage | SeaweedFS | Distributed, scalable across fleet |
| Deploy | Docker Compose | Consistent across dev/prod |

## Cost Breakdown (Per Post)

| Service | Cost | Notes |
|---------|------|-------|
| Image (HF Space) | $0 | Free ZeroGPU tier |
| Caption (Grok) | ~$0.0003 | ~200 tokens @ $0.15/M input |
| Thread (Grok) | ~$0.001 | ~1000 tokens |
| Hashtags (Grok) | ~$0.0001 | ~50 tokens |
| **Total** | **~$0.0014** | **Less than 1/10th of a cent per post** |

## Security

- API keys in `.env` only (never in code)
- xurl OAuth 2.0 tokens auto-refresh
- HF Spaces use `.hf_token` for auth
- All infra behind Tailscale (no public ports except Caddy/Traefik)
- Gitea mirrors for backup, GitHub as public origin
