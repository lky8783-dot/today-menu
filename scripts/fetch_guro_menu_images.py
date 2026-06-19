from __future__ import annotations

import io
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MENU_DIR = ROOT / "guro-menu"
DATA_PATH = MENU_DIR / "menu_today.json"
LOG_PATH = MENU_DIR / "collection_log.json"
SEOUL = ZoneInfo("Asia/Seoul")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))


def extract_meta_image(page_url: str, html: str) -> str | None:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(page_url, unescape(match.group(1)))
    return None


def normalize_image_url(image_url: str) -> str:
    return re.sub(r"img_(?:m|l|xl)\.jpg$", "img.jpg", image_url)


def download_image(image_url: str, output_path: Path) -> None:
    response = requests.get(image_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    width, height = image.size
    if width == height and width <= 600:
        raise RuntimeError("channel_default_image")
    image.save(output_path, format="PNG")


def main() -> None:
    data = load_data()
    results: list[dict] = []

    for restaurant in data.get("restaurants", []):
        page_url = restaurant.get("channel_url", "")
        output = MENU_DIR / restaurant.get("preview_image", "").removeprefix("./")
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            image_url = extract_meta_image(page_url, response.text)
            if not image_url:
                raise RuntimeError("menu_image_not_found")
            image_url = normalize_image_url(image_url)
            download_image(image_url, output)
            results.append(
                {
                    "name": restaurant["name"],
                    "page_url": page_url,
                    "image_url": image_url,
                    "output": str(output.relative_to(ROOT)).replace("\\", "/"),
                    "status": "updated",
                    "fetched_at": datetime.now(SEOUL).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        except Exception as exc:
            if output.exists():
                output.unlink()
            results.append(
                {
                    "name": restaurant.get("name", ""),
                    "page_url": page_url,
                    "status": "skipped",
                    "reason": str(exc),
                }
            )

    LOG_PATH.write_text(
        json.dumps({"sources": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
