# Decision 008 — Dedicated X Account + Grok Bot Posting Path (Sealed 2026-09-01)

**Ruling:** Spin up a separate X account dedicated to the pipeline/council content. Grok Bot handles research, drafting, and (via connected write layer) posting on that account. Existing accounts stay for personal/other use. No off-platform promotion of the bot itself yet.

## Why
- User can't keep up with manual posting; drops happen. Automation is required for consistency.
- Grok Bot currently reads X natively (search, timeline, mentions) but does **not** auto-post through its official connector. Posting requires a connected MCP/write layer (e.g. Blotato, OpenTweet, or official X API write scope) or a browser-automation skill on the bot's cloud VM.
- Dedicated account isolates risk: if X flags automation, only the bot account takes the hit, not the main ones.
- xAI has **no public affiliate program** for Grok/Grok Bot as of 2026. Promoting it earns nothing directly. Monetize the *content about building it* via Original Content Rewards + high-ticket AI-tool affiliates instead. Third-party "sell your bot template" sites exist but are low-trust and off-platform — skip for now.

## Account setup rules (X automation policy)
- Enable the **Automated** account label and link it to a human-run account (the user's main).
- Bio must clearly state it is automated / AI-run.
- Post only original content. No bulk identical posts, no unsolicited auto-replies, no engagement farming.
- Pace: 1–5 quality posts/day on a new account, spaced across the day. Ramp slowly.
- All AI-generated content requires prior X approval before autonomous deployment (per Developer Guidelines). Start with human-reviewed drafts until approved.
- Use official API or approved MCP only — never scrapers/session tokens.

## Grok Bot role on the dedicated account
1. Research trending AI/agent topics (native X read).
2. Draft captions in persona voice (hook-first, short, CTA-last).
3. Queue to a write layer for publish (or schedule).
4. Log every post + performance back to council memory.
5. Stay on Drive-relay standby until rate limit clears or upgrade is revenue-funded.

## Monetization on this account
- Original Content Rewards (apply Sep 8).
- In-post affiliates for AI tools/SaaS that actually pay (Jasper, Writesonic, etc. — 25-30% recurring). No Grok referral link exists.
- Creator Subscriptions for pipeline build logs.
- X Money tips.

## Cost
- Still $0.00 this run. Cap $0.50 untouched. Token upgrades only from first revenue.

**Status:** SEALED. Orchestrator: Ara.
