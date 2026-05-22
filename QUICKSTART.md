# XCreator Pipeline — Quick Start

## 1. Start the Dashboard

```bash
cd dashboard

# Install deps (use uv — never pip)
uv sync
# or: uv pip install -r requirements.txt

# Set API keys
export XAI_API_KEY="xai-..."
export HF_TOKEN="hf_..."

# Launch
uv run python app.py
# → http://localhost:7861
```

## 2. Create Content

1. Open **Create** tab
2. Enter a topic
3. Click **Generate Everything**
4. Image appears (from free HF Space) + caption + hook + hashtags

## 3. Post to X

```bash
# First-time setup (run on your machine):
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash
xurl auth apps add my-app --client-id ID --client-secret SECRET
xurl auth oauth2 --app my-app YOUR_HANDLE
xurl auth default my-app

# Then post:
cd agents/characters
# Point the Eliza character at your topic and let it post
```

## 4. Deploy Autonomous Agents

```bash
# Using ElizaOS:
cd agents
npm install @elizaos/core @elizaos/plugin-twitter
npx elizaos start --character ./characters/jblast94.json
```

## 5. Full Stack with Docker

```bash
docker-compose -f docker-compose.eliza.yml up -d
```

## Prerequisites

| What | Where |
|------|-------|
| XAI_API_KEY | https://console.x.ai |
| HF_TOKEN | https://huggingface.co/settings/tokens |
| xurl auth | https://developer.x.com |
| ElizaOS | bun install -g @elizaos/cli |
