"""content_gen.py — Content generation engine using free HF Spaces (no xAI image cost).

Backends:
  - Z-Image-Turbo (HF Space via MCP) — fast free image gen
  - FireRed Edit (HF Space via MCP) — image editing/refinement
  - Grok Chat (xAI text API) — captions, hooks, threads (text-only, cheap)

All images saved to /mnt/storage/comfy/output/ (central SeaweedFS).
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import httpx

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(os.environ.get("PIPELINE_OUTPUT_DIR", "/mnt/storage/comfy/output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
if not XAI_API_KEY:
    # Try to load from Hermes config
    try:
        import yaml
        cfg_path = Path.home() / ".hermes" / "config.yaml"
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text())
            XAI_API_KEY = cfg.get("XAI_API_KEY", "")
    except Exception:
        pass
if not XAI_API_KEY:
    # Try Hermes .env
    try:
        env_path = Path.home() / ".hermes" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("XAI_API_KEY=") and not line.startswith("XAI_API_KEY=***"):
                    XAI_API_KEY = line.split("=", 1)[1].strip()
    except Exception:
        pass
XAI_BASE_URL = "https://api.x.ai/v1"

# HF Space URLs
TURBO_SPACE = "https://jblast94-z-image-turbo.hf.space"
FIREED_SPACE = "https://jblast94-firered-image-edit-1-0-fast.hf.space"

HF_TOKEN = os.environ.get("HF_TOKEN", "")


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class ContentPiece:
    """A single piece of generated content."""
    id: str = ""
    image_url: str | None = None  # Remote URL
    image_path: str | None = None  # Local path
    caption: str = ""
    hook: str = ""  # Short hook (≤280 chars)
    thread: list[str] = field(default_factory=list)  # Multi-tweet thread
    hashtags: str = ""
    platform_ready: dict = field(default_factory=dict)  # {platform: adapted_text}
    created_at: str = ""
    backend: str = ""


@dataclass 
class GenerationResult:
    """Result from a generation request."""
    success: bool = True
    error: str | None = None
    content: ContentPiece | None = None
    images: list[str] = field(default_factory=list)  # URLs


# ── Image Generation (HF Spaces) ──────────────────────────────────────────────

def generate_image_turbo(
    prompt: str,
    *,
    width: int = 1024,
    height: int = 1024,
    seed: int = -1,
    steps: int = 9,
) -> GenerationResult:
    """Generate image via Z-Image-Turbo HF Space (free).
    
    Gradio API schema (fn_index=2):
      inputs: [prompt (textbox), height (slider), width (slider), steps (slider), seed (number), randomize_seed (checkbox)]
      outputs: [image (image), seed_used (number)]
    """
    try:
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        session_hash = str(uuid.uuid4())
        fn_index = 2  # generate_image endpoint
        
        # Input order: prompt, height, width, steps, seed, randomize_seed
        randomize = seed <= 0
        data = [prompt, height, width, steps, max(seed, 1), not randomize]

        payload = {
            "data": data,
            "fn_index": fn_index,
            "session_hash": session_hash,
        }

        with httpx.Client(timeout=120) as client:
            # Join queue
            resp = client.post(
                f"{TURBO_SPACE}/gradio_api/queue/join",
                json=payload,
                headers={**headers, "Content-Type": "application/json"},
            )
            if resp.status_code != 200:
                return GenerationResult(success=False, error=f"Queue join failed: {resp.text[:200]}")

            # Stream result
            event_resp = client.get(
                f"{TURBO_SPACE}/gradio_api/queue/data",
                params={"session_hash": session_hash},
                headers=headers,
                timeout=120,
            )

            for line in event_resp.text.split("\n"):
                if line.startswith("data:"):
                    import json
                    try:
                        data = json.loads(line[5:].strip())
                        if data.get("msg") == "process_completed":
                            output = data.get("output", {}).get("data", [])
                            if output and isinstance(output[0], dict) and output[0].get("url"):
                                img_url = output[0]["url"]
                                # Download to local storage
                                local = _download_image(img_url)
                                return GenerationResult(
                                    success=True,
                                    content=ContentPiece(
                                        id=session_hash[:8],
                                        image_url=img_url,
                                        image_path=str(local) if local else None,
                                        created_at=datetime.now().isoformat(),
                                        backend="image-turbo",
                                    ),
                                    images=[img_url],
                                )
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

        return GenerationResult(success=False, error="No image in response")

    except Exception as e:
        return GenerationResult(success=False, error=str(e))


def edit_image_firered(
    prompt: str,
    image_url: str | None = None,
    image_b64: str | None = None,
) -> GenerationResult:
    """Edit/refine image via FireRed Edit HF Space (free)."""
    try:
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        session_hash = str(uuid.uuid4())
        images_data = []
        if image_b64:
            images_data.append(image_b64)

        payload = {
            "data": [prompt, images_data],
            "fn_index": 0,
            "session_hash": session_hash,
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{FIREED_SPACE}/gradio_api/queue/join",
                json=payload,
                headers={**headers, "Content-Type": "application/json"},
            )
            if resp.status_code != 200:
                return GenerationResult(success=False, error=f"FireRed queue failed: {resp.text[:200]}")

            event_resp = client.get(
                f"{FIREED_SPACE}/gradio_api/queue/data",
                params={"session_hash": session_hash},
                headers=headers,
                timeout=120,
            )

            for line in event_resp.text.split("\n"):
                if line.startswith("data:"):
                    import json
                    try:
                        data = json.loads(line[5:].strip())
                        if data.get("msg") == "process_completed":
                            output = data.get("output", {}).get("data", [])
                            if output and isinstance(output[0], dict) and output[0].get("url"):
                                img_url = output[0]["url"]
                                local = _download_image(img_url)
                                return GenerationResult(
                                    success=True,
                                    content=ContentPiece(
                                        id=session_hash[:8],
                                        image_url=img_url,
                                        image_path=str(local) if local else None,
                                        created_at=datetime.now().isoformat(),
                                        backend="firered-edit",
                                    ),
                                    images=[img_url],
                                )
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

        return GenerationResult(success=False, error="No edited image in response")

    except Exception as e:
        return GenerationResult(success=False, error=str(e))


# ── Text Generation (Grok Chat — text only, cheap) ───────────────────────────

def generate_caption(
    topic: str,
    *,
    platform: str = "twitter",
    tone: str = "engaging",
    length: str = "short",
) -> str:
    """Generate a caption/hook using Grok chat (text-only, minimal cost)."""
    if not XAI_API_KEY:
        return f"[Set XAI_API_KEY] {topic}"

    platform_guide = {
        "twitter": "Max 280 chars. Punchy hook. 1-2 hashtags max. End with CTA or question.",
        "instagram": "Visual-first caption. 150-200 words. 10-15 hashtags. Storytelling hook.",
        "tiktok": "Gen-Z tone. Short, snappy. 100-150 chars caption. Trendy language.",
        "onlyfans": "Teasing, intimate tone. Build anticipation. Call-to-action for DMs.",
        "telegram": "Markdown supported. Can be longer. No hashtag limit. Professional yet casual.",
    }

    guide = platform_guide.get(platform, platform_guide["twitter"])
    length_guide = "Keep it under 280 chars." if length == "short" else "Write a full caption, 100-200 chars."

    system = f"""You are a social media copywriter. {guide} {length_guide}
Tone: {tone}. Do NOT use generic AI phrases like "In today's world" or "Unlock the power of".
Be specific, conversational, and platform-native."""

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {XAI_API_KEY}",
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Write a {platform} post about: {topic}"},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.8,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            return f"[API error {resp.status_code}]"
    except Exception as e:
        return f"[Error: {e}]"


def make_thread(
    topic: str,
    num_tweets: int = 5,
) -> list[str]:
    """Generate a Twitter thread using Grok chat."""
    if not XAI_API_KEY:
        return [f"[Set XAI_API_KEY] Thread about {topic}"]

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {XAI_API_KEY}",
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You create viral Twitter threads. Rules:
- Each tweet ≤ 280 chars
- First tweet is a hook that stops the scroll
- Last tweet has a CTA (follow, RT, link)
- No generic AI phrases
- Number each tweet: 1/ {num_tweets}, 2/ {num_tweets}, etc.
- Return ONLY the tweets, one per line, no extra text""",
                        },
                        {"role": "user", "content": f"Create a {num_tweets}-tweet thread about: {topic}"},
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.85,
                },
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                # Parse numbered tweets
                tweets = []
                for line in text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("Here") and not line.startswith("Thread"):
                        # Strip leading number pattern like "1/" or "1."
                        tweets.append(line)
                return tweets[:num_tweets] if tweets else [text]
            return [f"[API error {resp.status_code}]"]
    except Exception as e:
        return [f"[Error: {e}]"]


def generate_hashtags(topic: str, count: int = 10) -> str:
    """Generate relevant hashtags using Grok chat."""
    if not XAI_API_KEY:
        return "#content #viral"

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {XAI_API_KEY}",
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": f"Return {count} relevant hashtags, comma-separated, no explanation."},
                        {"role": "user", "content": f"Hashtags for: {topic}"},
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return "#content"


# ── One-Click Content Factory ────────────────────────────────────────────────

def create_content_piece(
    topic: str,
    *,
    image_prompt: str = "",
    platform: str = "twitter",
    tone: str = "engaging",
    generate_thread: bool = False,
    width: int = 1024,
    height: int = 1024,
) -> ContentPiece:
    """One-click: topic → image + caption (and optionally thread).
    
    Uses free HF Spaces for images, Grok text-only for captions.
    """
    piece = ContentPiece(
        id=uuid.uuid4().hex[:8],
        created_at=datetime.now().isoformat(),
        backend="pipeline",
    )

    # 1. Generate image (free HF Space)
    prompt = image_prompt or topic
    img_result = generate_image_turbo(prompt, width=width, height=height)
    if img_result.success and img_result.content:
        piece.image_url = img_result.content.image_url
        piece.image_path = img_result.content.image_path
        piece.backend = "image-turbo"
    else:
        piece.backend = "text-only"

    # 2. Generate caption
    piece.caption = generate_caption(topic, platform=platform, tone=tone)

    # 3. Generate hook (≤280 chars)
    piece.hook = generate_caption(topic, platform="twitter", tone=tone, length="short")
    if len(piece.hook) > 280:
        piece.hook = piece.hook[:277] + "..."

    # 4. Generate hashtags
    piece.hashtags = generate_hashtags(topic)

    # 5. Generate thread if requested
    if generate_thread:
        piece.thread = make_thread(topic)

    # 6. Adapt for platforms
    for p in ["twitter", "instagram", "tiktok", "telegram"]:
        piece.platform_ready[p] = generate_caption(topic, platform=p, tone=tone)

    return piece


# ── Helpers ───────────────────────────────────────────────────────────────────

def _download_image(url: str) -> Path | None:
    """Download image to central output dir."""
    try:
        ts = int(time.time())
        ext = ".png"
        if ".jpg" in url or ".jpeg" in url:
            ext = ".jpg"
        elif ".webp" in url:
            ext = ".webp"

        filepath = OUTPUT_DIR / f"pipeline_{ts}{ext}"
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            resp = client.get(url)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
        return filepath
    except Exception as e:
        print(f"[content_gen] Download failed: {e}")
        return None


def list_recent_outputs(limit: int = 20) -> list[dict]:
    """List recent generated files from output dir."""
    if not OUTPUT_DIR.exists():
        return []
    files = sorted(OUTPUT_DIR.glob("pipeline_*"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [
        {
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        }
        for f in files[:limit]
    ]
