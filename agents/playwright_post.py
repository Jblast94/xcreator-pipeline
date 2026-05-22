#!/usr/bin/env python3
"""playwright_post.py — Post to X via browser automation.

Acts as a human user: logs into X, writes a tweet, posts it.
No API keys needed. Uses saved cookies for persistent sessions.

Usage:
  # Save cookies first (one-time):
  python3 playwright_post.py --login --handle jblast94 --cookies /root/.x-cookies-jblast.json
  
  # Post:
  python3 playwright_post.py --handle jblast94 --text "Hello world" [--media photo.png]
  
  # Post thread:
  python3 playwright_post.py --handle jblast94 --thread "Tweet 1" "Tweet 2" "Tweet 3"
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

X_URL = "https://x.com"


def login(handle: str, cookies_file: str):
    """Interactive login — saves cookies for later use."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(f"{X_URL}/login")
        print(f"\n🔐 Log in as @{handle} in the browser window.")
        print("   Complete the login, then press ENTER here to save cookies.\n")
        input("   Press ENTER after logging in... ")
        
        context.storage_state(path=cookies_file)
        print(f"✅ Cookies saved to {cookies_file}")
        browser.close()


def post(handle: str, text: str, cookies_file: str, media_file: str = "", headless: bool = True):
    """Post a tweet using saved cookies."""
    if not Path(cookies_file).exists():
        return {"error": f"Cookies not found at {cookies_file}. Run --login first."}

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=cookies_file)
        page = context.new_page()
        
        # Go to X and wait for it to load
        page.goto(X_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Handle any popups
        dismissals = [
            'button[data-testid="xMigrationMigration"]',
            'button[aria-label="Close"]',
            'div[data-testid="sheetDialog"] button',
        ]
        for sel in dismissals:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    time.sleep(1)
            except Exception:
                pass

        # Click the tweet compose area
        tweet_area = None
        selectors = [
            'div[data-testid="tweetTextarea_0"]',
            'div[data-testid="tweetTextarea_0"] div[contenteditable="true"]',
            'div.public-DraftStyleDefault-block',
            'div[role="textbox"]',
        ]
        
        for sel in selectors:
            try:
                tweet_area = page.locator(sel).first
                if tweet_area.is_visible(timeout=5000):
                    break
            except Exception:
                continue

        if not tweet_area:
            # Maybe click the "Post" button first
            try:
                post_btn = page.locator('a[data-testid="SideNav_NewTweet_Button"]').first
                if post_btn.is_visible(timeout=3000):
                    post_btn.click()
                    time.sleep(2)
                    tweet_area = page.locator('div[data-testid="tweetTextarea_0"]').first
            except Exception:
                pass

        if not tweet_area:
            browser.close()
            return {"error": "Could not find tweet compose area. Login may have expired."}

        tweet_area.click()
        time.sleep(1)
        tweet_area.fill(text)
        time.sleep(1)

        # Upload media if provided
        if media_file and Path(media_file).exists():
            try:
                file_input = page.locator('input[data-testid="fileInput"]')
                if file_input.is_hidden():
                    # Click the media button first
                    media_btn = page.locator('div[data-testid="attachmentsButton"]').first
                    if media_btn.is_visible(timeout=3000):
                        media_btn.click()
                        time.sleep(1)
                file_input.set_input_files(media_file)
                time.sleep(3)  # Wait for upload
            except Exception as e:
                print(f"  ⚠️ Media upload: {e}")

        # Click the Post button
        post_selectors = [
            'div[data-testid="tweetButton"]',
            'button[data-testid="tweetButton"]',
            'div[data-testid="tweetButtonInline"]',
        ]
        
        posted = False
        for sel in post_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    time.sleep(3)
                    posted = True
                    break
            except Exception:
                continue

        browser.close()

        if posted:
            return {"success": True, "text": text[:50]}
        else:
            return {"error": "Could not find Post button"}


def post_thread(handle: str, tweets: list[str], cookies_file: str, headless: bool = True):
    """Post a thread (first tweet + replies)."""
    results = []
    
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=cookies_file)
        page = context.new_page()
        
        page.goto(X_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        for i, text in enumerate(tweets):
            # Click "Post" for first tweet, "Reply" for subsequent
            if i == 0:
                post_btn_sel = 'a[data-testid="SideNav_NewTweet_Button"]'
            else:
                post_btn_sel = f'a[href="/{handle}/status/{results[-1].get("tweet_id","")}"]' if results else 'a[data-testid="SideNav_NewTweet_Button"]'
            
            # Post the tweet
            try:
                # Click compose
                if i == 0:
                    btn = page.locator(post_btn_sel).first
                    if btn.is_visible():
                        btn.click()
                        time.sleep(2)

                # Find text area
                ta = page.locator('div[data-testid="tweetTextarea_0"]').first
                ta.click()
                ta.fill(text)
                time.sleep(1)

                # Click post
                post_btn = page.locator('div[data-testid="tweetButton"]').first
                post_btn.click()
                time.sleep(3)
                results.append({"success": True, "tweet_num": i + 1})
            except Exception as e:
                results.append({"error": str(e)[:100], "tweet_num": i + 1})
                break

        browser.close()
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post to X via browser automation")
    parser.add_argument("--handle", required=True, help="X handle (without @)")
    parser.add_argument("--text", help="Tweet text")
    parser.add_argument("--thread", nargs="+", help="Thread tweets")
    parser.add_argument("--media", help="Media file path")
    parser.add_argument("--cookies", default="", help="Cookies file path")
    parser.add_argument("--login", action="store_true", help="Save cookies (interactive login)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")

    args = parser.parse_args()
    cookies_file = args.cookies or f"/root/.x-cookies-{args.handle}.json"

    if args.login:
        login(args.handle, cookies_file)
        sys.exit(0)

    if args.thread:
        result = post_thread(args.handle, args.thread, cookies_file, headless=args.headless)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if not args.text:
        print("Need --text or --thread")
        sys.exit(1)

    result = post(args.handle, args.text, cookies_file, args.media or "", headless=args.headless)
    print(json.dumps(result, indent=2))
