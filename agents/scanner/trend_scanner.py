"""trend_scanner.py — Real-time trend analysis using Grok X Search + Web Search.

Discovers trending X niches and generates structured data for character creation.

Architecture:
  Grok MCP Tools (mcp_grok_x_search, mcp_grok_web_search, mcp_grok_chat)
    → TrendAnalyzer (this module)
      → CharacterGenerator (character_gen.py)
        → Eliza character.json files
          → Autonomous agents
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
if not XAI_API_KEY:
    try:
        import yaml
        cfg_path = Path.home() / ".hermes" / "config.yaml"
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text())
            XAI_API_KEY = cfg.get("XAI_API_KEY", "")
    except Exception:
        pass

XAI_BASE_URL = "https://api.x.ai/v1"
CHARACTERS_DIR = Path(__file__).parent.parent / "agents" / "characters"
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Trend:
    """A detected trend with actionable data."""
    id: str = ""
    topic: str = ""
    niche: str = ""  # e.g. "ai-coding", "fitness", "crypto"
    platform: str = "twitter"
    engagement_score: int = 0  # 1-100
    description: str = ""
    key_hashtags: list[str] = field(default_factory=list)
    top_influencers: list[str] = field(default_factory=list)
    avg_posting_frequency: str = ""  # e.g. "2-3x/day"
    content_style: str = ""  # e.g. "educational", "provocative", "entertainment"
    detected_at: str = ""


@dataclass 
class NicheProfile:
    """A complete niche profile for character creation."""
    name: str = ""
    description: str = ""
    tone: str = ""
    audience: str = ""
    content_pillars: list[str] = field(default_factory=list)
    hook_patterns: list[str] = field(default_factory=list)
    hashtag_pool: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    monetization_angle: str = ""
    trending_velocity: str = ""  # "rising", "peaked", "stable", "declining"


# ── Trend Scanner ────────────────────────────────────────────────────────────

class TrendScanner:
    """Scans X/Web for trending niches using Grok."""

    def __init__(self):
        self.api_key = XAI_API_KEY
        self.base_url = XAI_BASE_URL

    def _grok_chat(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        """Call Grok chat API (cheap text-only)."""
        if not self.api_key:
            return "ERROR: No XAI_API_KEY"

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": "grok-3-mini",
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                return f"ERROR: {resp.status_code}"
        except Exception as e:
            return f"ERROR: {e}"

    def scan_trending_hashtags(self, count: int = 15) -> list[str]:
        """Discover trending hashtags across X niches."""
        prompt = f"""List {count} trending hashtags on X/Twitter right now across different niches.
Return ONLY as a JSON array of strings: ["#hashtag1", "#hashtag2", ...]
Pick a diverse mix: tech, crypto, AI, fitness, finance, entertainment, news, memes, adult/NSFW.
No explanations, no markdown, just the JSON array."""
        
        system = "You track X/Twitter trending topics in real-time. Return only valid JSON arrays."
        result = self._grok_chat(prompt, system, max_tokens=500)
        
        try:
            # Try parsing as JSON
            if result.startswith("["):
                return json.loads(result)
        except Exception:
            pass
        
        # Fallback: extract hashtags
        import re
        hashtags = re.findall(r'#(\w+)', result)
        return [f"#{h}" for h in hashtags[:count]]

    def scan_trending_niches(self, count: int = 10) -> list[NicheProfile]:
        """Discover trending X niches and their profiles."""
        prompt = f"""Analyze X/Twitter right now. Identify {count} trending niches that are GROWING fast.
For each niche, return a JSON object with:
  name: the niche name
  description: 1-sentence what it's about
  tone: the dominant tone (educational, provocative, entertaining, controversial, teasing, inspirational)
  audience: target audience description
  content_pillars: array of 3-5 content topics within this niche
  hook_patterns: array of 3-4 hook formulas that work in this niche
  hashtag_pool: array of 5-10 relevant hashtags
  competitors: array of 3-5 top creator handles in this niche
  monetization_angle: how creators in this niche make money
  trending_velocity: "rising", "peaked", "stable", or "declining"

Return ONLY a JSON array of these objects. No markdown, no other text.
Make the niches diverse and include at least one from: AI/tech, crypto/web3, fitness, finance, adult/NSFW, entertainment."""
        
        system = "You are a social media trend analyst. Return ONLY valid JSON arrays. No markdown formatting."
        result = self._grok_chat(prompt, system, max_tokens=2000)
        
        try:
            # Clean up markdown code blocks
            clean = result.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            profiles = []
            for item in data:
                profiles.append(NicheProfile(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    tone=item.get("tone", "engaging"),
                    audience=item.get("audience", ""),
                    content_pillars=item.get("content_pillars", []),
                    hook_patterns=item.get("hook_patterns", []),
                    hashtag_pool=item.get("hashtag_pool", []),
                    competitors=item.get("competitors", []),
                    monetization_angle=item.get("monetization_angle", ""),
                    trending_velocity=item.get("trending_velocity", "stable"),
                ))
            return profiles
        except Exception as e:
            print(f"[trend_scanner] Parse error: {e}")
            print(f"Raw: {result[:300]}")
            return []

    def deep_scan_niche(self, niche_name: str) -> NicheProfile:
        """Deep dive into ONE niche for detailed character creation."""
        prompt = f"""Do a deep analysis of the X/Twitter niche: "{niche_name}"

Return a JSON object with:
  name: "{niche_name}"
  description: detailed description of what this niche is about
  tone: the dominant tone that works best (one of: educational, provocative, entertaining, controversial, teasing, inspirational, funny, architectural)
  audience: detailed target audience demographics and psychographics
  content_pillars: array of 5-7 specific content topics that perform well
  hook_patterns: array of 5 specific hook formulas that work in this niche (be specific, not generic)
  hashtag_pool: array of 15-20 relevant hashtags by popularity
  competitors: array of 7-10 top creator handles with their follower count in parentheses
  monetization_angle: 2-3 sentence description of how to monetize in this niche
  trending_velocity: "rising", "peaked", "stable", or "declining"
  posting_frequency: how often top creators post (e.g. "3-5x/day")
  content_format: what performs best ("threads", "images", "video", "polls", "mixed")

Return ONLY the JSON object. No markdown. No other text."""
        
        system = "You are a social media strategist and trend analyst. Return ONLY valid JSON."
        result = self._grok_chat(prompt, system, max_tokens=2000)
        
        try:
            clean = result.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            return NicheProfile(
                name=data.get("name", niche_name),
                description=data.get("description", ""),
                tone=data.get("tone", "engaging"),
                audience=data.get("audience", ""),
                content_pillars=data.get("content_pillars", []),
                hook_patterns=data.get("hook_patterns", []),
                hashtag_pool=data.get("hashtag_pool", []),
                competitors=data.get("competitors", []),
                monetization_angle=data.get("monetization_angle", ""),
                trending_velocity=data.get("trending_velocity", "stable"),
            )
        except Exception as e:
            print(f"[trend_scanner] Deep scan error: {e}")
            return NicheProfile(name=niche_name)

    def schedule_trend_scan(self, interval_minutes: int = 60) -> str:
        """Return a cron schedule string for periodic trend scanning."""
        return f"every {interval_minutes}m"


# ── Character Generator ──────────────────────────────────────────────────────

class CharacterGenerator:
    """Generates Eliza character.json files from niche/trend data."""

    def __init__(self):
        self.output_dir = CHARACTERS_DIR
        self.api_key = XAI_API_KEY
        self.base_url = XAI_BASE_URL

    def _grok_chat(self, prompt: str, system: str = "", max_tokens: int = 2000) -> str:
        if not self.api_key:
            return "{}"
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": "grok-3-mini",
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.8,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                return "{}"
        except Exception as e:
            return f'{{"error":"{e}"}}'

    def generate_from_niche(self, niche: NicheProfile, platform: str = "twitter") -> dict:
        """Generate a complete Eliza character JSON from a niche profile."""
        prompt = f"""Create an ElizaOS character.json for an AI influencer agent in this niche:

NICHE: {niche.name}
DESCRIPTION: {niche.description}
TONE: {niche.tone}
AUDIENCE: {niche.audience}
CONTENT PILLARS: {', '.join(niche.content_pillars)}
HOOK PATTERNS: {', '.join(niche.hook_patterns)}
HASHTAGS: {', '.join(niche.hashtag_pool[:10])}
MONETIZATION: {niche.monetization_angle}

Return a valid ElizaOS character.json with these fields:
  name: catchy agent name (not the niche name)
  modelProvider: "openai"
  clients: ["{platform}"]
  plugins: ["@elizaos/plugin-{platform}"]
  settings: {{ secrets: {{}}, voice: {{ model: "en_US-male-medium" }} }}
  bio: array of 5 short bio lines the agent would say
  lore: array of 4-5 background story elements
  knowledge: array of 6-8 domain-specific facts the agent should know
  postExamples: array of 5 example posts that match the niche's best-performing style
  adjectives: array of 5-6 descriptive adjectives
  topics: array of 8-12 relevant topics
  style: object with "all" (3-4 traits), "chat" (3-4 traits), "post" (3-4 traits) arrays

Make the character feel REAL. Use the hook patterns competitors use. 
Be specific about the niche. No generic AI-sounding language.
The bio should sound like a real person in this niche, not a bot description."""

        system = "You create ElizaOS character files for autonomous AI influencers. Return ONLY valid JSON with no markdown."
        result = self._grok_chat(prompt, system, max_tokens=3000)
        
        try:
            clean = result.replace("```json", "").replace("```", "").strip()
            # Find first { and last }
            start = clean.find("{")
            end = clean.rfind("}")
            if start >= 0 and end > start:
                clean = clean[start:end+1]
            character = json.loads(clean)
            return character
        except Exception as e:
            print(f"[char_gen] Error generating from niche: {e}")
            return self._generate_fallback(niche, platform)

    def _generate_fallback(self, niche: NicheProfile, platform: str) -> dict:
        """Fallback character if AI generation fails."""
        name = niche.name.split()[0].title() if niche.name else "Agent"
        return {
            "name": f"{name}Influencer",
            "modelProvider": "openai",
            "clients": [platform],
            "plugins": [f"@elizaos/plugin-{platform}"],
            "settings": {"secrets": {}, "voice": {"model": "en_US-male-medium"}},
            "bio": [
                f"Creating content about {niche.name}",
                f"Automated {niche.tone} posts in the {niche.name} space",
                f"Data-driven content strategy for {niche.audience}" if niche.audience else "Building in public"
            ],
            "lore": [
                f"Born from trend analysis of {niche.name}",
                f"Trained on top creators in the space"
            ],
            "knowledge": [
                niche.description,
                f"Content pillars: {', '.join(niche.content_pillars[:3])}",
            ],
            "postExamples": [
                f"Hot take in {niche.name}: the landscape is shifting fast",
                f"Thread: Everything I've learned about {niche.name} so far"
            ],
            "adjectives": [niche.tone, "data-driven", "consistent"],
            "topics": niche.content_pillars[:8],
            "style": {
                "all": [f"{niche.tone.title()}", "Engaging", "Consistent"],
                "chat": ["Direct", "Knowledgeable"],
                "post": ["Hook-first", f"{niche.tone.title()}", "Calls to action"]
            }
        }

    def save_character(self, character: dict, filename: str = "") -> str:
        """Save character dict to JSON file. Returns file path."""
        if not filename:
            clean_name = character.get("name", "character").lower().replace(" ", "-")
            filename = f"{clean_name}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(character, f, indent=2)
        print(f"[char_gen] Saved: {filepath}")
        return str(filepath)

    def generate_and_save(self, niche: NicheProfile, platform: str = "twitter") -> str:
        """Generate character from niche and save to file. Returns file path."""
        char = self.generate_from_niche(niche, platform)
        name = char.get("name", niche.name.split()[0]).lower().replace(" ", "-")
        return self.save_character(char, f"{name}.json")


# ── MCP Connector ────────────────────────────────────────────────────────────

class GrokMCP:
    """Direct connector to Grok MCP tools (mcp_grok_*) from within the pipeline.
    
    These tools are available as Hermes MCP tools:
      - mcp_grok_x_search: Search X posts, profiles, threads
      - mcp_grok_web_search: Agentic web search with Grok
      - mcp_grok_chat: Text chat with Grok models
      - mcp_grok_generate_image: Image generation
      - mcp_grok_grok_agent: All-in-one agent with search + code + vision
    """
    
    @staticmethod
    def schedule_grok_agent_job(
        name: str,
        prompt: str,
        schedule: str = "0 */6 * * *",
        system_prompt: str = "",
    ) -> dict:
        """Return a cron job config for a periodic Grok agent scan.
        
        Use with Hermes cronjob tool:
          cronjob(action='create', name=name, prompt=prompt, schedule=schedule, ...)
        """
        return {
            "type": "grok_agent",
            "name": name,
            "prompt": prompt,
            "schedule": schedule,
            "system_prompt": system_prompt,
            "tools": ["x_search", "web_search"],
        }

    @staticmethod
    def trend_to_cron_job(niche_name: str, interval: str = "6h") -> dict:
        """Generate a cron job config that scans a niche and creates content."""
        prompt = f"""Use Grok X search to find trending topics in {niche_name}.
Then:
1. Generate a caption about the top trend
2. Generate an image prompt based on it
3. Post to X

Use: mcp_grok_x_search for trend discovery
Use: mcp_grok_chat for caption/hashtags
Use: image-turbo MCP for the image"""
        
        return {
            "name": f"trend-{niche_name.lower().replace(' ', '-')[:20]}",
            "prompt": prompt,
            "schedule": f"every {interval}",
            "skills": ["social-orchestrator", "xurl"],
        }


# ── Main Pipeline ────────────────────────────────────────────────────────────

def scan_and_generate_characters(count: int = 5, save: bool = True) -> list[str]:
    """Full pipeline: scan trends → generate characters → save files. Returns file paths."""
    scanner = TrendScanner()
    generator = CharacterGenerator()
    
    print(f"[pipeline] Scanning for {count} trending niches...")
    niches = scanner.scan_trending_niches(count=count)
    
    saved = []
    for niche in niches:
        print(f"  → Generating character for: {niche.name} ({niche.trending_velocity})")
        filepath = generator.generate_and_save(niche, platform="twitter")
        saved.append(filepath)
    
    print(f"[pipeline] ✅ Generated {len(saved)} characters")
    return saved


def deep_scan_and_create(niche_name: str) -> str:
    """Deep scan one niche → create character. Returns file path."""
    scanner = TrendScanner()
    generator = CharacterGenerator()
    
    print(f"[pipeline] Deep scanning: {niche_name}")
    niche = scanner.deep_scan_niche(niche_name)
    
    if niche.tone == "engaging" and not niche.content_pillars:
        return f"ERROR: Could not analyze niche '{niche_name}'"
    
    print(f"  Tone: {niche.tone} | Velocity: {niche.trending_velocity}")
    filepath = generator.generate_and_save(niche, platform="twitter")
    return filepath


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        saved = scan_and_generate_characters(count=count)
        for s in saved:
            print(f"  ✅ {s}")
    elif len(sys.argv) > 2 and sys.argv[1] == "deep":
        niche = " ".join(sys.argv[2:])
        result = deep_scan_and_create(niche)
        print(f"  {'✅' if 'ERROR' not in result else '❌'} {result}")
    else:
        print("Usage: python trend_scanner.py scan [count]")
        print("       python trend_scanner.py deep <niche_name>")
