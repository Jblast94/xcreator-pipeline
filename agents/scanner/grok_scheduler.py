"""grok_scheduler.py — Prompt templates + cron job configs for Grok-powered trend scanning.

NO complex scanner logic. Just:
  - Prompt templates you paste into Grok
  - Cron job configs for Hermes to schedule

Grok IS the scanner. We just feed it the right prompt and schedule the output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ── Prompt Templates ─────────────────────────────────────────────────────────

TREND_SCAN_PROMPT = """You are a trend analyst. Search X for trending topics right now.
List 5 trending niches. For each: name, description, tone, audience, 3 hook formulas that work, 5 hashtags, monetization angle, trending velocity.

Return as JSON array."""

NICHE_DEEP_SCAN = """Search X for top creators and conversations in the niche "{niche}".
Analyze: what hooks work, what tone dominates, who the top 5 creators are, what monetization strategies they use, and what the audience responds to.

Return as structured data with: name, description, tone, audience, content_pillars (5), hook_patterns (5), hashtags (10), competitors (5), monetization_angle."""

DAILY_TREND_REPORT = """Search X for what's trending RIGHT NOW across these niches: AI, crypto, fitness, adult content, finance, tech.
For each niche: find the TOP 3 trending posts/topics. Explain WHY each is trending.
Then recommend: which niche has the highest engagement potential RIGHT NOW and what angle to use."""

CONTENT_FROM_TREND = """Based on the trending topic "{topic}" in the {niche} niche:
1. Write a hook tweet (≤280 chars) that would stop the scroll
2. Write a 5-tweet thread expanding on the topic
3. Generate 10 relevant hashtags
4. Describe an image prompt that would get high engagement for this post

Return as: hook, thread (array of 5 tweets), hashtags (array), image_prompt"""

CHARACTER_FROM_NICHE = """Create an ElizaOS character.json from this niche analysis:

Niche: {niche}
Hook patterns that work: {hooks}
Tone: {tone}
Audience: {audience}

Generate a complete character.json with:
  name, modelProvider, clients, plugins, settings
  bio (5 lines), lore (5), knowledge (5), postExamples (5)
  adjectives, topics, style (all/chat/post)

Make it sound like a real human in this niche, not a bot."""


# ── Cron Job Configs ─────────────────────────────────────────────────────────

@dataclass
class CronConfig:
    """A cron job configuration for trend-to-content automation."""
    name: str
    prompt: str
    schedule: str
    skills: list[str] = field(default_factory=list)
    deliver: str = "origin"
    model: str = "grok-3-mini"


SCHEDULED_JOBS = {
    "daily-trend-scan": CronConfig(
        name="daily-trend-scan",
        prompt=DAILY_TREND_REPORT,
        schedule="0 8 * * *",  # Every day at 8 AM
        skills=["social-orchestrator"],
        deliver="origin",
    ),
    "weekly-niche-deep": CronConfig(
        name="weekly-niche-deep",
        prompt="Search X for the fastest-growing niche this week. Deep analyze it. Return structured data.",
        schedule="0 9 * * 1",  # Every Monday at 9 AM
        skills=["social-orchestrator"],
        deliver="origin",
    ),
}


def get_job_config(name: str) -> dict | None:
    """Get a cron job config dict ready for Hermes cronjob tool."""
    config = SCHEDULED_JOBS.get(name)
    if not config:
        return None
    return {
        "action": "create",
        "name": config.name,
        "prompt": config.prompt,
        "schedule": config.schedule,
        "skills": config.skills if config.skills else None,
        "deliver": config.deliver,
    }


def trend_prompt(niche: str) -> str:
    """Build a prompt for scanning a specific niche."""
    return NICHE_DEEP_SCAN.format(niche=niche)


def content_prompt(topic: str, niche: str) -> str:
    """Build a prompt for generating content from a trend."""
    return CONTENT_FROM_TREND.format(topic=topic, niche=niche)


def character_prompt(niche: str, hooks: str, tone: str, audience: str) -> str:
    """Build a prompt for generating an Eliza character from niche data."""
    return CHARACTER_FROM_NICHE.format(
        niche=niche, hooks=hooks, tone=tone, audience=audience
    )


# ── Schedule Builder ─────────────────────────────────────────────────────────

def schedule(
    niche: str,
    post_frequency: str = "every 6h",
    trend_scan: str = "0 8 * * *",
) -> list[dict]:
    """Generate a full suite of cron jobs for one niche.
    
    Returns list of cron job configs ready for cronjob(action='create', ...).
    """
    jobs = [
        {
            "name": f"{niche.lower().replace(' ', '-')}-trend-scan",
            "prompt": f"Search X for the top trending topics in {niche} right now. Summarize the top 3.",
            "schedule": trend_scan,
            "skills": ["social-orchestrator"],
        },
        {
            "name": f"{niche.lower().replace(' ', '-')}-auto-post",
            "prompt": f"""Search X for what's trending in {niche} right now. Pick the best topic.
Then generate a post: hook (280 chars) + 5-tweet thread + hashtags + image prompt.
Use image-turbo MCP for the image, xurl skill to post to X.""",
            "schedule": post_frequency,
            "skills": ["xurl", "social-orchestrator"],
        },
    ]
    return jobs


# ── Quick Reference ──────────────────────────────────────────────────────────

REFERENCE = """
│▌ Grok Trend Prompts — Use in Grok Chat or Grok X Search
│▌
│▌ 1. SCAN: "List 5 trending niches on X right now. Return JSON."
│▌ 2. DEEP: "Analyze the [niche] niche on X. Top hooks, creators, monetization."
│▌ 3. DAILY: "What's trending on X across AI, crypto, fitness, finance, adult content?"
│▌ 4. CONTENT: "Write a tweet thread about [topic] in the [niche] niche."
│▌ 5. CHARACTER: "Generate an ElizaOS character.json for a [niche] influencer."
│▌
│▌ Cron Schedule Examples:
│▌   "every 6h"      → every 6 hours
│▌   "0 8 * * *"     → daily at 8 AM
│▌   "0 */12 * * *"  → every 12 hours
│▌   "0 9 * * 1"     → every Monday 9 AM
│▌   "0 9,15 * * *"  → 9 AM and 3 PM daily
"""
