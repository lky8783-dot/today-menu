from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytesseract
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "menu-today" / "menu_today.json"
HINTS_PATH = ROOT / "menu-today" / "dynamic_menu_hints.json"
COLLECTION_LOG_PATH = ROOT / "menu-today" / "collection_log.json"
SJ_WEEKLY_IMAGE_PATH = ROOT / "menu-today" / "images" / "sj-weekly-menu.png"
SEOUL = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
RECENT_FETCH_WINDOW = timedelta(hours=6)

SOURCE_CONFIG = {
    "아이밀": {"image": ROOT / "menu-today" / "images" / "imeal.png", "min_items": 8, "max_items": 14},
    "다시 봄": {"image": ROOT / "menu-today" / "images" / "dasibom.png", "min_items": 6, "max_items": 12},
    "밥(온) 구내식당": {"image": ROOT / "menu-today" / "images" / "babon.png", "min_items": 8, "max_items": 12},
    "구내식당라온푸드": {"image": ROOT / "menu-today" / "images" / "raonfood.png", "min_items": 8, "max_items": 12},
    "마이푸드": {"image": ROOT / "menu-today" / "images" / "myfood.png", "min_items": 8, "max_items": 12},
    "퍼블릭가산 구내식당": {"image": ROOT / "menu-today" / "images" / "public-gasan.png", "min_items": 3, "max_items": 4},
    "더푸드스케치": {"image": ROOT / "menu-today" / "images" / "thefoodsketch.png", "min_items": 9, "max_items": 12},
    "스타밸리푸드포유": {"image": ROOT / "menu-today" / "images" / "starvalley-food4u-post.png", "min_items": 8, "max_items": 12},
    "에스제이 구내식당": {"image": ROOT / "menu-today" / "images" / "sj-food-menu.png", "min_items": 10, "max_items": 16},
}

SAFE_FALLBACK_ONLY = {"밥(온) 구내식당", "마이푸드", "퍼블릭가산 구내식당"}

REPLACEMENTS = {
    "대파숫불치킨바베큐": "대파숯불치킨바베큐",
    "판고기 사전": "철판고기산적",
    "샐러": "샐러드",
    "까드": "깍두기",
    "프라면": "라면",
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


def load_hints() -> dict[str, dict]:
    if not HINTS_PATH.exists():
        return {}
    data = json.loads(HINTS_PATH.read_text(encoding="utf-8-sig"))
    return {entry.get("name", ""): entry for entry in data.get("sources", [])}


def load_collection_log() -> dict[str, dict]:
    if not COLLECTION_LOG_PATH.exists():
        return {}
    data = json.loads(COLLECTION_LOG_PATH.read_text(encoding="utf-8-sig"))
    return {entry.get("name", ""): entry for entry in data.get("sources", [])}


def save_data(data: dict) -> None:
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_logged_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SEOUL)
    except ValueError:
        return None


def get_source_fetched_at(name: str, image_path: Path, collection_log: dict[str, dict]) -> datetime | None:
    entry = collection_log.get(name, {})
    fetched_at = parse_logged_time(entry.get("fetched_at"))
    if fetched_at:
        return fetched_at
    if image_path.exists():
        return datetime.fromtimestamp(image_path.stat().st_mtime, tz=SEOUL)
    return None


def is_recent_fetch(fetched_at: datetime | None, now: datetime) -> bool:
    if not fetched_at:
        return False
    return fetched_at.date() == now.date() and now - fetched_at <= RECENT_FETCH_WINDOW


def has_today_marker(texts: list[str], now: datetime) -> bool:
    weekday = WEEKDAYS[now.weekday()]
    patterns = [
        rf"{now.month}\s*월\s*{now.day}\s*일",
        rf"{now.month}\s*/\s*{now.day}",
        weekday,
    ]
    merged = "\n".join(texts)
    return any(re.search(pattern, merged) for pattern in patterns)


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


def ocr_image_variants(image: Image.Image, configs: list[str] | None = None) -> list[str]:
    configs = configs or ["--psm 6", "--psm 11"]
    gray = ImageOps.autocontrast(image.convert("L"))
    enlarged = gray.resize((gray.width * 3, gray.height * 3)).filter(ImageFilter.SHARPEN)
    threshold = enlarged.point(lambda px: 255 if px > 182 else 0)
    variants = [enlarged, threshold]
    outputs: list[str] = []
    for variant in variants:
        for config in configs:
            text = pytesseract.image_to_string(variant, lang="kor+eng", config=config)
            outputs.append(text)
    return outputs


def ocr_dasibom_crops(image_path: Path) -> list[str]:
    base = Image.open(image_path).convert("RGB")
    regions = [
        (0, int(base.height * 0.12), base.width, int(base.height * 0.66), "--psm 11"),
        (0, int(base.height * 0.15), base.width, int(base.height * 0.62), "--psm 6"),
    ]
    outputs: list[str] = []
    for left, top, right, bottom, config in regions:
        crop = base.crop((left, top, right, bottom))
        gray = ImageOps.autocontrast(crop.convert("L")).resize((crop.width * 3, crop.height * 3)).filter(ImageFilter.SHARPEN)
        text = pytesseract.image_to_string(gray, lang="kor+eng", config=config)
        outputs.append(text)
    return outputs


def extract_sj_section_lines(image: Image.Image) -> list[str]:
    texts = ocr_image_variants(image)
    candidates = collect_candidates(texts)
    deduped = dedupe_candidates(candidates)
    filtered: list[str] = []
    seen: set[str] = set()
    footer_patterns = [
        (r"계란후라이.*토스트.*딸기잼", "계란후라이 / 토스트&딸기잼"),
        (r"셀프\s*라면|셀프라면", "셀프 라면"),
        (r"탄산음료.*숭늉.*매실차|숭늉.*매실차", "탄산음료, 숭늉, 매실차"),
        (r"백미밥\s*/\s*잡곡밥\s*/\s*김치|백미밥잡곡밥김치", "백미밥 / 잡곡밥 / 김치"),
        (r"그린샐러드.*드레싱", "그린샐러드 & 드레싱"),
    ]
    for item in deduped:
        if any(token in item for token in ["월요일", "화요일", "수요일", "목요일", "금요일", "4월", "점심", "저녁", "구분", "에스제이", "건강식단"]):
            continue
        normalized = item
        for pattern, label in footer_patterns:
            if re.search(pattern, normalized):
                normalized = label
                break
        if len(normalized) < 2:
            continue
        key = canonical_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        filtered.append(normalize_final_line(normalized))
    return filtered


def parse_sj_weekly_image(image_path: Path, now: datetime) -> tuple[dict[str, list[str]] | None, bool]:
    if now.weekday() > 4 or not image_path.exists():
        return None, False

    base = Image.open(image_path).convert("RGB")
    width, height = base.size
    left_label_width = int(width * 0.065)
    col_width = int((width - left_label_width) / 5)
    day_index = now.weekday()
    col_left = left_label_width + (col_width * day_index) + int(col_width * 0.04)
    col_right = left_label_width + (col_width * (day_index + 1)) - int(col_width * 0.04)

    header_crop = base.crop((col_left, int(height * 0.02), col_right, int(height * 0.12)))
    header_texts = ocr_image_variants(header_crop, ["--psm 6", "--psm 7", "--psm 11"])
    today_marker = has_today_marker(header_texts, now)

    lunch_crop = base.crop((col_left, int(height * 0.10), col_right, int(height * 0.54)))
    dinner_crop = base.crop((col_left, int(height * 0.58), col_right, int(height * 0.98)))

    lunch_items = extract_sj_section_lines(lunch_crop)
    dinner_items = extract_sj_section_lines(dinner_crop)

    plus_menu = ["계란후라이 / 토스트&딸기잼", "셀프 라면", "탄산음료, 숭늉, 매실차"]
    lunch_items = [item for item in lunch_items if item not in plus_menu]
    dinner_items = [item for item in dinner_items if item not in plus_menu]

    sections: dict[str, list[str]] = {}
    if lunch_items:
        sections["중식"] = lunch_items
    if dinner_items:
        sections["석식"] = dinner_items
    sections["플러스메뉴"] = plus_menu

    if not sections.get("중식") and not sections.get("석식"):
        return None, today_marker
    return sections, today_marker


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
    if name == "아이밀":
        merged = "\n".join(texts)
        found: list[str] = []
        patterns = [
            (r"유부미니우동", "유부미니우동"),
            (r"돈육메란장조림|돈육메추리알장조림", "돈육메란장조림"),
            (r"치킨까스\s*&\s*머스타드|치킨까스.*머스타드", "치킨까스 & 머스타드"),
            (r"콘참치펜네샐러드", "콘참치펜네샐러드"),
            (r"얼갈이된장나물", "얼갈이된장나물"),
            (r"참나물오리엔탈무침", "참나물오리엔탈무침"),
            (r"가든샐러드\s*&\s*블루베리D|가든샐러드.*블루베리D", "가든샐러드 & 블루베리D"),
            (r"국내산\s*배추겉절이|배추겉절이", "국내산 배추겉절이"),
            (r"흑미밥\s*/\s*백미밥|흑미밥백미밥", "흑미밥 / 백미밥"),
            (r"헛개차\s*/\s*탄산음료|헛개차.*탄산음료", "헛개차 / 탄산음료"),
            (r"셀프비빔밥\s*/\s*한강라면|셀프비빔밥.*한강라면", "셀프비빔밥 / 한강라면"),
            (r"간편식:\s*훈제오리샐러드|훈제오리샐러드", "간편식: 훈제오리샐러드"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, merged):
                found.append(label)
        found = [item for idx, item in enumerate(found) if item not in found[:idx]]
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "다시 봄":
        merged = "\n".join(texts)
        found: list[str] = []
        patterns = [
            (r"시금치된장국|\|금치된장국", "시금치된장국"),
            (r"대파.*치킨바베큐|대파숫불치킨바베큐", "대파숯불치킨바베큐"),
            (r"해물까스", "해물까스"),
            (r"철판고기산적|판고기 사전|판고기산적", "철판고기산적"),
            (r"양반단팥찐빵|단팥찐빵|팥찐빵|한입단팔핀빵|단팔핀빵|단팥핀빵", "양반단팥찐빵"),
            (r"꽈리고추양념찜|고추양념찜|파리고추양념찜", "꽈리고추양념찜"),
            (r"샐러드|샐러", "샐러드"),
            (r"깍두기|까드", "깍두기"),
            (r"잔치국수", "잔치국수"),
            (r"탄산음료|산음료|탄\s*산음\s*\w*음료", "탄산음료"),
            (r"셀프라면|프라면", "셀프라면"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, merged):
                found.append(label)
        found = [item for idx, item in enumerate(found) if item not in found[:idx]]
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "구내식당라온푸드":
        merged = "\n".join(texts)
        found: list[str] = []
        patterns = [
            (r"오므라이스", "오므라이스"),
            (r"돈육김치찌개|돈육김치지개", "돈육김치찌개"),
            (r"차돌박이숙주볶음|차돌박이숙주묶음|차돌박이숙주복음", "차돌박이숙주볶음"),
            (r"치킨스틱\s*&\s*치즈스틱|치킨스틱치즈스틱", "치킨스틱 & 치즈스틱"),
            (r"갈비산적데리야끼|갈비산적데리아끼|갈비산적데리야기", "갈비산적데리야끼"),
            (r"야채비빔만두|야재비빔만두|야채비빔만드", "야채비빔만두"),
            (r"스팸계란볶음밥|스팸계란복음밥", "스팸계란볶음밥"),
            (r"셀프라면\s*&\s*배추김치|셀프라면.*배추김치", "셀프라면 & 배추김치"),
            (r"샐러드\s*&\s*드레싱|샐러드.*드레싱", "샐러드 & 드레싱"),
            (r"숭늉\s*&\s*음료|숭늉.*음료", "숭늉 & 음료"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, merged):
                found.append(label)
        found = [item for idx, item in enumerate(found) if item not in found[:idx]]
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "더푸드스케치":
        merged = "\n".join(texts)
        found: list[str] = []
        patterns = [
            (r"혼합잡곡밥|호합잡곡밥|혼합잠곡밥", "혼합잡곡밥"),
            (r"들깨수제비|들깨수재비", "들깨수제비"),
            (r"매운갈비찜", "매운갈비찜"),
            (r"순살닭다리살치킨너겟|순살닭다리살치킨너것|순살닭다리살치킨너켓", "순살닭다리살치킨너겟"),
            (r"소세지스크램블에그|소시지스크램블에그", "소세지스크램블에그"),
            (r"비빔만두", "비빔만두"),
            (r"청양어묵볶음|청앙어묵볶음", "청양어묵볶음"),
            (r"유자연근무침|유자연근묻침", "유자연근무침"),
            (r"생깻잎지|생깻입지", "생깻잎지"),
            (r"가든샐러드\s*/\s*드레싱|가든샐러드.*드레싱", "가든샐러드 / 드레싱"),
            (r"배추겉절이\s*/\s*음료|배추겉절이.*음료", "배추겉절이 / 음료"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, merged):
                found.append(label)
        found = [item for idx, item in enumerate(found) if item not in found[:idx]]
        # 이미지가 오늘 식단으로 확인됐고 핵심 메뉴가 충분히 잡히면,
        # 수동 보정으로 넣어둔 전체 메뉴를 그대로 유지하면서 오늘 메뉴로 인정한다.
        if len(found) >= 8 and existing:
            return existing[: config["max_items"]], False
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "스타밸리푸드포유":
        merged = "\n".join(texts)
        found: list[str] = []
        patterns = [
            (r"흑미밥\s*/\s*백미밥|흑미밥백미밥", "흑미밥 / 백미밥"),
            (r"매콤소불고기볶음", "매콤소불고기볶음"),
            (r"쑥갓어묵탕", "쑥갓어묵탕"),
            (r"카레돈까스", "카레돈까스"),
            (r"골뱅이비빔라면", "골뱅이비빔라면"),
            (r"물만두.*초간장|물만두초간장", "물만두 * 초간장"),
            (r"베이컨감자볶음", "베이컨감자볶음"),
            (r"유부오이매실무침", "유부오이매실무침"),
            (r"가든샐러드.*흑임자D|가든샐러드흑임자D", "가든샐러드 & 흑임자D"),
            (r"포기김치", "포기김치"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, merged):
                found.append(label)
        found = [item for idx, item in enumerate(found) if item not in found[:idx]]
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
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


def parse_sj_sections_from_hint(hint_text: str) -> dict[str, list[str]] | None:
    if not hint_text:
        return None
    compact = re.sub(r"\s+", " ", hint_text)
    sections = {}
    section_patterns = {
        "중식": [
            "얼큰닭개장",
            "들깨백불고기",
            "매콤맛살링튀김",
            "불닭완자구이",
            "어묵메추리알조림",
            "도토리묵무침",
            "브로컬리숙회",
            "백미밥/잡곡밥/김치",
            "그린셀러드&드레싱",
        ],
        "석식": [
            "시래기된장국",
            "닭볶음탕",
            "돈가스",
            "치즈계란말이",
            "모듬채소잡채",
            "계절나물",
            "백미밥/잡곡밥/김치",
            "그린셀러드&드레싱",
        ],
    }

    def split_items(chunk: str, patterns: list[str]) -> list[str]:
        items = []
        for label in patterns:
            if label in chunk:
                items.append(label.replace("/", " / ").replace("&", " & "))
        return items

    markers = []
    for label in ["중식", "석식", "플러스메뉴"]:
        idx = compact.find(label)
        if idx >= 0:
            markers.append((idx, label))
    markers.sort()

    for pos, label in markers:
        end = len(compact)
        for next_pos, _ in markers:
            if next_pos > pos:
                end = next_pos
                break
        chunk = compact[pos + len(label):end].strip()
        if label == "플러스메뉴":
            extras = []
            for item in ["셀프계란후라이", "한강라면", "토스트&딸기잼", "탄산음료", "숭늉", "매실차"]:
                if item in chunk or item in compact:
                    extras.append(item.replace("&", " & "))
            if extras:
                sections["플러스메뉴"] = extras
            continue
        items = split_items(chunk, section_patterns.get(label, []))
        if items:
            sections[label] = items

    if not sections:
        return None
    return sections


def update_json_with_ocr() -> None:
    pytesseract.pytesseract.tesseract_cmd = find_tesseract()
    data = load_data()
    hints = load_hints()
    collection_log = load_collection_log()
    now = datetime.now(SEOUL)
    data["date_label"] = f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAYS[now.weekday()]}"

    logs: list[dict] = []
    for restaurant in data.get("restaurants", []):
        name = restaurant.get("name", "")
        config = SOURCE_CONFIG.get(name)
        if not config:
            continue
        image_path = config["image"]
        if name == "에스제이 구내식당" and SJ_WEEKLY_IMAGE_PATH.exists():
            image_path = SJ_WEEKLY_IMAGE_PATH
            restaurant["preview_image"] = "./images/sj-weekly-menu.png"
        if not image_path.exists():
            logs.append({"name": name, "updated": False, "reason": "image_missing"})
            continue
        source_fetched_at = get_source_fetched_at(name, image_path, collection_log)
        recorded_source_at = parse_logged_time(restaurant.get("menu_recorded_source_fetched_at"))
        if source_fetched_at and recorded_source_at and recorded_source_at >= source_fetched_at:
            logs.append(
                {
                    "name": name,
                    "items": len(restaurant.get("menu", [])),
                    "updated": True,
                    "used_existing_fallback": True,
                    "reason": "already_recorded",
                    "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            continue
        previous_menu = list(restaurant.get("menu", []))
        hint_entry = hints.get(name, {})
        hint_text = hint_entry.get("alt_text", "")
        fetched_recently = is_recent_fetch(source_fetched_at, now)
        if name == "에스제이 구내식당":
            if SJ_WEEKLY_IMAGE_PATH.exists():
                sections, today_marker = parse_sj_weekly_image(SJ_WEEKLY_IMAGE_PATH, now)
                if sections and fetched_recently and today_marker:
                    restaurant["menu_sections"] = [{"title": title, "items": items} for title, items in sections.items()]
                    flat_menu = []
                    for items in sections.values():
                        flat_menu.extend(items)
                    restaurant["menu"] = flat_menu
                    restaurant["menu_recorded_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    restaurant["menu_recorded_source_fetched_at"] = source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else now.strftime("%Y-%m-%d %H:%M:%S")
                    logs.append(
                        {
                            "name": name,
                            "items": len(flat_menu),
                            "updated": True,
                            "used_existing_fallback": False,
                            "today_marker": True,
                            "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                        }
                    )
                    continue
                logs.append(
                    {
                        "name": name,
                        "items": len(previous_menu),
                        "updated": False,
                        "used_existing_fallback": True,
                        "reason": "today_marker_not_found" if fetched_recently else "source_not_recent",
                        "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                    }
                )
                continue
            sections = parse_sj_sections_from_hint(hint_text)
            today_marker = has_today_marker([hint_text], now)
            if sections and fetched_recently and today_marker:
                restaurant["menu_sections"] = [{"title": title, "items": items} for title, items in sections.items()]
                flat_menu = []
                for items in sections.values():
                    flat_menu.extend(items)
                restaurant["menu"] = flat_menu
                restaurant["menu_recorded_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
                restaurant["menu_recorded_source_fetched_at"] = source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else now.strftime("%Y-%m-%d %H:%M:%S")
                logs.append(
                    {
                        "name": name,
                        "items": len(flat_menu),
                        "updated": True,
                        "used_existing_fallback": False,
                        "today_marker": True,
                        "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                    }
                )
                continue
            logs.append(
                {
                    "name": name,
                    "items": len(previous_menu),
                    "updated": False,
                    "used_existing_fallback": True,
                    "reason": "today_marker_not_found" if fetched_recently else "source_not_recent",
                    "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                }
            )
            continue
        texts = ocr_texts(image_path)
        if name == "다시 봄":
            texts.extend(ocr_dasibom_crops(image_path))
        today_marker = has_today_marker(texts + ([hint_text] if hint_text else []), now)
        if not fetched_recently or not today_marker:
            logs.append(
                {
                    "name": name,
                    "items": len(previous_menu),
                    "updated": False,
                    "used_existing_fallback": True,
                    "reason": "today_marker_not_found" if fetched_recently else "source_not_recent",
                    "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                }
            )
            continue
        extracted_menu, used_fallback = parse_restaurant_menu(name, texts, previous_menu)
        restaurant["menu"] = extracted_menu
        if name != "에스제이 구내식당":
            restaurant.pop("menu_sections", None)
        if extracted_menu and not used_fallback:
            restaurant["menu_recorded_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            restaurant["menu_recorded_source_fetched_at"] = source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else now.strftime("%Y-%m-%d %H:%M:%S")
        logs.append(
            {
                "name": name,
                "items": len(extracted_menu),
                "updated": bool(extracted_menu) and not used_fallback,
                "used_existing_fallback": used_fallback,
                "today_marker": today_marker,
                "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
            }
        )

    data["ocr_log"] = logs
    save_data(data)


def main() -> None:
    update_json_with_ocr()
    print("menu json updated from ocr")


if __name__ == "__main__":
    main()
