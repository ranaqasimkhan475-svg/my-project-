"""
Auto Image Generator + Facebook Poster
----------------------------------------
Har run par ye script:
1. prompts.txt se ek random prompt uthata hai
2. Pollinations.ai (free, no API key) se ek AI image generate karta hai
3. Wo image FB_PAGES secret mein di gayi har Facebook Page par post karta hai

Ye script GitHub Actions ke zariye har ghante automatically chalega.
"""

import os
import json
import random
import time
import urllib.parse
import requests

PROMPTS_FILE = "prompts.txt"
GRAPH_API_VERSION = "v19.0"


def load_prompts():
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]
    if not prompts:
        raise SystemExit("prompts.txt khali hai — kam az kam ek prompt add karein.")
    return prompts


def build_image_url(prompt: str) -> str:
    """Pollinations.ai free image generation URL banata hai."""
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 1_000_000)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&seed={seed}&nologo=true"
    )


def post_to_page(page_id: str, access_token: str, image_url: str, caption: str):
    endpoint = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/photos"
    payload = {
        "url": image_url,
        "caption": caption,
        "access_token": access_token,
    }
    return requests.post(endpoint, data=payload, timeout=60)


def main():
    pages_json = os.environ.get("FB_PAGES")
    if not pages_json:
        raise SystemExit(
            "FB_PAGES secret set nahi hai. GitHub repo Settings > Secrets mein add karein."
        )

    try:
        pages = json.loads(pages_json)
    except json.JSONDecodeError:
        raise SystemExit("FB_PAGES secret sahi JSON format mein nahi hai.")

    prompts = load_prompts()
    prompt = random.choice(prompts)
    image_url = build_image_url(prompt)
    caption = f"{prompt}\n\n#AIart #DailyPost"

    print(f"Selected prompt: {prompt}")
    print(f"Image URL: {image_url}")

    for page in pages:
        page_id = page.get("id")
        token = page.get("token")
        name = page.get("name", page_id)

        if not page_id or not token:
            print(f"Skipping invalid page entry: {page}")
            continue

        resp = post_to_page(page_id, token, image_url, caption)

        if resp.status_code == 200:
            print(f"[OK] Posted to {name}")
        else:
            print(f"[FAIL] {name} -> {resp.status_code}: {resp.text}")

        time.sleep(3)  # rate-limit ke liye thoda gap


if __name__ == "__main__":
    main()
