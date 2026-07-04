"""
Auto Image Generator + Facebook Poster (per-page themed content)
------------------------------------------------------------------
Har Page ka apna content set hai:
  - "Sweet Usa"  -> content_places.txt   (famous US places)
  - "imanexis"   -> content_stadiums.txt (iconic football stadiums)

Har line format: "image prompt | caption text"

Ab har page ke liye ek "state.json" file track karti hai ke kaunsi
lines already use ho chuki hain, taake repeat na ho jab tak sab
lines use na ho jayen (phir dobara shuffle hota hai).

Image bhi ab pehle download hoti hai (retry ke sath), phir actual
file Facebook ko upload hoti hai (URL ke bajaye) - taake transient
"missing image" errors permanently theek ho jayen.
"""

import os
import json
import random
import time
import urllib.parse
import requests

GRAPH_API_VERSION = "v19.0"

CONTENT_FILES = {
    "sweet usa": "content_places.txt",
    "imanexis": "content_stadiums.txt",
}
DEFAULT_CONTENT_FILE = "content_places.txt"

STATE_FILE = "state.json"


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


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def pick_unused_entry(page_key: str, entries, state):
    """Ek unused (prompt, caption) chunta hai. Agar sab use ho gaye
    hon to reset karke dobara shuffle karta hai."""
    used = set(state.get(page_key, []))
    total = len(entries)

    unused_indices = [i for i in range(total) if i not in used]

    if not unused_indices:
        # Sab use ho chuke, reset karo
        used = set()
        unused_indices = list(range(total))

    chosen_index = random.choice(unused_indices)
    used.add(chosen_index)
    state[page_key] = list(used)

    return entries[chosen_index]


def build_image_url(prompt: str) -> str:
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 1_000_000)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&seed={seed}&nologo=true"
    )


def download_image_with_retry(image_url, max_retries=5, wait_seconds=6):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 1000:
                print(f"[OK] Image downloaded (attempt {attempt})")
                return resp.content
            print(f"[RETRY] attempt {attempt}: bad response status={resp.status_code}")
        except Exception as e:
            print(f"[RETRY] attempt {attempt}: download error - {e}")

        if attempt < max_retries:
            time.sleep(wait_seconds)

    print("[FAIL] Image download failed after all retries")
    return None


def post_to_page(page_id: str, access_token: str, image_bytes: bytes, caption: str, max_retries=3):
    endpoint = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/photos"
    files = {"source": ("image.jpg", image_bytes)}
    data = {"caption": caption, "access_token": access_token}

    for attempt in range(1, max_retries + 1):
        resp = requests.post(endpoint, data=data, files=files, timeout=60)
        if resp.status_code == 200:
            return resp
        print(f"[RETRY] post attempt {attempt} failed: {resp.text}")
        time.sleep(5)

    return resp


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

    state = load_state()

    for page in pages:
        page_id = page.get("id")
        token = page.get("token")
        name = page.get("name", page_id)

        if not page_id or not token:
            print(f"Skipping invalid page entry: {page}")
            continue

        content_file = pick_content_file(name)
        entries = load_content(content_file)

        page_key = (name or page_id).lower()
        prompt, caption = pick_unused_entry(page_key, entries, state)

        image_url = build_image_url(prompt)

        print(f"[{name}] content file: {content_file}")
        print(f"[{name}] prompt: {prompt}")
        print(f"[{name}] image URL: {image_url}")

        image_bytes = download_image_with_retry(image_url)

        if not image_bytes:
            print(f"[SKIP] {name} - image download failed completely, skipping this run")
            time.sleep(3)
            continue

        resp = post_to_page(page_id, token, image_bytes, caption)

        if resp.status_code == 200:
            print(f"[OK] Posted to {name}")
        else:
            print(f"[FAIL] {name} -> {resp.status_code}: {resp.text}")

        time.sleep(3)

    save_state(state)


if __name__ == "__main__":
    main()
