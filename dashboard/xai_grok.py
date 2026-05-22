"""
xai_grok.py — xAI/Grok API integration for the content pipeline.

Wraps the xAI API for:
  - Image generation (grok-imagine-image-quality)
  - Image editing (grok-imagine-image-quality)
  - Video generation (grok-imagine-video, async polling)
  - X posting (via Grok's native X integration)

API docs: https://docs.x.ai/api/mcp
Endpoint: https://api.x.ai/v1

Requires: pip install xai-sdk openai
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

# ── Config ────────────────────────────────────────────────────────────────────

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL_IMAGE = "grok-imagine-image-quality"
XAI_MODEL_VIDEO = "grok-imagine-video"

# Aspect ratios supported by xAI
ASPECT_RATIOS = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
    "widescreen": "16:9",
    "mobile": "9:16",
    "photo": "3:2",
    "banner": "2:1",
    "auto": "auto",
}

# Video durations in seconds
VIDEO_MIN_DURATION = 5
VIDEO_MAX_DURATION = 15
VIDEO_DEFAULT_DURATION = 10

VIDEO_RESOLUTIONS = ["480p", "720p", "1080p"]
VIDEO_DEFAULT_RESOLUTION = "720p"


# ── Data Models ───────────────────────────────────────────────────────────────


@dataclass
class ImageResult:
    """Result from an xAI image generation request."""

    url: str | None = None
    base64: str | None = None
    model: str = XAI_MODEL_IMAGE
    prompt: str = ""
    aspect_ratio: str = "1:1"
    success: bool = True
    error: str | None = None


@dataclass
class VideoResult:
    """Result from an xAI video generation request."""

    url: str | None = None
    model: str = XAI_MODEL_VIDEO
    prompt: str = ""
    duration: int = VIDEO_DEFAULT_DURATION
    aspect_ratio: str = "16:9"
    resolution: str = VIDEO_DEFAULT_RESOLUTION
    request_id: str = ""
    status: str = ""
    success: bool = True
    error: str | None = None


# ── Image Generation ──────────────────────────────────────────────────────────


def generate_image(
    prompt: str,
    *,
    n: int = 1,
    aspect_ratio: str = "1:1",
    model: str = XAI_MODEL_IMAGE,
    api_key: str | None = None,
) -> list[ImageResult]:
    """Generate images using xAI's Grok Imagine API.

    Uses the OpenAI-compatible endpoint: POST /v1/images/generations

    Args:
        prompt: Text description of the image to generate.
        n: Number of images to generate (1-4).
        aspect_ratio: Aspect ratio string (e.g., "1:1", "16:9", "9:16", "auto").
        model: Model name (default: grok-imagine-image-quality).
        api_key: xAI API key. Defaults to XAI_API_KEY env var.

    Returns:
        List of ImageResult objects.
    """
    key = api_key or XAI_API_KEY
    if not key:
        return [ImageResult(success=False, error="XAI_API_KEY not set")]

    # Validate aspect_ratio
    ar = ASPECT_RATIOS.get(aspect_ratio, aspect_ratio)
    if ar not in ASPECT_RATIOS.values() and ar != aspect_ratio:
        # Allow user to pass raw ratio strings
        pass

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": min(max(n, 1), 4),
    }
    if ar:
        payload["aspect_ratio"] = ar

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{XAI_BASE_URL}/images/generations",
                headers=headers,
                json=payload,
            )
            if resp.status_code != 200:
                return [
                    ImageResult(
                        success=False,
                        error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    )
                ]

            data = resp.json()
            results = []
            for item in data.get("data", []):
                results.append(
                    ImageResult(
                        url=item.get("url"),
                        base64=item.get("b64_json"),
                        model=model,
                        prompt=prompt,
                        aspect_ratio=ar,
                    )
                )
            return results

    except Exception as e:
        return [ImageResult(success=False, error=str(e))]


def edit_image(
    prompt: str,
    image_path: str | Path | bytes,
    *,
    model: str = XAI_MODEL_IMAGE,
    api_key: str | None = None,
) -> ImageResult:
    """Edit an image using xAI's Grok Imagine API.

    Uses the OpenAI-compatible endpoint: POST /v1/images/edits

    Args:
        prompt: Description of the edit to apply.
        image_path: Path to the image file, or raw bytes.
        model: Model name.
        api_key: xAI API key.

    Returns:
        ImageResult with the edited image.
    """
    key = api_key or XAI_API_KEY
    if not key:
        return ImageResult(success=False, error="XAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {key}",
    }

    try:
        # Prepare the image
        if isinstance(image_path, bytes):
            image_data = image_path
            filename = "image.png"
        else:
            p = Path(image_path)
            image_data = p.read_bytes()
            filename = p.name

        with httpx.Client(timeout=120) as client:
            files = {
                "image": (filename, image_data, "image/png"),
                "prompt": (None, prompt),
                "model": (None, model),
            }
            resp = client.post(
                f"{XAI_BASE_URL}/images/edits",
                headers=headers,
                files=files,
            )

            if resp.status_code != 200:
                return ImageResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            data = resp.json()
            item = data.get("data", [{}])[0]
            return ImageResult(
                url=item.get("url"),
                base64=item.get("b64_json"),
                model=model,
                prompt=prompt,
            )

    except Exception as e:
        return ImageResult(success=False, error=str(e))


# ── Video Generation ──────────────────────────────────────────────────────────


def generate_video(
    prompt: str,
    *,
    duration: int = VIDEO_DEFAULT_DURATION,
    aspect_ratio: str = "16:9",
    resolution: str = VIDEO_DEFAULT_RESOLUTION,
    model: str = XAI_MODEL_VIDEO,
    api_key: str | None = None,
    poll_interval: int = 5,
    poll_timeout: int = 600,
) -> VideoResult:
    """Generate a video using xAI's Grok video API.

    Uses: POST /v1/videos/generations (async, polls until done)

    Args:
        prompt: Text description of the video.
        duration: Video duration in seconds (5-15).
        aspect_ratio: Aspect ratio (e.g., "16:9", "9:16").
        resolution: "480p", "720p", or "1080p".
        model: Model name.
        api_key: xAI API key.
        poll_interval: Seconds between status polls.
        poll_timeout: Max seconds to wait for completion.

    Returns:
        VideoResult with the video URL.
    """
    key = api_key or XAI_API_KEY
    if not key:
        return VideoResult(success=False, error="XAI_API_KEY not set")

    # Validate params
    duration = max(VIDEO_MIN_DURATION, min(duration, VIDEO_MAX_DURATION))
    if resolution not in VIDEO_RESOLUTIONS:
        resolution = VIDEO_DEFAULT_RESOLUTION

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }

    try:
        with httpx.Client(timeout=30) as client:
            # Submit the video generation request
            resp = client.post(
                f"{XAI_BASE_URL}/videos/generations",
                headers=headers,
                json=payload,
            )
            if resp.status_code != 200:
                return VideoResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            data = resp.json()
            request_id = data.get("request_id", "")
            if not request_id:
                return VideoResult(
                    success=False,
                    error="No request_id in response",
                )

            # Poll until ready
            start = time.time()
            while time.time() - start < poll_timeout:
                poll_resp = client.get(
                    f"{XAI_BASE_URL}/videos/{request_id}",
                    headers={"Authorization": headers["Authorization"]},
                )
                if poll_resp.status_code != 200:
                    return VideoResult(
                        request_id=request_id,
                        success=False,
                        error=f"Poll HTTP {poll_resp.status_code}",
                    )

                poll_data = poll_resp.json()
                status = poll_data.get("status", "")

                if status == "done":
                    video_url = ""
                    video_data = poll_data.get("video", {})
                    if isinstance(video_data, dict):
                        video_url = video_data.get("url", "")
                    elif isinstance(video_data, str):
                        video_url = video_data

                    return VideoResult(
                        url=video_url,
                        request_id=request_id,
                        status="done",
                        duration=duration,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                    )

                elif status in ("expired", "failed"):
                    error_msg = poll_data.get("error", status)
                    return VideoResult(
                        request_id=request_id,
                        status=status,
                        success=False,
                        error=error_msg,
                    )

                time.sleep(poll_interval)

            return VideoResult(
                request_id=request_id,
                status="timeout",
                success=False,
                error=f"Timed out after {poll_timeout}s",
            )

    except Exception as e:
        return VideoResult(success=False, error=str(e))


# ── Download Helpers ──────────────────────────────────────────────────────────


def download_to_file(
    url: str,
    output_dir: str | Path = "/tmp/grok-outputs",
    filename: str | None = None,
) -> Path | None:
    """Download a generated image/video to a local file.

    Args:
        url: The URL from xAI API.
        output_dir: Directory to save to.
        filename: Custom filename (auto-derived from URL if not set).

    Returns:
        Path to the downloaded file, or None on failure.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not filename:
        # Derive from URL
        ext = Path(url.split("?")[0]).suffix or ".bin"
        filename = f"grok_{int(time.time())}{ext}"

    filepath = out / filename

    try:
        with httpx.Client(follow_redirects=True, timeout=120) as client:
            resp = client.get(url)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
        return filepath
    except Exception as e:
        print(f"[xai_grok] Download failed: {e}")
        return None


# ── CLI Test ──────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python xai_grok.py <prompt> [--video] [--ar 16:9] [--n 2]")
        sys.exit(1)

    prompt = sys.argv[1]
    is_video = "--video" in sys.argv
    ar = "16:9" if "--ar" not in sys.argv else sys.argv[sys.argv.index("--ar") + 1]
    n = 4 if "--n" not in sys.argv else int(sys.argv[sys.argv.index("--n") + 1])

    if is_video:
        print(f"🎬 Generating video: {prompt}")
        result = generate_video(prompt, aspect_ratio=ar, duration=10)
        if result.success:
            print(f"✅ Video URL: {result.url}")
            local = download_to_file(result.url)
            if local:
                print(f"📁 Saved to: {local}")
        else:
            print(f"❌ Failed: {result.error}")
    else:
        print(f"🖼 Generating {n} images: {prompt}")
        results = generate_image(prompt, n=n, aspect_ratio=ar)
        for i, img in enumerate(results):
            if img.success:
                print(f"  [{i+1}] ✅ {img.url}")
                local = download_to_file(img.url)
                if local:
                    print(f"      📁 {local}")
            else:
                print(f"  [{i+1}] ❌ {img.error}")
