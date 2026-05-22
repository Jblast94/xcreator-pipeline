"""x_poster.py — Post to X via API (xurl) or browser automation (Playwright).

Two modes:
  API mode:  Uses xurl CLI with X Premium API credentials
  Browser:   Uses Playwright to post as a human (no API key needed)

Supports multiple accounts and media upload.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Config ───────────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

XURL_BIN = "xurl"
PLAYWRIGHT_SCRIPT = str(Path(__file__).parent / "playwright_post.py")


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class PostResult:
    """Result of posting to X."""
    success: bool = True
    tweet_id: str = ""
    tweet_url: str = ""
    error: str = ""
    method: str = ""  # "api" or "browser"
    account: str = ""
    posted_at: str = ""


@dataclass
class XAccount:
    """An X account with posting capability."""
    handle: str
    app_name: str  # xurl app name (e.g. "jblast", "bbj4t")
    method: str = "api"  # "api" or "browser"
    cookies_file: str = ""  # Playwright cookies file (browser mode)
    premium: bool = True
    notes: str = ""


# ── Account Registry ────────────────────────────────────────────────────────

ACCOUNTS = {
    "jblast94": XAccount(
        handle="@jblast94",
        app_name="jblast",
        method="api",
        premium=True,
        notes="X Premium — primary account",
    ),
    "bbj4t": XAccount(
        handle="@bbj4t",
        app_name="bbj4t",
        method="api",
        premium=True,
        notes="X Premium — secondary account",
    ),
}


def get_account(handle_or_app: str) -> XAccount | None:
    """Get account config by handle or app name."""
    for key, acct in ACCOUNTS.items():
        if key == handle_or_app or acct.app_name == handle_or_app or acct.handle == handle_or_app:
            return acct
    return None


# ── API Mode (xurl) ─────────────────────────────────────────────────────────

def post_via_xurl(account: XAccount, text: str, media_path: str = "") -> PostResult:
    """Post via xurl CLI. Requires xurl to be authenticated for this account."""
    result = PostResult(method="api", account=account.handle)

    try:
        # Check xurl auth status first
        status_check = subprocess.run(
            [XURL_BIN, "auth", "status"],
            capture_output=True, text=True, timeout=15,
        )
        
        if account.app_name not in status_check.stdout:
            return PostResult(
                success=False,
                error=f"xurl app '{account.app_name}' not authenticated. Run: xurl auth apps add {account.app_name} --client-id ... && xurl auth oauth2 --app {account.app_name} {account.handle}",
                method="api",
                account=account.handle,
            )

        # Build command
        cmd = [XURL_BIN, "--app", account.app_name, "post", text]
        
        if media_path:
            # Upload media first, then post with media-id
            media_result = subprocess.run(
                [XURL_BIN, "--app", account.app_name, "media", "upload", media_path],
                capture_output=True, text=True, timeout=60,
            )
            if media_result.returncode == 0:
                try:
                    media_data = json.loads(media_result.stdout)
                    media_id = media_data.get("data", {}).get("media_id_string", "")
                    if media_id:
                        cmd.extend(["--media-id", media_id])
                except (json.JSONDecodeError, KeyError):
                    pass

        # Post
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
                tweet_id = data.get("data", {}).get("id", "")
                result.tweet_id = tweet_id
                result.tweet_url = f"https://x.com/{account.handle}/{tweet_id}"
                result.success = True
            except json.JSONDecodeError:
                result.success = True
                result.tweet_id = "unknown"
                result.tweet_url = f"https://x.com/{account.handle}/status/unknown"
        else:
            error_text = proc.stderr or proc.stdout
            result.error = f"xurl error: {error_text[:200]}"
            result.success = False

    except FileNotFoundError:
        result.error = "xurl not installed. Run: curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash"
        result.success = False
    except subprocess.TimeoutExpired:
        result.error = "xurl timed out"
        result.success = False
    except Exception as e:
        result.error = str(e)[:200]
        result.success = False

    result.posted_at = datetime.now().isoformat()
    _log(result)
    return result


# ── Browser Mode (Playwright) ──────────────────────────────────────────────

def post_via_browser(account: XAccount, text: str, media_path: str = "") -> PostResult:
    """Post via Playwright browser automation. No API key needed."""
    result = PostResult(method="browser", account=account.handle)

    try:
        cmd = ["python3", PLAYWRIGHT_SCRIPT, 
               "--handle", account.handle.lstrip("@"),
               "--text", text,
               "--cookies", account.cookies_file or f"/root/.x-cookies-{account.app_name}.json"]

        if media_path:
            cmd.extend(["--media", media_path])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
                result.tweet_id = data.get("tweet_id", "")
                result.tweet_url = data.get("tweet_url", "")
                result.success = True
            except json.JSONDecodeError:
                result.success = True
        else:
            result.error = f"Browser error: {proc.stderr[:300]}"
            result.success = False

    except Exception as e:
        result.error = str(e)[:200]
        result.success = False

    result.posted_at = datetime.now().isoformat()
    _log(result)
    return result


# ── Unified Poster ─────────────────────────────────────────────────────────

def post(
    text: str,
    account: str = "jblast94",
    media_path: str = "",
    method: str = "",  # "auto", "api", "browser"
) -> PostResult:
    """Post to X. Auto-selects API or browser based on account config."""
    acct = get_account(account)
    if not acct:
        return PostResult(success=False, error=f"Unknown account: {account}")

    if not method:
        method = acct.method

    if method == "api":
        return post_via_xurl(acct, text, media_path)
    elif method == "browser":
        return post_via_browser(acct, text, media_path)
    else:
        return PostResult(success=False, error=f"Unknown method: {method}")


def post_thread(
    tweets: list[str],
    account: str = "jblast94",
    media_paths: list[str] | None = None,
) -> list[PostResult]:
    """Post a thread. First tweet is the hook, rest are replies."""
    results = []

    for i, text in enumerate(tweets):
        media = (media_paths or [""])[i] if media_paths and i < len(media_paths) else ""
        result = post(text, account=account, media_path=media)
        results.append(result)
        
        if not result.success:
            break
        
        # Brief pause between tweets
        time.sleep(2)

    return results


# ── Helpers ─────────────────────────────────────────────────────────────────

def _log(result: PostResult):
    """Log post result to file."""
    log_file = LOG_DIR / f"x-posts-{datetime.now().strftime('%Y-%m-%d')}.log"
    entry = {
        "time": result.posted_at,
        "account": result.account,
        "method": result.method,
        "success": result.success,
        "tweet_id": result.tweet_id,
        "error": result.error,
    }
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Setup Helpers ──────────────────────────────────────────────────────────

def check_setup() -> dict:
    """Check what's configured and what's missing."""
    status = {
        "xurl_installed": False,
        "xurl_authed": [],
        "playwright_installed": False,
        "accounts_ready": [],
    }

    # Check xurl
    try:
        result = subprocess.run([XURL_BIN, "--help"], capture_output=True, timeout=5)
        status["xurl_installed"] = result.returncode == 0
    except FileNotFoundError:
        pass

    if status["xurl_installed"]:
        try:
            result = subprocess.run([XURL_BIN, "auth", "status"], capture_output=True, text=True, timeout=5)
            for name, acct in ACCOUNTS.items():
                if acct.app_name in result.stdout:
                    status["xurl_authed"].append(name)
        except Exception:
            pass

    # Check playwright
    try:
        result = subprocess.run(["python3", "-m", "playwright", "--version"], capture_output=True, timeout=5)
        status["playwright_installed"] = result.returncode == 0
    except Exception:
        pass

    # Determine ready accounts
    for name, acct in ACCOUNTS.items():
        if acct.method == "api" and name in status["xurl_authed"]:
            status["accounts_ready"].append(name)
        elif acct.method == "browser" and Path(acct.cookies_file).exists():
            status["accounts_ready"].append(name)

    return status


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python x_poster.py <account> <text> [--media path]")
        print("       python x_poster.py --check")
        sys.exit(1)

    if sys.argv[1] == "--check":
        status = check_setup()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    account = sys.argv[1]
    text = " ".join(sys.argv[2:])
    media = ""
    
    if "--media" in sys.argv:
        idx = sys.argv.index("--media")
        media = sys.argv[idx + 1]

    result = post(text, account=account, media_path=media)
    print(json.dumps({
        "success": result.success,
        "tweet_url": result.tweet_url,
        "error": result.error,
        "method": result.method,
        "account": result.account,
    }, indent=2))
