# Decision 010 — In-House Gradio Space X Poster Bot

**Date:** 2026-09-01
**Status:** SEALED
**Cost:** $0.00

## Ruling
Build the X poster bot ourselves as a Hugging Face Gradio Space. No third-party bot platforms (Blotato, OpenTweet, etc.).

- Grok Bot / council researches + drafts
- Gradio Space (`x-poster-gradio`) posts via official X API using OAuth 1.0a user token
- Research tab included for trend intel
- Runs on HF free tier or your relay boxes
- Secrets: X OAuth creds, council inbox/outbox URLs, HF_TOKEN

## Repo
https://github.com/Jblast94/x-poster-gradio

## Next
1. Authenticate HF MCP (currently anonymous)
2. Create Space on HF (or push from GitHub)
3. Set secrets in Space settings
4. Wire council outbox → Space inbox
5. Test one post manually before autonomy

## Hard rules
- No bearer tokens
- No scraping
- Daily cap 5, spacing 45min+, jitter
- Automated label + bio disclosure required
- Human review first week