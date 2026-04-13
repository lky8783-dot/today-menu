from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'menu-today' / 'menu_today.json'
HTML_PATH = ROOT / 'menu-today' / 'index.html'
SEOUL = ZoneInfo('Asia/Seoul')
PRIORITY = ['아이밀', '다시 봄', '밥(온) 구내식당']


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding='utf-8-sig'))


def parse_logged_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SEOUL)
    except ValueError:
        return None


def sort_restaurants(restaurants: list[dict]) -> list[dict]:
    priority_map = {name: index for index, name in enumerate(PRIORITY)}

    def sort_key(item: dict) -> tuple[int, str]:
        if item['name'] in priority_map:
            return (priority_map[item['name']], item['name'])
        return (len(priority_map) + 1, item['name'])

    leading = sorted([item for item in restaurants if item['name'] in priority_map], key=sort_key)
    trailing = [item for item in restaurants if item['name'] not in priority_map]
    trailing_ready = [item for item in trailing if item.get('status') == 'ready']
    trailing_preparing = [item for item in trailing if item.get('status') != 'ready']
    return leading + trailing_ready + trailing_preparing


def count_by_status(restaurants: list[dict], status: str) -> int:
    return sum(1 for item in restaurants if item.get('status') == status)


def render_restaurant_card(item: dict) -> str:
    name = escape(item['name'])
    building = escape(item.get('building', ''))
    address = escape(item.get('address', ''))
    status = item.get('status', 'ready')
    preview_image = item.get('preview_image', '').strip()
    map_url = item.get('map_url', '').strip()
    if not map_url:
        map_query = item.get('map_query', '').strip() or ' '.join(part for part in [item.get('name', ''), item.get('building', '')] if part)
        map_url = f'https://map.naver.com/p/search/{quote(map_query)}'
    badge_text = '준비중'
    badge_class = 'preparing'
    sub = building
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    title_html = (
        f'<a class="name-link" href="{escape(map_url)}" target="_blank" rel="noopener">'
        f'{name}<span class="direction-icon" aria-hidden="true"><img src="./images/naver-map.jpg" alt=""></span></a>'
    )
    preview_html = ''
    if status == 'ready' and preview_image:
        preview_html = f'''
            <div class="menu-preview">
              <img src="{escape(preview_image)}" alt="{name} 식단 이미지 미리보기">
            </div>'''
    menu_fresh = item.get('menu_fresh_today', True)
    if status == 'ready':
        menu_items = ''.join(f'<li>{escape(menu)}</li>' for menu in item.get('menu', []))
        menu_sections = item.get('menu_sections', [])
        section_html = ''
        if menu_sections:
            parts = []
            for section in menu_sections:
                title = escape(section.get('title', ''))
                items = ''.join(f'<li>{escape(menu)}</li>' for menu in section.get('items', []))
                if items:
                    parts.append(
                        f'<div class="menu-section"><div class="menu-section-title">{title}</div><ul>{items}</ul></div>'
                    )
            section_html = ''.join(parts)
        note_html = ''
        if item['name'] == '퍼블릭가산 구내식당':
            note_html = '<div class="info-note">현재는 메인메뉴만 공개됐습니다.</div>'
        elif not menu_fresh:
            note_html = '<div class="info-note">수집대기중입니다.</div>'
        elif not item.get('menu') and preview_image:
            note_html = '<div class="info-note">메뉴 텍스트는 정리 중입니다. 메뉴 이미지 확인 버튼으로 식단을 확인해 주세요.</div>'
        show_menu_items = menu_fresh and (bool(item.get('menu')) or bool(menu_sections))
        menu_html = section_html if menu_sections else f'<ul>{menu_items}</ul>'
        body = f'{note_html}{menu_html}' if show_menu_items else note_html
        action_html = ''
        if preview_image:
            action_html = (
                f'<button class="badge image-button" type="button" '
                f'data-image="{escape(preview_image)}" data-title="{name}">메뉴 이미지 확인</button>'
            )
        else:
            action_html = '<div class="badge ready">확인 완료</div>'
    else:
        body = '<div class="pending-box">수집예정입니다.</div>'
        action_html = f'<div class="badge {badge_class}">{badge_text}</div>'

    return f'''
      <article class="restaurant-card">
        <div class="card-head">
          <div class="title-wrap">
            <h2 class="name">{title_html}</h2>
            {sub_html}
            {preview_html}
          </div>
          {action_html}
        </div>
        {body}
      </article>'''


def render_page(data: dict) -> str:
    ocr_log = {entry.get('name'): entry for entry in data.get('ocr_log', [])}
    now = datetime.now(SEOUL).date()
    restaurants = []
    for item in data['restaurants']:
        row = dict(item)
        log = ocr_log.get(row.get('name'))
        recorded_at = parse_logged_time(row.get('menu_recorded_at'))
        row['menu_fresh_today'] = bool((log and log.get('updated')) or (recorded_at and recorded_at.date() == now))
        restaurants.append(row)
    ready_count = count_by_status(restaurants, 'ready')
    preparing_count = count_by_status(restaurants, 'preparing')
    cards = '\n'.join(render_restaurant_card(item) for item in restaurants)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(data['title'])}</title>
  <meta name="description" content="가산디지털단지 구내식당 오늘 메뉴를 식당별로 한눈에 확인할 수 있는 화면입니다.">
  <style>
    :root {{
      --bg: #f4f7fb;
      --surface: #ffffff;
      --text: #172033;
      --muted: #607089;
      --line: #dfe7f3;
      --accent: #2f67ff;
      --accent-soft: #eef4ff;
      --ok: #1f9d5c;
      --ok-soft: #ebfbf3;
      --wait: #bf7b00;
      --wait-soft: #fff7e6;
      --shadow: 0 18px 44px rgba(25, 44, 87, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: radial-gradient(circle at top, rgba(47, 103, 255, 0.08), transparent 28%), var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Malgun Gothic", sans-serif;
      cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 36 36'%3E%3Ctext x='4' y='27' font-size='24'%3E%F0%9F%8D%9E%3C/text%3E%3C/svg%3E") 8 8, auto;
    }}
    .wrap {{ max-width: 1160px; margin: 0 auto; padding: 24px 18px 40px; }}
    .hero {{
      background: linear-gradient(135deg, #153a9c 0%, #2f67ff 55%, #6fa3ff 100%);
      color: #fff;
      border-radius: 28px;
      padding: 28px;
      box-shadow: var(--shadow);
      margin-bottom: 22px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.22);
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 16px;
    }}
    h1 {{ margin: 0 0 10px; font-size: clamp(28px, 4.8vw, 46px); line-height: 1.2; color: #fff; }}
    .title-inline-icon {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      vertical-align: middle;
      margin: 0 0.12em;
    }}
    .title-inline-icon.meal {{
      font-size: 0.8em;
      transform: translateY(-0.03em);
    }}
    .search-wrap {{ margin-top: 18px; width: 100%; max-width: none; }}
    .search-label {{ display: block; font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.84); margin-bottom: 8px; }}
    .search-input {{ width: 100%; height: 52px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.24); background: rgba(255,255,255,0.14); color: #fff; padding: 0 16px; font-size: 16px; outline: none; backdrop-filter: blur(10px); }}
    .search-input::placeholder {{ color: rgba(255,255,255,0.68); }}
    .meta-bar {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0 22px; }}
    .meta-card, .restaurant-card {{ background: var(--surface); border: 1px solid var(--line); box-shadow: var(--shadow); }}
    .meta-card {{ border-radius: 20px; padding: 18px 20px; }}
    .meta-label {{ font-size: 12px; font-weight: 800; letter-spacing: 0.04em; color: var(--muted); text-transform: uppercase; margin-bottom: 8px; }}
    .meta-value {{ font-size: 21px; font-weight: 800; line-height: 1.35; }}
    .usage-note {{ margin: 0 0 22px; padding: 16px 18px; border-radius: 18px; background: var(--surface); border: 1px solid var(--line); box-shadow: var(--shadow); color: var(--muted); line-height: 1.7; font-size: 15px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .restaurant-card {{ border-radius: 24px; padding: 22px; display: flex; flex-direction: column; min-height: 100%; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }}
    .title-wrap {{ position: relative; }}
    .name {{ margin: 0; font-size: 24px; line-height: 1.25; word-break: keep-all; overflow-wrap: normal; }}
    .name-link {{ color: inherit; text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 0.18s ease, color 0.18s ease; display: inline-flex; align-items: center; gap: 8px; flex-wrap: nowrap; }}
    .name-link:hover {{ color: var(--accent); border-color: rgba(47, 103, 255, 0.4); }}
    .direction-icon {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 999px;
      overflow: hidden;
      box-shadow: 0 4px 10px rgba(47, 103, 255, 0.18);
      flex-shrink: 0;
    }}
    .direction-icon img {{
      display: block;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .sub {{ color: var(--muted); font-size: 14px; line-height: 1.6; margin-top: 6px; }}
    .badge {{ flex-shrink: 0; border-radius: 999px; padding: 9px 12px; font-size: 12px; font-weight: 800; white-space: nowrap; }}
    .badge.ready {{ background: var(--ok-soft); color: var(--ok); border: 1px solid rgba(31,157,92,0.18); }}
    .badge.preparing {{ background: var(--wait-soft); color: var(--wait); border: 1px solid rgba(191,123,0,0.18); }}
    .image-button {{ background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(47,103,255,0.16); text-decoration: none; cursor: pointer; }}
    .image-button:hover {{ background: #e2edff; }}
    mark.search-hit {{
      background: #fff2a8;
      color: #172033;
      padding: 0 2px;
      border-radius: 4px;
      font-weight: 800;
      box-shadow: inset 0 -1px 0 rgba(255, 196, 0, 0.35);
    }}
    ul {{ margin: 0; padding-left: 19px; line-height: 1.78; font-size: 16px; }}
    li + li {{ margin-top: 2px; }}
    .pending-box {{ margin-top: 8px; padding: 16px 18px; border-radius: 18px; background: #fffaf0; border: 1px dashed rgba(191,123,0,0.35); color: #6f5607; line-height: 1.7; font-size: 15px; }}
    .info-note {{ margin: 2px 0 12px; color: var(--muted); font-size: 14px; line-height: 1.6; }}
    .menu-section + .menu-section {{ margin-top: 14px; }}
    .menu-section-title {{
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 800;
      color: var(--accent);
      letter-spacing: 0.02em;
    }}
    .menu-preview {{ position: absolute; left: 0; top: calc(100% + 12px); width: 260px; padding: 10px; border-radius: 18px; background: rgba(255,255,255,0.98); border: 1px solid var(--line); box-shadow: 0 22px 48px rgba(16, 31, 69, 0.18); opacity: 0; visibility: hidden; transform: translateY(8px); transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease; z-index: 20; pointer-events: none; }}
    .menu-preview img {{ display: block; width: 100%; height: auto; border-radius: 12px; object-fit: cover; }}
    .title-wrap:hover .menu-preview {{ opacity: 1; visibility: visible; transform: translateY(0); }}
    .footer-note {{ margin-top: 22px; color: var(--muted); font-size: 13px; line-height: 1.7; text-align: center; }}
    .hidden-card {{ display: none; }}
    .modal-overlay {{
      position: fixed;
      inset: 0;
      background: rgba(8, 18, 40, 0.42);
      display: none;
      z-index: 1000;
    }}
    .modal-overlay.open {{ display: block; }}
    .modal-dialog {{
      position: fixed;
      width: min(92vw, 640px);
      max-height: min(82vh, 920px);
      background: #fff;
      border-radius: 24px;
      box-shadow: 0 28px 60px rgba(9, 20, 45, 0.32);
      overflow: hidden;
    }}
    .modal-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
    }}
    .modal-title {{ font-size: 18px; font-weight: 800; color: var(--text); }}
    .modal-close {{
      width: 38px;
      height: 38px;
      border: 0;
      border-radius: 999px;
      background: #eef3fb;
      color: var(--text);
      font-size: 20px;
      cursor: pointer;
    }}
    .modal-body {{ padding: 14px; background: #f8fbff; }}
    .modal-body img {{
      display: block;
      width: 100%;
      height: auto;
      max-height: calc(82vh - 92px);
      border-radius: 16px;
      background: #fff;
    }}
    @media (max-width: 960px) {{
      .meta-bar {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
      .menu-preview {{ display: none; }}
      .card-head {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }}
      .title-wrap {{
        min-width: 0;
      }}
      .image-button,
      .badge.preparing {{
        align-self: start;
        justify-self: end;
      }}
      .name {{
        font-size: 22px;
      }}
      .meta-card {{
        padding: 14px 16px;
        border-radius: 18px;
      }}
      .meta-label {{
        margin-bottom: 6px;
        font-size: 11px;
      }}
      .meta-value {{
        font-size: 16px;
        line-height: 1.4;
      }}
    }}
    @media (max-width: 560px) {{
      .meta-bar {{
        gap: 10px;
      }}
      .meta-card {{
        padding: 12px 14px;
        border-radius: 16px;
      }}
      .meta-value {{
        font-size: 15px;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">가산디지털단지 구내식당 메뉴모음</div>
      <h1>가산디지털단지 구내식당 <span class="title-inline-icon meal" aria-hidden="true">🍽️</span> 메뉴정보</h1>
      <div class="search-wrap">
        <label class="search-label" for="menu-search">메뉴검색</label>
        <input id="menu-search" class="search-input" type="text" placeholder="식당명, 건물명, 메뉴명으로 검색">
      </div>
    </section>

    <section class="meta-bar">
      <div class="meta-card"><div class="meta-label">기준 날짜</div><div class="meta-value">{escape(data['date_label'])}</div></div>
      <div class="meta-card"><div class="meta-label">최종 가져온 시간</div><div class="meta-value">{escape(data['updated_at'])}</div></div>
      <div class="meta-card"><div class="meta-label">확인 완료</div><div class="meta-value">{ready_count}개 식당</div></div>
      <div class="meta-card"><div class="meta-label">준비중</div><div class="meta-value">{preparing_count}개 채널</div></div>
    </section>

    <div class="usage-note">OCR로 읽어 오타가 있을 수 있습니다. 자동 갱신 시간은 평일 09:10, 09:40, 10:10, 10:40, 11:10, 11:40입니다.</div>

    <section class="grid" id="restaurant-grid">
{cards}
    </section>

    <div class="footer-note">메뉴 이미지는 공개 채널 기준으로 자동 수집한 뒤 정리한 결과입니다. 실제 운영 사정에 따라 식당 현장 메뉴와 일부 차이가 있을 수 있습니다.</div>
  </div>
  <div class="modal-overlay" id="image-modal" aria-hidden="true">
    <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-head">
        <div class="modal-title" id="modal-title">메뉴 이미지</div>
        <button class="modal-close" type="button" id="modal-close" aria-label="닫기">×</button>
      </div>
      <div class="modal-body">
        <img id="modal-image" src="" alt="메뉴 이미지 크게 보기">
      </div>
    </div>
  </div>
  <script>
    const searchInput = document.getElementById('menu-search');
    const cards = Array.from(document.querySelectorAll('.restaurant-card'));
    const imageButtons = Array.from(document.querySelectorAll('.image-button[data-image]'));
    const modal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');
    const modalTitle = document.getElementById('modal-title');
    const modalClose = document.getElementById('modal-close');
    const modalDialog = modal.querySelector('.modal-dialog');

    const textSelectors = ['.name-link', '.sub', '.info-note', '.pending-box', 'li'];
    const textNodes = cards.map((card) => {{
      const nodes = Array.from(card.querySelectorAll(textSelectors.join(',')));
      nodes.forEach((node) => {{
        if (!node.dataset.originalHtml) {{
          node.dataset.originalHtml = node.innerHTML;
        }}
      }});
      return nodes;
    }});

    const escapeRegExp = (value) => value.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');

    const highlightNode = (node, keyword) => {{
      const originalHtml = node.dataset.originalHtml || node.innerHTML;
      node.innerHTML = originalHtml;
      if (!keyword) return;
      const text = node.textContent || '';
      if (!text.toLowerCase().includes(keyword.toLowerCase())) return;
      const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      const textNodeList = [];
      while (walker.nextNode()) {{
        textNodeList.push(walker.currentNode);
      }}
      const regex = new RegExp(`(${{
        escapeRegExp(keyword)
      }})`, 'gi');
      textNodeList.forEach((textNode) => {{
        const value = textNode.nodeValue || '';
        if (!value.toLowerCase().includes(keyword.toLowerCase())) return;
        const wrapper = document.createElement('span');
        wrapper.innerHTML = value.replace(regex, '<mark class=\"search-hit\">$1</mark>');
        textNode.replaceWith(...Array.from(wrapper.childNodes));
      }});
    }};

    searchInput.addEventListener('input', () => {{
      const keyword = searchInput.value.trim().toLowerCase();
      cards.forEach((card, index) => {{
        const text = card.textContent.toLowerCase();
        card.classList.toggle('hidden-card', keyword !== '' && !text.includes(keyword));
        textNodes[index].forEach((node) => highlightNode(node, keyword));
      }});
    }});

    const positionModalNearButton = (button) => {{
      const rect = button.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const desiredWidth = Math.min(viewportWidth - 24, 640);
      const left = Math.min(
        Math.max(12, rect.left + rect.width - desiredWidth),
        Math.max(12, viewportWidth - desiredWidth - 12)
      );
      const estimatedHeight = Math.min(viewportHeight - 24, 620);
      let top = rect.bottom + 12;
      if (top + estimatedHeight > viewportHeight - 12) {{
        top = Math.max(12, rect.top - estimatedHeight - 12);
      }}
      modalDialog.style.width = `${{desiredWidth}}px`;
      modalDialog.style.left = `${{left}}px`;
      modalDialog.style.top = `${{top}}px`;
    }};

    imageButtons.forEach((button) => {{
      button.addEventListener('click', () => {{
        modalImage.src = button.dataset.image || '';
        modalTitle.textContent = `${{button.dataset.title || '메뉴 이미지'}}`;
        positionModalNearButton(button);
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
      }});
    }});

    const closeModal = () => {{
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden', 'true');
      modalImage.src = '';
      modalDialog.style.left = '';
      modalDialog.style.top = '';
      modalDialog.style.width = '';
    }};

    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (event) => {{
      if (event.target === modal) closeModal();
    }});
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape' && modal.classList.contains('open')) closeModal();
    }});
  </script>
</body>
</html>
'''


def main() -> None:
    data = load_data()
    data['updated_at'] = datetime.now(SEOUL).strftime('%Y-%m-%d %H:%M:%S')
    data['restaurants'] = sort_restaurants(data['restaurants'])
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    HTML_PATH.write_text(render_page(data), encoding='utf-8')
    print(f"updated: {data['updated_at']}")


if __name__ == '__main__':
    main()
