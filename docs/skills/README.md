# Grok Skills — xcreator-pipeline

These are the **Grok Skills** (Skill Creator format) for the pipeline agents.
Each lives in its own directory with a `SKILL.md`. Install by copying into
`~/.grok/skills/` or `<repo>/.grok/skills/` — Grok discovers them automatically.

## Skills

| Skill | Agent | Stage | Status |
|---|---|---|---|
| `orchestrator` | Orchestrator | Control plane | Active |
| `trendscout` | TrendScout | Stage 1 — Ingest | Active |
| `analyst` | Analyst | Stage 2 — Analyze | Active |
| `imagine-worker` | ImagineWorker | Stage 3 — Generate (gated) | Gated |
| `copywriter` | Copywriter | Stage 4 — Draft | Gated |
| `poster` | Poster | Stage 5 — Post (gated) | Gated |
| `payments` | Payments | Stage 6 — Monetize (Phase 2) | Phase 2 |
| `qa` | QA | Smoke test | Active |

## Rules (apply to every skill)

- **Grok-only.** No Qwen, no RunPod, no external generators.
- **One orchestrator.** No second control plane.
- **No database yet.** Output lands in `/data/runs/<date>/`.
- **Hard cap:** $0.50 per daily run. Every cent logged in `cost.json`.
- **Ingest first.** Generation and posting must not run until intel is solid.
- **Monetization is open.** Any offer that converts — not just Linktree.

## How to install

```bash
# From repo root
mkdir -p ~/.grok/skills
cp -a docs/skills/orchestrator ~/.grok/skills/
cp -a docs/skills/trendscout ~/.grok/skills/
cp -a docs/skills/analyst ~/.grok/skills/
# ... etc
```

Or invoke directly in chat: `/trendscout`, `/analyst`, etc.

## Source of truth

`docs/WORKFLOW_AGENTS.md` is the locked workflow. These skills implement it.
