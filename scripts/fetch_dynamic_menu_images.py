from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlretrieve
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SEOUL = ZoneInfo("Asia/Seoul")
HINTS_PATH = ROOT / "menu-today" / "dynamic_menu_hints.json"
COLLECTION_LOG_PATH = ROOT / "menu-today" / "collection_log.json"
STARVALLEY_NAME = "\uc2a4\ud0c0\ubc38\ub9ac\ud478\ub4dc\ud3ec\uc720"
SJ_NAME = "\uc5d0\uc2a4\uc81c\uc774 \uad6c\ub0b4\uc2dd\ub2f9"


def load_collection_sources() -> list[dict]:
    if not COLLECTION_LOG_PATH.exists():
        return []
    data = json.loads(COLLECTION_LOG_PATH.read_text(encoding="utf-8-sig"))
    return data.get("sources", [])


def save_collection_sources(static_sources: list[dict], dynamic_sources: list[dict]) -> None:
    merged = {entry.get("name", ""): entry for entry in static_sources if entry.get("name")}
    for entry in dynamic_sources:
        if entry.get("name"):
            merged[entry["name"]] = entry
    COLLECTION_LOG_PATH.write_text(
        json.dumps({"sources": list(merged.values())}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_starvalley(page) -> dict:
    now = datetime.now(SEOUL)
    page.goto("https://pf.kakao.com/_axkixdn/posts", wait_until="networkidle", timeout=120000)
    first_href = page.locator("a.link_title").first.get_attribute("href")
    if not first_href:
        raise RuntimeError("starvalley_first_post_not_found")

    detail_url = f"https://pf.kakao.com{first_href}"
    page.goto(detail_url, wait_until="networkidle", timeout=120000)
    image = page.locator("img").evaluate_all(
        """
        els => els
          .map(e => ({src:e.src, alt:e.alt || '', w:e.naturalWidth, h:e.naturalHeight}))
          .filter(x => x.w >= 800 && x.h >= 1000)
          .slice(0, 1)
        """
    )
    if not image:
        raise RuntimeError("starvalley_menu_image_not_found")

    output = ROOT / "menu-today" / "images" / "starvalley-food4u-post.png"
    urlretrieve(image[0]["src"], str(output))
    return {
        "name": STARVALLEY_NAME,
        "page_url": "https://pf.kakao.com/_axkixdn/posts",
        "detail_url": detail_url,
        "image_url": image[0]["src"],
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
        "status": "updated",
        "fetched_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_sj(page) -> tuple[dict, dict]:
    now = datetime.now(SEOUL)
    page.goto("https://www.instagram.com/s_j_food_278/", wait_until="networkidle", timeout=120000)
    images = page.locator("img").evaluate_all(
        """
        els => els.map(e => ({src:e.src, alt:e.alt || '', w:e.naturalWidth, h:e.naturalHeight}))
        """
    )

    target = None
    target_patterns = [
        f"{now.month}\uc6d4 {now.day}\uc77c",
        f"{now.month}\uc6d4{now.day}\uc77c",
        f"{now.month}/{now.day}",
    ]
    for image in images:
        alt = image.get("alt", "")
        if any(pattern in alt for pattern in target_patterns) and "\uba54\ub274" in alt:
            target = image
            break

    if not target:
        raise RuntimeError("sj_today_menu_image_not_found")

    links = page.locator("a").evaluate_all(
        """
        els => els.map(e => e.getAttribute('href') || '').filter(x => x.includes('/p/')).slice(0, 8)
        """
    )
    post_url = f"https://www.instagram.com{links[0]}" if links else ""
    output = ROOT / "menu-today" / "images" / "sj-food-menu.png"
    urlretrieve(target["src"], str(output))
    result = {
        "name": SJ_NAME,
        "page_url": "https://www.instagram.com/s_j_food_278/",
        "detail_url": post_url,
        "image_url": target["src"],
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
        "status": "updated",
        "fetched_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    hint = {
        "name": SJ_NAME,
        "alt_text": target["alt"],
        "captured_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return result, hint


def main() -> None:
    results: list[dict] = []
    hints: list[dict] = []
    static_sources = load_collection_sources()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2400})

        try:
            results.append(fetch_starvalley(page))
        except Exception as exc:
            results.append(
                {
                    "name": STARVALLEY_NAME,
                    "page_url": "https://pf.kakao.com/_axkixdn/posts",
                    "status": "skipped",
                    "reason": str(exc),
                }
            )

        try:
            result, hint = fetch_sj(page)
            results.append(result)
            hints.append(hint)
        except Exception as exc:
            results.append(
                {
                    "name": SJ_NAME,
                    "page_url": "https://www.instagram.com/s_j_food_278/",
                    "status": "skipped",
                    "reason": str(exc),
                }
            )

        browser.close()

    HINTS_PATH.write_text(json.dumps({"sources": hints}, ensure_ascii=False, indent=2), encoding="utf-8")
    save_collection_sources(static_sources, results)
    print(json.dumps({"results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
