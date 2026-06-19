from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MENU_DIR = ROOT / "guro-menu"
DATA_PATH = MENU_DIR / "menu_today.json"
HTML_PATH = MENU_DIR / "index.html"
SEOUL = ZoneInfo("Asia/Seoul")


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))


def render_card(item: dict) -> str:
    name = escape(item["name"])
    building = escape(item.get("building", ""))
    address = escape(item.get("address", ""))
    image = escape(item.get("preview_image", ""))
    image_path = MENU_DIR / item.get("preview_image", "").removeprefix("./")
    map_url = f"https://map.naver.com/p/search/{quote(item.get('map_query') or item['name'])}"
    channel_url = escape(item.get("channel_url", ""))
    menu = "".join(f"<li>{escape(line)}</li>" for line in item.get("menu", []))
    message = escape(item.get("message", ""))
    message_html = f'<p class="message">{message}</p>' if message else ""
    menu_html = f"<ul>{menu}</ul>" if menu else ""
    image_html = (
        f'<img class="menu-image" src="{image}" alt="{name} 식단 이미지" loading="lazy">'
        if image_path.exists()
        else '<div class="image-pending">메뉴 이미지 확인 중</div>'
    )
    return f"""
      <article class="restaurant-card">
        <div class="card-head">
          <div>
            <h2><a href="{map_url}" target="_blank" rel="noopener">{name}<span aria-hidden="true"> ↗</span></a></h2>
            <p class="building">{building}</p>
            <p class="address">{address}</p>
          </div>
          <a class="channel" href="{channel_url}" target="_blank" rel="noopener">원본 채널</a>
        </div>
        {image_html}
        {message_html}
        {menu_html}
      </article>"""


def render(data: dict) -> str:
    restaurants = data.get("restaurants", [])
    names = [item["name"] for item in restaurants]
    buildings = [item.get("building", "") for item in restaurants]
    addresses = [item.get("address", "") for item in restaurants]
    description = "구로디지털단지 구내식당 오늘 메뉴 모음: " + ", ".join(names)
    keywords = [
        "구로디지털단지 구내식당", "구디 구내식당", "구디 점심", "구로디지털단지 메뉴",
        "오늘 메뉴", *names, *buildings,
    ]
    structured = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": data["title"],
        "description": description,
        "itemListElement": [
            {
                "@type": "FoodEstablishment",
                "position": index,
                "name": item["name"],
                "address": item.get("address", ""),
                "servesCuisine": "구내식당",
                "url": item.get("channel_url", ""),
                "image": item.get("preview_image", ""),
                "containedInPlace": {"@type": "Place", "name": item.get("building", "")},
            }
            for index, item in enumerate(restaurants, 1)
        ],
    }
    cards = "\n".join(render_card(item) for item in restaurants)
    hidden_text = " ".join([*names, *buildings, *addresses])
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escape(data["title"])}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="keywords" content="{escape(", ".join(dict.fromkeys(keywords)))}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escape(data["title"])}">
  <meta property="og:description" content="{escape(description)}">
  <script type="application/ld+json">{json.dumps(structured, ensure_ascii=False)}</script>
  <style>
    :root{{--bg:#f4f7fb;--surface:#fff;--text:#172033;--muted:#607089;--line:#dfe7f3;--accent:#146c5c;--accent2:#32a889;--soft:#edf9f6;--shadow:0 18px 44px rgba(25,44,87,.08)}}
    *{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,rgba(50,168,137,.1),transparent 28%),var(--bg);color:var(--text);font-family:"Segoe UI","Malgun Gothic",sans-serif}}
    .wrap{{max-width:1160px;margin:auto;padding:24px 18px 42px}}.hero{{padding:30px;border-radius:28px;color:#fff;background:linear-gradient(135deg,#0c453c,#147864 58%,#45bfa0);box-shadow:var(--shadow)}}
    .eyebrow{{font-size:13px;font-weight:800;letter-spacing:.05em}}h1{{margin:12px 0 18px;font-size:clamp(28px,4.8vw,46px);line-height:1.2}}.search{{width:100%;height:52px;padding:0 16px;border:1px solid rgba(255,255,255,.28);border-radius:16px;background:rgba(255,255,255,.14);color:#fff;font-size:16px;outline:none}}.search::placeholder{{color:rgba(255,255,255,.75)}}
    .meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}}.meta div{{padding:17px 19px;border:1px solid var(--line);border-radius:19px;background:#fff;box-shadow:var(--shadow)}}.meta small{{display:block;color:var(--muted);font-weight:800;margin-bottom:6px}}.meta strong{{font-size:18px}}
    .notice{{margin-bottom:20px;padding:15px 18px;border:1px solid var(--line);border-radius:17px;background:#fff;color:var(--muted);line-height:1.7}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
    .restaurant-card{{padding:22px;border:1px solid var(--line);border-radius:24px;background:var(--surface);box-shadow:var(--shadow)}}.card-head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}h2{{margin:0;font-size:23px}}h2 a{{color:inherit;text-decoration:none}}h2 a:hover{{color:var(--accent)}}.building{{margin:6px 0 2px;color:var(--accent);font-weight:800}}.address{{margin:0;color:var(--muted);font-size:13px;line-height:1.55}}.channel{{flex:none;padding:7px 10px;border-radius:999px;background:var(--soft);color:var(--accent);font-size:12px;font-weight:800;text-decoration:none}}
    .menu-image{{display:block;width:100%;max-height:500px;margin:16px 0 13px;object-fit:contain;border:1px solid var(--line);border-radius:14px;background:#fff}}.image-pending{{margin:16px 0 13px;padding:45px 16px;text-align:center;border:1px dashed #aac9bf;border-radius:14px;background:var(--soft);color:var(--accent);font-weight:800}}ul{{margin:0;padding-left:20px;line-height:1.8}}.message{{margin:0 0 10px;color:var(--muted);font-size:14px;line-height:1.65}}.hidden{{display:none}}.seo{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
    footer{{padding:28px 10px;text-align:center;color:var(--muted);font-size:13px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}.meta{{grid-template-columns:1fr}}}}@media(max-width:520px){{.card-head{{display:block}}.channel{{display:inline-block;margin-top:10px}}}}
  </style>
</head>
<body>
<main class="wrap">
  <header class="hero">
    <div class="eyebrow">구로디지털단지 구내식당 메뉴모음</div>
    <h1>구로디지털단지 구내식당 메뉴정보</h1>
    <input id="menu-search" class="search" type="search" placeholder="식당명, 건물명, 메뉴명으로 검색" aria-label="메뉴 검색">
  </header>
  <section class="meta">
    <div><small>기준 날짜</small><strong>{escape(data["date_label"])}</strong></div>
    <div><small>최종 갱신</small><strong>{escape(data["updated_at"])}</strong></div>
    <div><small>등록 식당</small><strong>{len(restaurants)}개</strong></div>
  </section>
  <div class="notice">공개 카카오 채널의 메뉴 이미지를 자동 수집하고 OCR로 정리합니다. 텍스트에 오타가 있을 수 있으니 식단 이미지를 함께 확인해 주세요.</div>
  <section class="grid" id="restaurant-grid">{cards}
  </section>
  <section class="seo" aria-label="검색 정보">{escape(hidden_text)}</section>
</main>
<footer>구로디지털단지 구내식당 메뉴 · 공개 채널 기준 자동 갱신</footer>
<script>
  const input=document.querySelector('#menu-search');
  const cards=[...document.querySelectorAll('.restaurant-card')];
  input.addEventListener('input',()=>{{
    const q=input.value.trim().toLowerCase();
    cards.forEach(card=>card.classList.toggle('hidden',q&&!card.textContent.toLowerCase().includes(q)));
  }});
</script>
</body>
</html>"""


def main() -> None:
    data = load_data()
    now = datetime.now(SEOUL)
    if not data.get("date_label"):
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        data["date_label"] = f"{now.year}년 {now.month}월 {now.day}일 {weekdays[now.weekday()]}"
    data["updated_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HTML_PATH.write_text(render(data), encoding="utf-8")
    print(f"updated: {data['updated_at']}")


if __name__ == "__main__":
    main()
