# XCreator Pipeline — User Setup Guide
## Everything you need to run to get autonomous posting live

---

## 1. GitHub & Gitea Access

### Clone the main repo to your machine

```bash
# From GitHub (public, no auth needed to read):
git clone https://github.com/Jblast94/xcreator-pipeline.git
cd xcreator-pipeline

# Or from Gitea (if you have SSH access):
git clone ssh://git@100.97.161.104:2222/root/xcreator-pipeline.git
cd xcreator-pipeline
```

---

## 2. xurl — X/Twitter CLI (MANDATORY for auto-posting)

This is the #1 blocker. Do this on your main machine (ai-laptop or linux-home).

```bash
# Install xurl
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Verify
xurl --help
```

### Create an X API App

1. Go to https://developer.x.com/en/portal/dashboard
2. Create a new project + app
3. Set **redirect URI**: `http://localhost:8080/callback`
4. Copy the **Client ID** + **Client Secret**
5. Set app type to **"Web app, automated app or bot"** in User Authentication Settings

### Auth your first X account (@jblast94)

```bash
xurl auth apps add jblast --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app jblast @jblast94
# ↑ This opens a browser. Auth with @jblast94's X account.
xurl auth default jblast

# Verify:
xurl whoami
```

### Auth your second X account (@bbj4t)

```bash
xurl auth apps add bbj4t --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app bbj4t @bbj4t
# ↑ Auth with @bbj4t's X account.

# To post as bbj4t, use:
xurl --app bbj4t post "tweet text"
```

### Test posting

```bash
xurl post "Testing the pipeline. Autonomous content incoming. 🤖"
```

---

## 3. Run the Dashboard

```bash
cd xcreator-pipeline/dashboard

# Install dependencies (use uv, never pip):
uv sync

# Set API keys (if not already in env):
export XAI_API_KEY="xai-..."    # From https://console.x.ai
export HF_TOKEN="hf_..."         # From https://huggingface.co/settings/tokens

# Launch:
uv run python app.py
# → Opens at http://localhost:7861
```

### Dashboard tabs

| Tab | Purpose |
|-----|---------|
| **Dashboard** | System overview, health status |
| **Create** | Topic → image + caption + thread in one click |
| **Trends** | Grok prompt library — scan X niches |
| **Agents** | View/manage Eliza character files |
| **Distribute** | Publishing guides for each platform |
| Grok | (legacy) xAI direct image/video gen |
| Outputs | Generated content archive |

---

## 4. Grok Trend Scanning (Your Part)

Open Grok on X (or `mcp_grok_chat`) and paste these:

### Quick Scan — copy this whole block:

```
List 5 trending niches on X right now. For each: name, description, tone, audience, 3 hook formulas, 5 hashtags, monetization angle, trending velocity. Return as JSON array.
```

### Deep Dive — replace {niche}:

```
Analyze the {niche} niche on X. What hooks work? Top 5 creators? Monetization strategies? Return structured data.
```

### Daily Trend Report:

```
Search X for what's trending RIGHT NOW across: AI, crypto, fitness, adult content, finance, tech. For each niche: top 3 trending posts with WHY. Recommend: best niche to post in right now and what angle.
```

### Generate Content from Trend:

```
Based on trending topic "{topic}" in {niche}:
1. Hook tweet (≤280 chars)
2. 5-tweet thread
3. 10 hashtags
4. Image prompt for high engagement

Return as structured JSON.
```

---

## 5. Schedule Auto-Posting (via Hermes CLI)

Once xurl is authed on the machine running Hermes:

```bash
# Post every 6 hours from a trend-based agent:
hermes cron create \
  --name "trend-agent-auto" \
  --schedule "every 6h" \
  --prompt "Search X for trending topic. Generate hook + thread + image. Post to X using xurl. Use image-turbo MCP for image." \
  --skills xurl,social-orchestrator

# Daily morning post at 8 AM:
hermes cron create \
  --name "morning-tweet" \
  --schedule "0 8 * * *" \
  --prompt "Generate a tweet about AI/tech trends. Hook + hashtags + image. Post to X." \
  --skills xurl,social-orchestrator
```

---

## 6. Deploy from the Dashboard

```bash
# To run in background:
cd /root/xcreator-pipeline/dashboard
nohup uv run python app.py > pipeline.log 2>&1 &
echo "Dashboard running at http://localhost:7861"
```

Or via Docker:

```bash
cd /root/xcreator-pipeline
docker-compose -f docker-compose.eliza.yml up -d
```

---

## 7. Glossary

| Term | What it means |
|------|--------------|
| **xurl** | X/Twitter CLI — posts tweets, uploads media, reads timelines |
| **ElizaOS** | Open-source agent framework — runs character.json files |
| **Character** | JSON file defining an agent's personality, style, platform clients |
| **Grok** | xAI's LLM — used for TEXT ONLY (cheap captions/threads) |
| **Z-Image-Turbo** | Free HF Space — generates images at zero cost |
| **HF Space** | Hugging Face hosted app — free inference tier |
| **Cron job** | Scheduled task that runs on a timer (Hermes or systemd) |
| **SeaweedFS** | Distributed file system — stores all outputs at /mnt/storage/comfy/ |

---

## 8. Quick Reference

```bash
# Dashboard
uv run python dashboard/app.py                    # Start UI
open http://localhost:7861                         # Open it

# Post to X
xurl post "text"                                   # Single tweet
xurl --app bbj4t post "text"                       # Other account
xurl media upload photo.png && xurl post "x" --media-id ID  # With image
xurl reply POST_ID "text"                          # Reply
xurl thread TWEET1 "TWEET2" "TWEET3"               # Thread

# Cron
hermes cron list                                   # See scheduled jobs
hermes cron remove JOB_ID                          # Stop a job
hermes cron create --name "" --schedule "" --prompt ""  # Create job

# Git
git push origin main                               # Push to GitHub
git push gitea main                                # Push to Gitea
```

---

## 9. Platform Accounts Ready to Wire

| Account | Platform | xurl Setup | Auth Done? |
|---------|----------|-----------|------------|
| @jblast94 | X/Twitter | ⬜ Not yet | — |
| @bbj4t | X/Twitter | ⬜ Not yet | — |
| Instagram | IG | 🔜 Future | — |
| TikTok | TT | 🔜 Future | — |
| OF account | OnlyFans | 🔜 Future | — |
| Telegram | TG | ✅ Already | Hermes connected |

---

## What to Do Right Now (Priority Order)

1. **⬜ `curl -fsSL ... | bash`** → Install xurl
2. **⬜ `xurl auth apps add jblast`** → Register your X app
3. **⬜ `xurl auth oauth2 --app jblast @jblast94`** → Auth your main account
4. **⬜ `xurl whoami`** → Verify it works
5. **⬜ Open Grok on X** → Paste the Quick Scan prompt → Send me results
6. **⬜ `uv run python app.py`** → Start dashboard
7. **⬜ Paste Grok results into Trends tab** → Generate characters
8. **⬜ `hermes cron create`** → Schedule auto-posting
