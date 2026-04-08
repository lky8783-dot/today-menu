from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytesseract
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "menu-today" / "menu_today.json"
SEOUL = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

SOURCE_CONFIG = {
    "아이밀": {"image": ROOT / "menu-today" / "images" / "imeal.png", "min_items": 8, "max_items": 14},
    "밥(온) 구내식당": {"image": ROOT / "menu-today" / "images" / "babon.png", "min_items": 8, "max_items": 12},
    "구내식당라온푸드": {"image": ROOT / "menu-today" / "images" / "raonfood.png", "min_items": 8, "max_items": 12},
    "마이푸드": {"image": ROOT / "menu-today" / "images" / "myfood.png", "min_items": 8, "max_items": 12},
    "퍼블릭가산 구내식당": {"image": ROOT / "menu-today" / "images" / "public-gasan.png", "min_items": 3, "max_items": 4},
}

SAFE_FALLBACK_ONLY = {"밥(온) 구내식당", "마이푸드", "퍼블릭가산 구내식당"}

REPLACEMENTS = {
    "불고 기": "불고기",
    "볼어묵볶음": "불어묵볶음",
    "가든샐러드&오렌지ㅁ": "가든샐러드&오렌지D",
    "배주겉절이": "배추겉절이",
    "셀프비빔밤": "셀프비빔밥",
    "치킨덴더샐러뜨": "치킨텐더샐러드",
    "흰쌀밥/검은쌀잡곡밥": "흰쌀밥 / 검은쌀잡곡밥",
    "인쌀밥": "흰쌀밥",
    "검은쌀삽곡밥": "검은쌀잡곡밥",
    "김지제육두루지기": "김치제육두루치기",
    "순살지킨까스": "순살치킨까스",
    "콘마요s": "콘마요S",
    "햄깜자채야채볶음": "햄감자채야채볶음",
    "양배 주샐러드": "양배추샐러드",
    "삼색 경단": "삼색경단",
    "맑은콤나물국": "맑은콩나물국",
    "문제오리": "훈제오리",
    "고구마닭볶음탐": "고구마닭볶음탕",
    "생선까스/타르타르": "생선까스 / 타르타르",
    "꽈리고추멸지볶음": "꽈리고추멸치볶음",
    "알마늘종지무침": "알마늘쫑지무침",
    "샐러드&드레심": "샐러드 & 드레싱",
    "숭능": "숭늉",
    "잠치마요밥&조미김": "참치마요밥 & 조미김",
    "함박폭잡": "함박폭찹",
    "김말이*만두투김&양념장": "김말이 * 만두튀김 & 양념장",
    "햄감자채볶 음": "햄감자채볶음",
    "간장마늘쫓알마늘지": "간장마늘쫑알마늘지",
    "그린샐러드&드레싱": "그린샐러드 & 드레싱",
    "쌈채소&풋고추": "쌈채소 & 풋고추",
    "한강라면&달콤한토스트": "한강라면 & 달콤한 토스트",
    "구수한숭늉&시원한탄산음료": "구수한 숭늉 & 시원한 탄산음료",
}

STOP_TOKENS = [
    "4월",
    "2026",
    "메뉴",
    "점심",
    "중식",
    "원산지",
    "라온푸드",
    "다시봄",
    "urbanworkdasibom",
    "kcal",
]

NOISE_SUBSTRINGS = [
    "저희 사업장",
    "국산",
    "국내산",
    "호주산",
    "미국산",
    "스페인산",
    "SAL",
    "Wry",
    "yy",
    "tro",
    "MBS",
    "20555",
]


def find_tesseract() -> str:
    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path("/usr/bin/tesseract"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "tesseract"


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))


def save_data(data: dict) -> None:
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def preprocess_variants(image_path: Path) -> list[tuple[str, Image.Image, str]]:
    base = Image.open(image_path).convert("RGB")
    scale = 2
    color = base.resize((base.width * scale, base.height * scale))
    gray = ImageOps.autocontrast(base.convert("L")).resize((base.width * scale, base.height * scale))
    sharp = gray.filter(ImageFilter.SHARPEN)
    threshold = gray.point(lambda px: 255 if px > 182 else 0)
    return [
        ("color6", color, "--psm 6"),
        ("color11", color, "--psm 11"),
        ("gray6", gray, "--psm 6"),
        ("sharp6", sharp, "--psm 6"),
        ("th6", threshold, "--psm 6"),
    ]


def ocr_texts(image_path: Path) -> list[str]:
    outputs: list[str] = []
    for _, image, config in preprocess_variants(image_path):
        text = pytesseract.image_to_string(image, lang="kor+eng", config=config)
        outputs.append(text)
    return outputs


def clean_line(line: str) -> str:
    line = line.strip()
    line = line.replace("|", "").replace("•", " ").replace("·", " ").replace("●", " ")
    line = re.sub(r"\s+", " ", line)
    line = line.strip(" -_:,./")
    for before, after in REPLACEMENTS.items():
        line = line.replace(before, after)
    line = re.sub(r"\s*&\s*", " & ", line)
    line = re.sub(r"\s*/\s*", " / ", line)
    return line.strip()


def is_valid_candidate(line: str) -> bool:
    if not line:
        return False
    if any(token in line for token in STOP_TOKENS):
        return False
    if len(line) < 2 or len(line) > 44:
        return False
    if not re.search(r"[가-힣]", line):
        return False
    if re.fullmatch(r"[\d@A-Za-z\s]+", line):
        return False
    if any(token in line for token in NOISE_SUBSTRINGS):
        return False
    return True


def canonical_key(line: str) -> str:
    key = line
    key = key.replace(" ", "")
    key = key.replace("&", "").replace("/", "").replace("*", "")
    key = key.replace("(", "").replace(")", "")
    key = key.replace("D", "")
    key = key.replace("S", "")
    key = key.replace("@", "")
    return key


def normalize_final_line(line: str) -> str:
    line = clean_line(line)
    line = re.sub(r"^[@#]+\s*", "", line)
    line = re.sub(r"\([^)]*\)", "", line)
    line = re.sub(r"\[[^\]]*\]", "", line)
    line = re.sub(r"\s+", " ", line)
    line = line.strip(" -_/,:")
    return line.strip()


def collect_candidates(texts: list[str]) -> list[str]:
    candidates: list[str] = []
    for text in texts:
        for raw in text.splitlines():
            line = clean_line(raw)
            if is_valid_candidate(line):
                candidates.append(line)
    return candidates


def dedupe_candidates(candidates: list[str]) -> list[str]:
    counts = Counter(canonical_key(item) for item in candidates)
    first_line: dict[str, str] = {}
    first_index: dict[str, int] = {}
    for idx, item in enumerate(candidates):
        key = canonical_key(item)
        first_line.setdefault(key, normalize_final_line(item))
        first_index.setdefault(key, idx)
    ordered = sorted(first_line, key=lambda key: (-counts[key], first_index[key]))
    return [first_line[key] for key in ordered]


def parse_restaurant_menu(name: str, texts: list[str], existing: list[str]) -> tuple[list[str], bool]:
    if name in SAFE_FALLBACK_ONLY:
        return existing, True
    config = SOURCE_CONFIG[name]
    candidates = collect_candidates(texts)
    deduped = dedupe_candidates(candidates)
    if name == "퍼블릭가산 구내식당":
        return existing, True
    else:
        priority = [item for item in deduped if not any(token in item for token in ["셀프", "간편식", "탄산음료", "헛개차"])]
        tail = [item for item in deduped if item not in priority]
        deduped = priority + tail
    result = deduped[: config["max_items"]]
    duplicate_count = len(result) - len({canonical_key(item) for item in result})
    suspicious = sum(
        1
        for item in result
        if any(token in item for token in NOISE_SUBSTRINGS)
        or bool(re.search(r"[<>\\\\']", item))
        or len(re.findall(r"[A-Za-z]", item)) >= 2
        or bool(re.search(r"\d", item))
    )
    if duplicate_count >= 1:
        return existing, True
    if suspicious > max(1, len(result) // 4):
        return existing, True
    if len(result) < config["min_items"]:
        return existing, True
    return result, False


def update_json_with_ocr() -> None:
    pytesseract.pytesseract.tesseract_cmd = find_tesseract()
    data = load_data()
    now = datetime.now(SEOUL)
    data["date_label"] = f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAYS[now.weekday()]}"

    logs: list[dict] = []
    for restaurant in data.get("restaurants", []):
        name = restaurant.get("name", "")
        config = SOURCE_CONFIG.get(name)
        if not config:
            continue
        image_path = config["image"]
        if not image_path.exists():
            logs.append({"name": name, "updated": False, "reason": "image_missing"})
            continue
        previous_menu = list(restaurant.get("menu", []))
        texts = ocr_texts(image_path)
        extracted_menu, used_fallback = parse_restaurant_menu(name, texts, previous_menu)
        restaurant["menu"] = extracted_menu
        logs.append(
            {
                "name": name,
                "items": len(extracted_menu),
                "updated": not used_fallback,
                "used_existing_fallback": used_fallback,
            }
        )

    data["ocr_log"] = logs
    save_data(data)


def main() -> None:
    update_json_with_ocr()
    print("menu json updated from ocr")


if __name__ == "__main__":
    main()
