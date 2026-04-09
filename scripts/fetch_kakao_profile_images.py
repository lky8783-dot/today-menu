from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}

PROFILE_SOURCES = [
    {"name": "아이밀", "page_url": "https://pf.kakao.com/_vygYn", "output": ROOT / "menu-today" / "images" / "imeal.png"},
    {"name": "다시 봄", "page_url": "https://pf.kakao.com/_xhNExmn", "output": ROOT / "menu-today" / "images" / "dasibom.png"},
    {"name": "밥(온) 구내식당", "page_url": "https://pf.kakao.com/_mYxfen", "output": ROOT / "menu-today" / "images" / "babon.png"},
    {"name": "구내식당라온푸드", "page_url": "https://pf.kakao.com/_Rxkrxfn", "output": ROOT / "menu-today" / "images" / "raonfood.png"},
    {"name": "마이푸드", "page_url": "https://pf.kakao.com/_xaAvxlG", "output": ROOT / "menu-today" / "images" / "myfood.png"},
    {"name": "퍼블릭가산 구내식당", "page_url": "https://pf.kakao.com/_ECNfn", "output": ROOT / "menu-today" / "images" / "public-gasan.png"},
    {"name": "더푸드스케치", "page_url": "https://pf.kakao.com/_nFfwj", "output": ROOT / "menu-today" / "images" / "thefoodsketch.png"},
    {"name": "스타밸리푸드포유", "page_url": "https://pf.kakao.com/_axkixdn", "output": ROOT / "menu-today" / "images" / "starvalley-food4u.png"},
    {"name": "돈토", "page_url": "https://pf.kakao.com/_Gxjxcbxj", "output": ROOT / "menu-today" / "images" / "donto.png"},
    {"name": "에스제이 구내식당", "page_url": "https://www.instagram.com/s_j_food_278/", "output": ROOT / "menu-today" / "images" / "sj-food.png"},
]


def extract_meta_image(page_url: str, html: str) -> str | None:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(page_url, match.group(1))
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
    output_path.write_bytes(response.content)


def sync_preview_images() -> None:
    results: list[dict] = []
    for source in PROFILE_SOURCES:
        try:
            page_response = requests.get(source["page_url"], headers=HEADERS, timeout=30)
            page_response.raise_for_status()
            image_url = extract_meta_image(source["page_url"], page_response.text)
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
            image_url = normalize_kakao_image_url(image_url)
            download_file(image_url, source["output"])
            results.append(
                {
                    "name": source["name"],
                    "page_url": source["page_url"],
                    "image_url": image_url,
                    "output": str(source["output"].relative_to(ROOT)).replace("\\", "/"),
                    "status": "updated",
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
    print("kakao profile images updated")


if __name__ == "__main__":
    main()
