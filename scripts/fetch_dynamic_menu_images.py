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


def fetch_starvalley(page) -> dict:
    page.goto("https://pf.kakao.com/_axkixdn/posts", wait_until="networkidle", timeout=120000)
    first_href = page.locator("a.link_title").first.get_attribute("href")
    if not first_href:
        raise RuntimeError("스타밸리푸드포유 첫 게시글 링크를 찾지 못했습니다.")

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
        raise RuntimeError("스타밸리푸드포유 상세 메뉴 이미지를 찾지 못했습니다.")

    output = ROOT / "menu-today" / "images" / "starvalley-food4u-post.png"
    urlretrieve(image[0]["src"], str(output))
    return {
        "name": "스타밸리푸드포유",
        "status": "updated",
        "detail_url": detail_url,
        "image_url": image[0]["src"],
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
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
    target_label = f"{now.month}월 {now.day}일"
    for image in images:
        alt = image.get("alt", "")
        if target_label in alt and "메뉴" in alt:
            target = image
            break

    if not target:
        raise RuntimeError("에스제이 구내식당 오늘 메뉴 이미지를 찾지 못했습니다.")

    links = page.locator("a").evaluate_all(
        """
        els => els.map(e => e.getAttribute('href') || '').filter(x => x.includes('/p/')).slice(0, 8)
        """
    )
    post_url = f"https://www.instagram.com{links[0]}" if links else ""
    output = ROOT / "menu-today" / "images" / "sj-food-menu.png"
    urlretrieve(target["src"], str(output))
    result = {
        "name": "에스제이 구내식당",
        "status": "updated",
        "detail_url": post_url,
        "image_url": target["src"],
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
    }
    hint = {
        "name": "에스제이 구내식당",
        "alt_text": target["alt"],
        "captured_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return result, hint


def main() -> None:
    results: list[dict] = []
    hints: list[dict] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2400})

        try:
            results.append(fetch_starvalley(page))
        except Exception as exc:
            results.append({"name": "스타밸리푸드포유", "status": "skipped", "reason": str(exc)})

        try:
            result, hint = fetch_sj(page)
            results.append(result)
            hints.append(hint)
        except Exception as exc:
            results.append({"name": "에스제이 구내식당", "status": "skipped", "reason": str(exc)})

        browser.close()

    HINTS_PATH.write_text(json.dumps({"sources": hints}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
