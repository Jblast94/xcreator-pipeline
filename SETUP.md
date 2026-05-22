# XCreator Pipeline — Complete Setup Guide

## Your Setup: X Premium + SuperGrok

You're already on the right plans:
- **X Premium** → X API access (use xurl CLI)
- **SuperGrok** → xAI API key (already configured)
- **X Premium (alt account @bbj4t)** → second API slot
- **Playwright** → browser automation backup

---

## 1. Generate an xAI API Key (You do this)

1. Go to https://console.x.ai
2. Create or copy an API key
3. Paste it into the pipeline:

```bash
cd /root/xcreator-pipeline
echo "XAI_API_KEY=xai-xxxxxxxxxxxx" >> .env
```

Already configured in Hermes — the Grok MCP tools are live. You can test:

```bash
# From dashboard:
cd dashboard && uv run python app.py
# Open http://localhost:7861 → Create tab → generate content
```

---

## 2. Auth xurl for Posting to X (You do this)

xurl is already installed on edge. You just need to authenticate with your X Premium account.

### Step 1: Create an X Developer App

1. Go to https://developer.x.com/en/portal/dashboard
2. Create a new app (you can use your Premium access)
3. **App type**: "Web app, automated app or bot"
4. **Redirect URI**: `http://localhost:8080/callback`
5. **Website URL**: `https://jb-ai.encke-elver.ts.net` or any of your domains
6. Copy **Client ID** and **Client Secret**

### Step 2: Auth @jblast94

```bash
xurl auth apps add jblast --client-id YOUR_ID_HERE --client-secret YOUR_SECRET_HERE
xurl auth oauth2 --app jblast @jblast94
# ↑ Opens browser — log in as @jblast94
xurl auth default jblast
xurl whoami  # Verify
```

### Step 3: Auth @bbj4t

```bash
xurl auth apps add bbj4t --client-id YOUR_ID_HERE --client-secret YOUR_SECRET_HERE
xurl auth oauth2 --app bbj4t @bbj4t
```

### Step 4: Test Posting

```bash
xurl post "Pipeline test. Autonomous content incoming. 🤖"
xurl --app bbj4t post "Testing from the second account."
```

---

## 3. Browser Automation (Playwright) — Backup

For accounts without API access, or as a fallback:

### Save cookies (one-time, interactive):

```bash
cd /root/xcreator-pipeline/agents
python3 playwright_post.py --login --handle jblast94 --cookies /root/.x-cookies-jblast.json
# ↑ Browser opens — log into X, press ENTER to save
python3 playwright_post.py --login --handle bbj4t --cookies /root/.x-cookies-bbj4t.json
```

### Post via browser:

```bash
python3 playwright_post.py --handle jblast94 --text "Posted via browser automation" --cookies /root/.x-cookies-jblast.json
python3 playwright_post.py --handle jblast94 --thread "Tweet 1" "Tweet 2" "Tweet 3" --cookies /root/.x-cookies-jblast.json
```

---

## 4. Run the Dashboard

```bash
cd /root/xcreator-pipeline/dashboard
uv run python app.py
# → http://localhost:7861
```

### What works right now:

| Feature | Status | How |
|---------|--------|-----|
| **Create tab** | ✅ LIVE | Topic → image (HF Space) + caption (Grok) |
| **Trends tab** | ✅ LIVE | Grok prompt library — copy/paste into Grok |
| **Agents tab** | ✅ LIVE | Shows generated Eliza character files |
| **Distribute tab** | ✅ LIVE | Guides for X (xurl) + Telegram |
| **X posting** | ⏳ Needs you | Auth xurl (Step 2 above) |
| **Browser posting** | ⏳ Needs you | Save cookies (Step 3 above) |

---

## 5. Your Grok Workflow

No complex trend scanner needed. **You are the trend scanner.** Open Grok on X, paste:

**Quick Scan:**
```
List 5 trending niches on X right now. For each: name, description, tone, audience, 3 hook formulas, 5 hashtags, monetization angle, trending velocity. Return as JSON array.
```

**Content from trend:**
```
Based on the trending topic "{topic}" in {niche}:
1. Hook tweet (≤280 chars)
2. 5-tweet thread
3. 10 hashtags
4. Image prompt

Return as structured JSON.
```

**Character from niche:**
```
Create an ElizaOS character.json for a {niche} influencer.
Tone: {tone}. Audience: {audience}.
Generate: name, bio (5), lore (5), postExamples (5), style, topics.
Make it human, not bot.
```

**Paste Grok's output back to me** — I'll generate the character files and schedule the posting.

---

## 6. Schedule Auto-Posting

After xurl is authed:

```bash
# Post every 6 hours (trend-based):
hermes cron create \
  --name "auto-trend-post" \
  --schedule "every 6h" \
  --prompt "Search X for trending topic in AI/tech. Generate hook + thread + image. Post to @jblast94 using xurl." \
  --skills xurl,social-orchestrator

# Daily morning post:
hermes cron create \
  --name "morning-tweet" \
  --schedule "0 8 * * *" \
  --prompt "Generate a provocative tweet about AI/agents. Use mcp_grok_chat for text, image-turbo for image. Post to @jblast94 using xurl." \
  --skills xurl,social-orchestrator
```

---

## 7. Your Quick Checklist

| # | Task | Command | Time |
|---|------|---------|------|
| 1 | Get xAI API key | https://console.x.ai | 2 min |
| 2 | Create X dev app | https://developer.x.com | 5 min |
| 3 | Auth @jblast94 | `xurl auth oauth2 --app jblast @jblast94` | 2 min |
| 4 | Auth @bbj4t | `xurl auth oauth2 --app bbj4t @bbj4t` | 2 min |
| 5 | Test post | `xurl post "hello world"` | 1 min |
| 6 | Run dashboard | `cd dashboard && uv run python app.py` | 1 min |
| 7 | Open Grok on X | Paste Quick Scan prompt | 2 min |
| 8 | Paste results to me | Drop JSON output in this chat | 1 min |

**Total: ~15 minutes to first autonomous post.**
