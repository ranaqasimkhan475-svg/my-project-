"""
Auto Image Generator + Facebook Poster (per-page themed content)
------------------------------------------------------------------
Har Page ka apna content set hai:
  - "Sweet Usa"  -> content_places.txt   (famous US places)
  - "imanexis"   -> content_stadiums.txt (iconic football stadiums)

Har line format: "image prompt | caption text"

Har run par har Page ke liye ek random line uske apne content file
se select hoti hai, image generate hoti hai, aur us Page par post hoti hai.
"""

import os
import json
import random
import time
import urllib.parse
import requests

GRAPH_API_VERSION = "v19.0"

# Page name (case-insensitive substring match) -> content file
CONTENT_FILES = {
    "sweet usa": "content_places.txt",
    "imanexis": "content_stadiums.txt",
}
DEFAULT_CONTENT_FILE = "content_places.txt"


def load_content(file_path):
    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                prompt, caption = line.split("|", 1)
                entries.append((prompt.strip(), caption.strip()))
    if not entries:
        raise SystemExit(f"{file_path} mein koi valid entry nahi mili.")
    return entries


def pick_content_file(page_name: str) -> str:
    name_lower = (page_name or "").lower()
    for key, file_path in CONTENT_FILES.items():
        if key in name_lower:
            return file_path
    return DEFAULT_CONTENT_FILE


def build_image_url(prompt: str) -> str:
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

    for page in pages:
        page_id = page.get("id")
        token = page.get("token")
        name = page.get("name", page_id)

        if not page_id or not token:
            print(f"Skipping invalid page entry: {page}")
            continue

        content_file = pick_content_file(name)
        entries = load_content(content_file)
        prompt, caption = random.choice(entries)
        image_url = build_image_url(prompt)

        print(f"[{name}] content file: {content_file}")
        print(f"[{name}] prompt: {prompt}")
        print(f"[{name}] image URL: {image_url}")

        resp = post_to_page(page_id, token, image_url, caption)

        if resp.status_code == 200:
            print(f"[OK] Posted to {name}")
        else:
            print(f"[FAIL] {name} -> {resp.status_code}: {resp.text}")

        time.sleep(3)  # rate-limit ke liye thoda gap


if __name__ == "__main__":
    main()
