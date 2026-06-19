from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytesseract
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MENU_DIR = ROOT / "guro-menu"
DATA_PATH = MENU_DIR / "menu_today.json"
LOG_PATH = MENU_DIR / "collection_log.json"
OVERRIDES_PATH = MENU_DIR / "manual_menu_overrides.json"
SEOUL = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
NOISE = {
    "메뉴", "구내식당", "오늘의 메뉴", "점심", "중식", "석식", "원산지", "공지",
    "카카오톡 채널", "친구추가", "좋아요", "공유", "댓글", "더보기",
}
REPLACEMENTS = {
    "김밀이": "김말이",
    "공나물": "콩나물",
    "무밀랭이": "무말랭이",
    "무짐": "무침",
    "숭능": "숭늉",
    "북은지": "묵은지",
    "떡괄비": "떡갈비",
    "틀기름": "들기름",
    "고주장": "고추장",
    "관장고주지": "간장고추지",
    "탄산올료": "탄산음료",
    "미슷가루": "미숫가루",
}


def find_tesseract() -> str:
    for candidate in [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path("/usr/bin/tesseract"),
    ]:
        if candidate.exists():
            return str(candidate)
    return "tesseract"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean_line(value: str) -> str:
    value = re.sub(r"[|•·●■◆▶▷※]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -_:;,./")
    value = value.strip(" {}[]\\")
    value = re.sub(r"\s+[A-Z]{2,4}$", "", value)
    for source, target in REPLACEMENTS.items():
        value = value.replace(source, target)
    return value


def is_menu_line(value: str, excluded_terms: list[str]) -> bool:
    if not value or len(value) < 2 or len(value) > 38:
        return False
    if value in NOISE:
        return False
    if any(term and term.replace(" ", "") in value.replace(" ", "") for term in excluded_terms):
        return False
    if re.search(r"\d{1,2}\s*월\s*\d{1,2}\s*일|\d{1,2}\s*/\s*\d{1,2}|[월화수목금토일]요일", value):
        return False
    if re.fullmatch(r"[\d\s:./~-]+", value):
        return False
    if any(token in value for token in ["http", "카카오", "채널", "문의", "영업시간", "전화", "식권", "식단은", "변경될 수"]):
        return False
    return bool(re.search(r"[가-힣]", value))


def ocr_lines(image_path: Path, excluded_terms: list[str]) -> tuple[list[str], str]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    if width < 1400:
        ratio = 1400 / width
        image = image.resize((1400, int(height * ratio)))
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray).filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(gray, lang="kor+eng", config="--psm 6")
    lines: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = clean_line(raw)
        if is_menu_line(line, excluded_terms) and line not in seen:
            seen.add(line)
            lines.append(line)
    return lines[:18], text


def has_today_marker(text: str, now: datetime) -> bool:
    compact = re.sub(r"\s+", "", text)
    markers = [
        f"{now.month}월{now.day}일",
        f"{now.month}/{now.day}",
        WEEKDAYS[now.weekday()],
    ]
    return any(marker.replace(" ", "") in compact for marker in markers)


def main() -> None:
    pytesseract.pytesseract.tesseract_cmd = find_tesseract()
    data = read_json(DATA_PATH)
    collection = {
        entry.get("name", ""): entry
        for entry in read_json(LOG_PATH).get("sources", [])
    }
    overrides = read_json(OVERRIDES_PATH) if OVERRIDES_PATH.exists() else {}
    now = datetime.now(SEOUL)
    logs: list[dict] = []

    data["date_label"] = f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAYS[now.weekday()]}"
    for restaurant in data.get("restaurants", []):
        name = restaurant["name"]
        image_path = MENU_DIR / restaurant.get("preview_image", "").removeprefix("./")
        source = collection.get(name, {})
        if not image_path.exists() or source.get("status") != "updated":
            restaurant["menu"] = []
            restaurant["message"] = "오늘 메뉴 이미지를 가져오지 못했습니다."
            logs.append({"name": name, "updated": False, "reason": "image_missing"})
            continue

        lines, raw_text = ocr_lines(
            image_path,
            [name, restaurant.get("building", "")],
        )
        today_marker = has_today_marker(raw_text, now)
        manual = overrides.get(now.strftime("%Y-%m-%d"), {}).get(name)
        if manual:
            lines = manual.get("menu", lines)
            today_marker = True

        if len(lines) >= 4:
            restaurant["menu"] = lines
            restaurant["message"] = "" if today_marker else "최신 공개 식단 이미지의 텍스트입니다. 날짜는 원본 이미지를 확인해 주세요."
        else:
            restaurant["menu"] = []
            restaurant["message"] = "공개 채널에서 최신 메뉴 이미지 제공 방식을 확인 중입니다."
        logs.append(
            {
                "name": name,
                "items": len(lines) if len(lines) >= 4 else 0,
                "updated": len(lines) >= 4,
                "today_marker": today_marker,
                "source_fetched_at": source.get("fetched_at", ""),
            }
        )

    data["ocr_log"] = logs
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"restaurants": len(data.get("restaurants", [])), "logs": logs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
