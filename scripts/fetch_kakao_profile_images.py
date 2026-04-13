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
SEOUL = ZoneInfo("Asia/Seoul")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}

PROFILE_SOURCES = [
    {"name": "아이밀", "page_url": "https://pf.kakao.com/_vygYn", "output": ROOT / "menu-today" / "images" / "imeal.png", "strategy": "meta_image"},
    {"name": "다시 봄", "page_url": "https://pf.kakao.com/_xhNExmn", "output": ROOT / "menu-today" / "images" / "dasibom.png", "strategy": "meta_image"},
    {"name": "밥(온) 구내식당", "page_url": "https://pf.kakao.com/_mYxfen", "output": ROOT / "menu-today" / "images" / "babon.png", "strategy": "meta_image"},
    {"name": "구내식당라온푸드", "page_url": "https://pf.kakao.com/_Rxkrxfn", "output": ROOT / "menu-today" / "images" / "raonfood.png", "strategy": "meta_image"},
    {"name": "마이푸드", "page_url": "https://pf.kakao.com/_xaAvxlG", "output": ROOT / "menu-today" / "images" / "myfood.png", "strategy": "meta_image"},
    {"name": "퍼블릭가산 구내식당", "page_url": "https://pf.kakao.com/_ECNfn", "output": ROOT / "menu-today" / "images" / "public-gasan.png", "strategy": "meta_image"},
    {"name": "더푸드스케치", "page_url": "https://pf.kakao.com/_nFfwj", "output": ROOT / "menu-today" / "images" / "thefoodsketch.png", "strategy": "meta_image"},
    {"name": "스타밸리푸드포유", "page_url": "https://pf.kakao.com/_axkixdn/posts", "output": ROOT / "menu-today" / "images" / "starvalley-food4u.png", "strategy": "kakao_first_post_image"},
    {"name": "돈토", "page_url": "https://pf.kakao.com/_Gxjxcbxj", "output": ROOT / "menu-today" / "images" / "donto.png", "strategy": "meta_image"},
    {"name": "에스제이 구내식당", "page_url": "https://www.instagram.com/s_j_food_278/", "output": ROOT / "menu-today" / "images" / "sj-food.png", "strategy": "instagram_first_post_image"},
]


def fetch_page_html(page_url: str) -> str:
    response = requests.get(page_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_meta_image(page_url: str, html: str) -> str | None:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(page_url, unescape(match.group(1)))
    return None


def extract_first_kakao_post_url(page_url: str, html: str) -> str | None:
    patterns = [
        r'<a[^>]+class=["\'][^"\']*link_title[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        r'href=["\']([^"\']+/\d+)["\']',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html, flags=re.IGNORECASE)
        for match in matches:
            post_url = urljoin(page_url, unescape(match))
            if re.search(r'/_[^/]+/\d+$', post_url):
                return post_url
    return None


def extract_first_instagram_post_url(page_url: str, html: str) -> str | None:
    matches = re.findall(r'href=["\']([^"\']*/p/[^"\']+/)["\']', html, flags=re.IGNORECASE)
    seen: set[str] = set()
    for match in matches:
        post_url = urljoin(page_url, unescape(match))
        if post_url in seen:
            continue
        seen.add(post_url)
        if '/p/' in post_url:
            return post_url
    return None


def normalize_kakao_image_url(image_url: str) -> str:
    for suffix in ["img_m.jpg", "img_l.jpg", "img_xl.jpg"]:
        if image_url.endswith(suffix):
            return image_url[: -len(suffix)] + "img.jpg"
    return image_url


def download_file(url: str, output_path: Path) -> None:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    image.save(output_path, format="PNG")


def resolve_image_url(source: dict) -> tuple[str | None, str | None]:
    strategy = source.get("strategy", "meta_image")
    page_url = source["page_url"]
    html = fetch_page_html(page_url)

    if strategy == "meta_image":
        image_url = extract_meta_image(page_url, html)
        if image_url:
            return normalize_kakao_image_url(image_url), page_url
        return None, None

    if strategy == "kakao_first_post_image":
        detail_url = extract_first_kakao_post_url(page_url, html)
        if not detail_url:
            return None, None
        detail_html = fetch_page_html(detail_url)
        image_url = extract_meta_image(detail_url, detail_html)
        if image_url:
            return normalize_kakao_image_url(image_url), detail_url
        return None, detail_url

    if strategy == "instagram_first_post_image":
        detail_url = extract_first_instagram_post_url(page_url, html)
        if not detail_url:
            return None, None
        detail_html = fetch_page_html(detail_url)
        image_url = extract_meta_image(detail_url, detail_html)
        if image_url:
            return image_url, detail_url
        return None, detail_url

    raise ValueError(f"unknown strategy: {strategy}")


def sync_preview_images() -> None:
    results: list[dict] = []
    for source in PROFILE_SOURCES:
        try:
            image_url, detail_url = resolve_image_url(source)
            if not image_url:
                results.append(
                    {
                        "name": source["name"],
                        "page_url": source["page_url"],
                        "status": "skipped",
                        "reason": "image_not_found",
                    }
                )
                continue
            download_file(image_url, source["output"])
            results.append(
                {
                    "name": source["name"],
                    "page_url": source["page_url"],
                    "detail_url": detail_url,
                    "image_url": image_url,
                    "output": str(source["output"].relative_to(ROOT)).replace("\\", "/"),
                    "status": "updated",
                    "fetched_at": datetime.now(SEOUL).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "name": source["name"],
                    "page_url": source["page_url"],
                    "status": "skipped",
                    "reason": str(exc),
                }
            )

    (ROOT / "menu-today" / "collection_log.json").write_text(
        json.dumps({"sources": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    sync_preview_images()
    print("menu images updated")


if __name__ == "__main__":
    main()
