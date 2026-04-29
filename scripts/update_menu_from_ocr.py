from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

import pytesseract
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "menu-today" / "menu_today.json"
HINTS_PATH = ROOT / "menu-today" / "dynamic_menu_hints.json"
COLLECTION_LOG_PATH = ROOT / "menu-today" / "collection_log.json"
MANUAL_OVERRIDES_PATH = ROOT / "menu-today" / "manual_menu_overrides.json"
SJ_WEEKLY_IMAGE_PATH = ROOT / "menu-today" / "images" / "sj-weekly-menu.png"
SEOUL = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
RECENT_FETCH_WINDOW = timedelta(hours=6)
PARTIAL_MENU_MIN_ITEMS = 1

SOURCE_CONFIG = {
    "아이밀": {"image": ROOT / "menu-today" / "images" / "imeal.png", "min_items": 8, "max_items": 14},
    "다시 봄": {"image": ROOT / "menu-today" / "images" / "dasibom.png", "min_items": 6, "max_items": 12},
    "밥(온) 구내식당": {"image": ROOT / "menu-today" / "images" / "babon.png", "min_items": 8, "max_items": 12},
    "구내식당라온푸드": {"image": ROOT / "menu-today" / "images" / "raonfood.png", "min_items": 8, "max_items": 12},
    "마이푸드": {"image": ROOT / "menu-today" / "images" / "myfood.png", "min_items": 8, "max_items": 12},
    "퍼블릭가산 구내식당": {"image": ROOT / "menu-today" / "images" / "public-gasan.png", "min_items": 3, "max_items": 4},
    "더푸드스케치": {"image": ROOT / "menu-today" / "images" / "thefoodsketch.png", "min_items": 9, "max_items": 12},
    "스타밸리푸드포유": {"image": ROOT / "menu-today" / "images" / "starvalley-food4u-post.png", "min_items": 8, "max_items": 12},
    "디폴리스 구내식당": {"image": ROOT / "menu-today" / "images" / "dipolis.png", "min_items": 3, "max_items": 20},
    "에스제이 구내식당": {"image": ROOT / "menu-today" / "images" / "sj-food-menu.png", "min_items": 10, "max_items": 16},
}

SAFE_FALLBACK_ONLY = {"퍼블릭가산 구내식당"}

REPLACEMENTS = {
    "대파숫불치킨바베큐": "대파숯불치킨바베큐",
    "판고기 사전": "철판고기산적",
    "샐러": "샐러드",
    "까드": "깍두기",
    "프라면": "라면",
    "불고 기": "불고기",
    "볼어묵볶음": "불어묵볶음",
    "가든샐러드&오렌지ㅁ": "가든샐러드&오렌지D",
    "가든샐러드 & 흑임자ㅁ": "가든샐러드 & 흑임자D",
    "가든샐러드 & 흑임자ㅁ2": "가든샐러드 & 흑임자D",
    "백미밤 / ae": "백미밥 / 흑미밥",
    "배주겉절이": "배추겉절이",
    "배주끝절이짐지": "배추겉절이김치",
    "셀프비빔밤": "셀프비빔밥",
    "치킨덴더샐러뜨": "치킨텐더샐러드",
    "치킨덴더샐러드뜨": "치킨텐더샐러드",
    "치킨덴더샐러드": "치킨텐더샐러드",
    "흰쌀밥/검은쌀잡곡밥": "흰쌀밥 / 검은쌀잡곡밥",
    "린쌀밥 / 검은쌀잡": "흰쌀밥 / 검은쌀잡곡밥",
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
    "실곤약야채무침": "실곤약 야채 무침",
    "셀라면": "셀프라면",
    "오징어젓갈오돌무침": "오징어젓갈무침",
    "햄쌀밥": "흰쌀밥",
    "Sq": "누룽지",
    "지킨": "치킨",
    "얼길이": "얼갈이",
    "고주군만두": "고추군만두",
    "데미s": "데미S",
    "데미5": "데미S",
    "데미6": "데미S",
    "= 버섯두부조림": "버섯두부조림",
    "기 견과류멸치볶음": "견과류멸치볶음",
    "Ww 숙주나물": "숙주나물",
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

COMMON_MENU_TERMS = {
    "백미밥",
    "잡곡밥",
    "흑미밥",
    "흰쌀밥 / 검은쌀잡곡밥",
    "백미밥 / 흑미밥",
    "백미밥 / 잡곡밥",
    "포기김치",
    "배추김치",
    "배추겉절이",
    "국내산 포기김치",
    "그린샐러드",
    "그린샐러드&드레싱",
    "가든샐러드",
    "가든샐러드&드레싱",
    "샐러드 & 드레싱",
    "셀프라면",
    "셀프 라면",
    "한강라면",
    "탄산음료",
    "숭늉",
    "숭늉 & 음료",
    "헛개차 / 탄산음료",
    "계란후라이",
    "계란후라이 / 토스트&딸기잼",
    "오렌지",
    "깍두기",
    "계절나물",
    "추가찬2종",
}


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


def load_manual_overrides() -> dict:
    if not MANUAL_OVERRIDES_PATH.exists():
        return {}
    return json.loads(MANUAL_OVERRIDES_PATH.read_text(encoding="utf-8-sig"))


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


def is_current_week_fetch(fetched_at: datetime | None, now: datetime) -> bool:
    if not fetched_at:
        return False
    return fetched_at.isocalendar()[:2] == now.isocalendar()[:2]


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


def has_dipolis_meal_marker(texts: list[str]) -> bool:
    merged = "\n".join(texts)
    return bool(re.search(r"저\s*녁|점\s*심|중\s*식|아\s*침|조\s*식|5\s*시\s*10\s*분|6\s*시\s*30\s*분", merged))


def parse_dipolis_menu_sections(texts: list[str], config: dict) -> dict[str, list[str]] | None:
    merged = "\n".join(texts)
    title = "석식" if re.search(r"저\s*녁|5\s*시\s*10\s*분|6\s*시\s*30\s*분", merged) else "중식"
    patterns = [
        (r"잡곡밥\s*/\s*흰쌀밥|잘곡밥\s*/\s*흰쌀밥|잡곡밥.*흰쌀밥", "잡곡밥 / 흰쌀밥"),
        (r"베이컨\s*김치\s*볶음밥", "베이컨 김치 볶음밥"),
        (r"목살\s*버섯\s*불고기", "목살 버섯 불고기"),
        (r"수제\s*치킨\s*텐더\s*&\s*교촌간장소스|수제\s*치킨\s*텐더.*교촌간장소스", "수제 치킨 텐더 & 교촌간장소스"),
        (r"구수한\s*누룽지\s*/\s*프렌치\s*토스트|구수한\s*Sq\s*/\s*프렌치\s*토스트", "구수한 누룽지 / 프렌치 토스트"),
        (r"미트볼\s*폭찹\s*스테이크조림|미트볼.*스테이크조림", "미트볼 폭찹 스테이크조림"),
        (r"시금치\s*된장국|금치\s*된장국", "시금치 된장국"),
        (r"매운\s*국물\s*떡볶이\s*/\s*돌나물\s*매실초장", "매운 국물 떡볶이 / 돌나물 매실초장"),
        (r"양배추\s*야채\s*샐러드", "양배추 야채 샐러드"),
        (r"열무\s*얼갈이\s*김치|열무\s*얼갈이\s*ZAI", "열무 얼갈이 김치"),
        (r"탄\s*산\s*음료", "탄산음료"),
        (r"돼지\s*양념\s*구이", "돼지 양념 구이"),
        (r"순살\s*후라이드|후라이드\s*&\s*매운소스", "순살 후라이드 & 매운소스"),
        (r"두부구이\s*양념\s*조림|툴로.*양념\s*소림|두부.*양념\s*조림", "두부구이 양념 조림"),
        (r"얼.?갈.?이\s*된장국|열갈이\s*된장국", "얼갈이 된장국"),
        (r"실.?곤약\s*야채\s*무침|곤약\s*야재\s*무진", "실곤약 야채 무침"),
        (r"양상추\s*야채\s*샐러드", "양상추 야채 샐러드"),
        (r"국산\s*포기김치|국산포기김치", "국산 포기김치"),
        (r"탄\s*산\s*음료|EAA\s*음료|Eb\s*At", "탄산음료"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    if len(found) < config["min_items"]:
        return None
    return {title: found[: config["max_items"]]}


def has_raon_today_marker(texts: list[str], now: datetime) -> bool:
    merged = "\n".join(texts)
    patterns = [
        rf"{now.year}\s*년?\s*{now.month}\s*월?\s*{now.day}\s*일?",
        rf"{str(now.year)[-2:]}\s*년?\s*{now.month}\s*월?\s*{now.day}\s*일?",
        rf"{now.month}\s*월?\s*{now.day}\s*일",
    ]
    return any(re.search(pattern, merged) for pattern in patterns)


def has_raon_other_day_marker(texts: list[str], now: datetime) -> bool:
    merged = "\n".join(texts)
    day_matches = [int(match) for match in re.findall(r"(\d{1,2})\s*일", merged)]
    return any(day != now.day for day in day_matches)


def has_public_gasan_week_marker(texts: list[str], now: datetime) -> bool:
    merged = "\n".join(texts)
    monday = now - timedelta(days=now.weekday())
    friday = monday + timedelta(days=4)
    patterns = [
        rf"{monday.year % 100}\s*년\s*{monday.month}\s*월\s*{monday.day}\s*일\s*~\s*{friday.year % 100}\s*년\s*{friday.month}\s*월\s*{friday.day}\s*일",
        rf"{monday.month}\s*월\s*{monday.day}\s*일\s*~\s*.*{friday.month}\s*월\s*{friday.day}\s*일",
        rf"{now.day}\s*일",
    ]
    return any(re.search(pattern, merged) for pattern in patterns)


def parse_public_gasan_menu(texts: list[str], now: datetime) -> list[str]:
    merged = "\n".join(texts)
    if now.weekday() not in (1, 2):
        return []
    weekly_fixed = {
        1: ["이모카세 닭갈비", "임연수구이", "김말이튀김"],
        2: ["생선까스 & 어니언콘소스", "의정부대볶음", "얼큰참치순두부국"],
    }
    if has_public_gasan_week_marker(texts, now):
        return weekly_fixed[now.weekday()]
    if now.weekday() == 1:
        patterns = [
            (r"이모카세\s*닭갈비|이모카세[\s\S]{0,80}닭갈비", "이모카세 닭갈비"),
            (r"임연수구이", "임연수구이"),
            (r"김말이튀김", "김말이튀김"),
        ]
    else:
        patterns = [
            (r"생선까스\s*&\s*어니언콘소스|생선까스[\s\S]{0,40}어니언콘소", "생선까스 & 어니언콘소스"),
            (r"의정부대볶음", "의정부대볶음"),
            (r"얼큰참치\s*순두부국|얼큰참치[\s\S]{0,20}순두부국", "얼큰참치순두부국"),
        ]
    return extract_pattern_matches_in_order(merged, patterns)


def extract_sj_section_lines(image: Image.Image) -> list[str]:
    texts = ocr_image_variants(image)
    merged = "\n".join(texts)
    section_patterns = [
        (r"얼큰김치수제비", "얼큰김치수제비"),
        (r"소고기콩나물밥", "소고기콩나물밥(우육:호주산)"),
        (r"후라이드치킨", "후라이드치킨(계육:국산) * 소스"),
        (r"매콤순대볶음", "매콤순대볶음(돈혈:국산)"),
        (r"깻잎옥수수맛살전|T[il1]O.*OFA", "깻잎옥수수맛살전"),
        (r"매콤두부조림|매콤[\s\S]{0,12}부조림", "매콤두부조림"),
        (r"청경채[걸겉]절이", "청경채겉절이"),
        (r"버섯순두부찌개|셔수드브[\s\S]{0,16}찌개|셔소드브[\s\S]{0,16}찌개", "버섯순두부찌개"),
        (r"잡곡밥", "잡곡밥"),
        (r"오징어돈육볶음|징어돈육볶음", "오징어돈육볶음(오징어:중국산, 돈육:국산)"),
        (r"치즈돈까스", "치즈돈까스(돈육:국산) * 소스"),
        (r"오색산적구이", "오색산적구이"),
        (r"미역[줄즐]기[볶뷰]음", "미역줄기볶음"),
        (r"계절나물", "계절나물"),
        (r"배[추주]김치|베[추주]김치", "배추김치"),
        (r"그린샐러드", "그린샐러드"),
        (r"추가찬2종|주가찬2종", "추가찬2종"),
    ]
    patterned = extract_pattern_matches_in_order(merged, section_patterns)
    if len(patterned) >= 6:
        return patterned

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
    plus_keys = {canonical_key(item) for item in plus_menu}
    lunch_items = [item for item in lunch_items if canonical_key(item) not in plus_keys]
    dinner_items = [item for item in dinner_items if canonical_key(item) not in plus_keys]

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


def normalize_fixed_menu_terms(line: str) -> str:
    line = re.sub(r"샐러드드+|샐러드뜨|샐러뜨|샘러드|셀러드|셀러뜨|싱싱샐러드드+", "샐러드", line)
    line = re.sub(r"그린샐러드(?!\s*&)", "그린샐러드", line)
    line = re.sub(r"가든샐러드(?!\s*&)", "가든샐러드", line)
    line = re.sub(r"드레심|드래싱|드레신|드래심|드레씽", "드레싱", line)
    line = re.sub(r"숭능|숭눙|숭뉵|승능|숭늬", "숭늉", line)
    line = re.sub(r"\s*&\s*", " & ", line)
    line = re.sub(r"\s*/\s*", " / ", line)
    line = re.sub(r"\s+", " ", line)
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


def menu_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, canonical_key(left), canonical_key(right)).ratio()


def is_suspicious_menu_item(line: str) -> bool:
    if not line:
        return True
    if re.search(r"[€£¥¢]", line):
        return True
    if re.search(r"[<>\\\\'\"{}\\[\\]@]", line):
        return True
    if re.search(r"[ㄱ-ㅎㅏ-ㅣ]", line):
        return True
    if re.search(r"\b[A-Za-z]\d|\d[A-Za-z]", line):
        return True
    if re.search(r"^\d+\s+", line):
        return True
    if re.search(r"\d", line) and not re.search(r"(추가찬\s*\d+종|\d+종|[A-Za-z]D|st)", line):
        return True
    if len(re.findall(r"[A-Za-z]", line)) >= 3:
        allowed = re.sub(r"\b(?:D|S|JPG|JPEG)\b", "", line)
        if len(re.findall(r"[A-Za-z]", allowed)) >= 2:
            return True
    compact = canonical_key(line)
    korean_count = len(re.findall(r"[가-힣]", compact))
    if korean_count < 2:
        return True
    if len(compact) >= 8 and korean_count / max(len(compact), 1) < 0.45:
        return True
    return False


def normalize_final_line(line: str) -> str:
    line = clean_line(line)
    line = re.sub(r"^[@#]+\s*", "", line)
    line = re.sub(r"\([^)]*\)", "", line)
    line = re.sub(r"\[[^\]]*\]", "", line)
    line = normalize_fixed_menu_terms(line)
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
    first_line: dict[str, str] = {}
    first_index: dict[str, int] = {}
    for idx, item in enumerate(candidates):
        key = canonical_key(item)
        first_line.setdefault(key, normalize_final_line(item))
        first_index.setdefault(key, idx)
    ordered = sorted(first_line, key=lambda key: first_index[key])
    return [first_line[key] for key in ordered]


def has_recorded_menu(restaurant: dict) -> bool:
    if restaurant.get("menu"):
        return True
    for section in restaurant.get("menu_sections", []):
        if section.get("items"):
            return True
    return False


def count_menu_items(restaurant: dict) -> int:
    if restaurant.get("menu_sections"):
        return sum(len(section.get("items", [])) for section in restaurant.get("menu_sections", []))
    return len(restaurant.get("menu", []))


def mark_menu_uncollected(restaurant: dict) -> None:
    restaurant["menu"] = []
    restaurant.pop("menu_sections", None)
    restaurant["message"] = "오늘 메뉴 미수집 상태입니다."


def collect_menu_items_from_entry(entry: dict) -> list[str]:
    items = list(entry.get("menu", []))
    for section in entry.get("menu_sections", []):
        items.extend(section.get("items", []))
    return items


def collect_known_menu_terms(data: dict, overrides: dict) -> set[str]:
    terms = set(COMMON_MENU_TERMS)
    # Do not learn from menu_today.json itself: one bad OCR run can otherwise
    # become a "known good" menu and keep passing future validation.
    for day in overrides.values():
        for restaurant in day.get("restaurants", {}).values():
            for item in collect_menu_items_from_entry(restaurant):
                normalized = normalize_final_line(item)
                if normalized and not is_suspicious_menu_item(normalized):
                    terms.add(normalized)
    return terms


def menu_output_quality_ok(restaurant: dict) -> bool:
    items = collect_menu_items_from_entry(restaurant)
    if not items:
        return False
    return not any(is_suspicious_menu_item(normalize_final_line(item)) for item in items)


def find_best_known_term(item: str, known_terms: set[str]) -> tuple[str | None, float]:
    if not known_terms:
        return None, 0.0
    best_term = None
    best_score = 0.0
    item_key = canonical_key(item)
    for term in known_terms:
        term_key = canonical_key(term)
        if not item_key or not term_key:
            continue
        score = SequenceMatcher(None, item_key, term_key).ratio()
        if score > best_score:
            best_term = term
            best_score = score
    return best_term, best_score


def repair_menu_items(items: list[str], known_terms: set[str], max_items: int) -> tuple[list[str], int]:
    repaired: list[str] = []
    rejected = 0
    seen: set[str] = set()

    for raw_item in items:
        item = normalize_final_line(raw_item)
        if not item:
            continue
        best_term, score = find_best_known_term(item, known_terms)
        if best_term and (score >= 0.86 or (is_suspicious_menu_item(item) and score >= 0.66)):
            item = best_term
        item = normalize_final_line(item)
        if is_suspicious_menu_item(item):
            rejected += 1
            continue
        key = canonical_key(item)
        if key in seen:
            continue
        seen.add(key)
        repaired.append(item)
        if len(repaired) >= max_items:
            break
    return repaired, rejected


def validate_extracted_menu(
    name: str,
    items: list[str],
    known_terms: set[str],
    strict_min: bool = True,
) -> tuple[list[str], bool, int]:
    config = SOURCE_CONFIG[name]
    repaired, rejected = repair_menu_items(items, known_terms, config["max_items"])
    if not repaired:
        return [], False, rejected

    minimum = config["min_items"] if strict_min else PARTIAL_MENU_MIN_ITEMS
    if name == "퍼블릭가산 구내식당":
        minimum = 3
    if len(repaired) < minimum:
        return repaired, False, rejected
    if strict_min and rejected > max(2, len(repaired)):
        return repaired, False, rejected
    return repaired, True, rejected


def validate_menu_sections(
    name: str,
    sections: dict[str, list[str]],
    known_terms: set[str],
) -> tuple[dict[str, list[str]], bool, int]:
    fixed_sections: dict[str, list[str]] = {}
    rejected_total = 0
    useful_count = 0
    for title, items in sections.items():
        if title == "플러스메뉴":
            fixed_sections[title] = items
            continue
        fixed, _, rejected = validate_extracted_menu(name, items, known_terms, strict_min=False)
        rejected_total += rejected
        if fixed:
            fixed_sections[title] = fixed
            useful_count += len(fixed)
    if sections.get("플러스메뉴"):
        fixed_sections["플러스메뉴"] = sections["플러스메뉴"]
    return fixed_sections, useful_count >= 4, rejected_total


def apply_manual_overrides(data: dict, logs: list[dict], now: datetime) -> None:
    overrides = load_manual_overrides()
    date_key = now.strftime("%Y-%m-%d")
    date_overrides = overrides.get(date_key, {}).get("restaurants", {})
    if not date_overrides:
        return

    logs_by_name = {log.get("name"): log for log in logs}
    recorded_at = now.strftime("%Y-%m-%d %H:%M:%S")

    for restaurant in data.get("restaurants", []):
        name = restaurant.get("name", "")
        override = date_overrides.get(name)
        if not override:
            continue

        if "status" in override:
            restaurant["status"] = override["status"]
        if "message" in override:
            restaurant["message"] = override["message"]
        if "preview_image" in override:
            restaurant["preview_image"] = override["preview_image"]

        sections = override.get("menu_sections")
        if sections:
            restaurant["menu_sections"] = sections
            flat_menu: list[str] = []
            for section in sections:
                flat_menu.extend(section.get("items", []))
            restaurant["menu"] = flat_menu
        else:
            restaurant["menu"] = override.get("menu", restaurant.get("menu", []))
            restaurant.pop("menu_sections", None)

        restaurant["menu_recorded_at"] = recorded_at
        restaurant["menu_recorded_source_fetched_at"] = restaurant.get("menu_recorded_source_fetched_at") or recorded_at
        restaurant["menu_recent_source_today"] = True

        log = logs_by_name.get(name)
        if not log:
            log = {"name": name}
            logs.append(log)
            logs_by_name[name] = log
        log.update(
            {
                "items": count_menu_items(restaurant),
                "updated": True,
                "used_existing_fallback": False,
                "manual_override": True,
                "today_marker": True,
                "source_fetched_at": restaurant.get("menu_recorded_source_fetched_at", ""),
            }
        )


def extract_missing_menu_candidates(name: str, texts: list[str]) -> list[str]:
    config = SOURCE_CONFIG[name]
    candidates = collect_candidates(texts)
    deduped = dedupe_candidates(candidates)
    if name == "퍼블릭가산 구내식당":
        keywords = ["주물럭", "카레", "전", "볶음", "덮밥", "탕", "찌개", "국", "밥"]
        filtered = [item for item in deduped if any(keyword in item for keyword in keywords)]
        limit = 4
        minimum = 2
    else:
        filtered = [
            item
            for item in deduped
            if not any(token in item for token in ["셀프", "간편식", "탄산음료", "헛개차", "숭늉"])
        ]
        if not filtered:
            filtered = deduped
        limit = config["max_items"]
        minimum = PARTIAL_MENU_MIN_ITEMS
    result = filtered[:limit]
    if len(result) < minimum:
        return []
    return result


def extract_pattern_matches_in_order(merged: str, patterns: list[tuple[str, str]]) -> list[str]:
    matches: list[tuple[int, str]] = []
    for pattern, label in patterns:
        found = re.search(pattern, merged)
        if found:
            matches.append((found.start(), label))
    matches.sort(key=lambda item: item[0])
    ordered: list[str] = []
    for _, label in matches:
        if label not in ordered:
            ordered.append(label)
    return ordered


def extract_pattern_matches_by_pattern_order(merged: str, patterns: list[tuple[str, str]]) -> list[str]:
    ordered: list[str] = []
    for pattern, label in patterns:
        if re.search(pattern, merged) and label not in ordered:
            ordered.append(label)
    return ordered


def parse_dasibom_menu(texts: list[str], config: dict) -> list[str]:
    merged = "\n".join(texts)
    patterns = [
        (r"파송송계란탕", "파송송계란탕"),
        (r"사[천전]\s*보차이불고기|사천보차이불고기|사전보차이불고기", "사천보차이불고기"),
        (r"[통동등]살생선까스", "통살생선까스"),
        (r"삼각군만두부침", "삼각군만두부침"),
        (r"미트스파게티", "미트스파게티"),
        (r"수제.?깻잎지|수제.?껏임지|스제깨잎지", "수제깻잎지"),
        (r"싱싱샐러드+", "싱싱샐러드"),
        (r"깍두기|까두기|깟두기|7\s*7[\]\|]", "깍두기"),
        (r"참치마요비빔밥", "참치마요비빔밥"),
        (r"탄산음료|타.?산.?음.?료|타사을", "탄산음료"),
        (r"셀프\s*라면|셀프라면", "셀프라면"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    if len(found) >= max(8, config["min_items"] - 1):
        return found[: config["max_items"]]
    return []


def parse_imeal_menu(texts: list[str], config: dict) -> list[str]:
    merged = "\n".join(texts)
    patterns = [
        (r"근대된장국", "근대된장국"),
        (r"[고구]추?장제육볶음|직화고추장제육볶음", "고추장제육볶음(돈육:미국산)"),
        (r"야채고로케\s*&\s*케찹|야채고로케.*케찹", "야채고로케 & 케찹"),
        (r"베이컨감자채볶음", "베이컨감자채볶음"),
        (r"오이무침", "오이무침"),
        (r"양배추숙쌈\s*&\s*우렁강된장|양배추숙쌈.*우렁강된장", "양배추숙쌈 & 우렁강된장"),
        (r"가든샐러드\s*&\s*흑임자[DOㅁ0]", "가든샐러드 & 흑임자D"),
        (r"국내산\s*포기김치|포기김치", "국내산 포기김치"),
        (r"백미밥\s*/\s*흑미밥|백미밤\s*/\s*ae", "백미밥 / 흑미밥"),
        (r"둥굴레차\s*/\s*탄산음료|둥굴레차", "둥굴레차 / 탄산음료"),
        (r"셀프비빔밥\s*/\s*한강라면|셀프비빔밥.*한강라면", "셀프비빔밥 / 한강라면"),
        (r"간편식:\s*치킨[텐덴]더샐러드|치킨[텐덴]더샐러드", "간편식: 치킨텐더샐러드"),
        (r"콩나물김치국|롱나물김짓국|콩나물김짓국", "콩나물김치국"),
        (r"소불고기납작당면볶음|납작당면볶음", "소불고기납작당면볶음"),
        (r"수제오징어김치전", "수제오징어김치전"),
        (r"두부조림", "두부조림"),
        (r"숙주나물", "숙주나물"),
        (r"치커리유자청무침", "치커리유자청무침"),
        (r"가든샐러드\s*&\s*요거트D|가든샐러드.*요거트[DOㅁ0]", "가든샐러드 & 요거트D"),
        (r"국내산\s*배추겉절이|배추겉절이", "국내산 배추겉절이"),
        (r"백미밥\s*/\s*흑미밥|백미밥흑미밥", "백미밥 / 흑미밥"),
        (r"헛개차\s*/\s*탄산음료|AWWA\s*/\s*탄산음료|헛개차.*탄산음료|[AS][WH]A\s*/\s*탄산음료", "헛개차 / 탄산음료"),
        (r"셀프비빔밥\s*/\s*한강라면|셀프비빔밥.*한강라면", "셀프비빔밥 / 한강라면"),
        (r"간편식:\s*훈제닭가슴살샐러드|훈제닭가슴살샐러드", "간편식: 훈제닭가슴살샐러드"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    main_items = ["고추장제육볶음(돈육:미국산)"]
    for main_item in main_items:
        if main_item in found:
            found.remove(main_item)
            insert_at = 1 if found and found[0] == "근대된장국" else 0
            found.insert(insert_at, main_item)
    if len(found) >= config["min_items"]:
        return found[: config["max_items"]]
    return []


def parse_babon_menu(texts: list[str], config: dict) -> list[str]:
    merged = "\n".join(texts)
    patterns = [
        (r"흰쌀밥\s*/\s*검은쌀잡곡밥|린쌀밥\s*/\s*검은쌀잡", "흰쌀밥 / 검은쌀잡곡밥"),
        (r"무우어묵탕|무우\s*어묵탕", "무우어묵탕"),
        (r"치즈닭갈비볶음|지즈닭갈비볶음|지즈닭깔비볶음", "치즈닭갈비볶음"),
        (r"그릴떡갈비채소구이|그림떡갈비재소구이|그릴떡갈비재소", "그릴떡갈비채소구이"),
        (r"새우계란볶음밥", "새우계란볶음밥"),
        (r"바삭햄김치전", "바삭햄김치전"),
        (r"메추리알마요샐러드|메주리알마요샐러드", "메추리알마요샐러드"),
        (r"청경채겉절이|청경채거절이", "청경채겉절이"),
        (r"배추겉절이김치|배주끝절이짐지", "배추겉절이김치"),
        (r"양배추샐러드\s*/\s*식빵러스크|양배주샐러드\s*/\s*식빵러스크", "양배추샐러드 / 식빵러스크"),
        (r"흰쌀밥\s*/\s*검은쌀잡곡밥|흰쌀밥검은쌀잡곡밥|히.?식.?[빠빨].*쌍.?잡|힌.?쌀.?밥.*검.?은.?쌀.?잡|[윈흰]쌀밥[\s/]*[끔검].?은쌀[\s/]*[삽잡]곡[\s/]*밥|쌀밥[\s/]*.*은쌀[\s/]*.*곡[\s/]*밥", "흰쌀밥 / 검은쌀잡곡밥"),
        (r"소갈비탕", "소갈비탕"),
        (r"불맛직화제육볶음", "불맛직화제육볶음"),
        (r"순살생선까스\*?감자튀김|순살생선까스.*감자튀김|순살생.?선.?까스.*감자튀", "순살생선까스*감자튀김"),
        (r"부대소시지떡볶이", "부대소시지떡볶이"),
        (r"분홍소시지전\*?동그랑땡|분홍소시지전.*동그랑땡|BE\s*GARE.*Tapa|PSSaAlnl.*12h", "분홍소시지전*동그랑땡"),
        (r"간장연근조림", "간장연근조림"),
        (r"얼갈이겉절이무침|얼.?갈.?이.?겉절이무침|6071.*기거", "얼갈이겉절이무침"),
        (r"알타리총각김치|알타리총각김지|알타리롱각김치|알타리.*ae.*Al", "알타리총각김치"),
        (r"양배추샐러드\s*/\s*모듬상추쌈|양배추샐러드.*모듬상추쌈|양배.?주.*[샘삼]러드.*모듬상.?[주추].?쌈|양배.?주.*모듬상.?[주추].?쌈", "양배추샐러드/모듬상추쌈"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    if (
        all("흰쌀밥 / 검은쌀잡곡밥" != item for item in found)
        and re.search(r"쌀밥|쌍.?잡|삽곡|잡곡", merged)
    ):
        found.insert(0, "흰쌀밥 / 검은쌀잡곡밥")
    if len(found) >= max(8, config["min_items"] - 2):
        return found[: config["max_items"]]
    return []


def parse_raonfood_menu(texts: list[str], config: dict) -> list[str]:
    merged = "\n".join(texts)
    patterns = [
        (r"소고.?기.?미역국|소고\s*\)\|0\|역국", "소고기미역국"),
        (r"닭다리닭볶음[탕탐]|맑다리닭볶음[탕탐]", "닭다리닭볶음탕"),
        (r"멘[치지]볼카츠\s*/\s*데.?미소스|멘치불카츠\s*/\s*데.?미소스", "멘치볼카츠 / 데미소스"),
        (r"마늘쫑한입떡갈비조림|마늘.*한입떡갈비조림", "마늘쫑한입떡갈비조림"),
        (r"김풍st비빔파스타|김풍.?s?t.?비빔파스타|김풍.*빔파스타", "김풍st비빔파스타"),
        (r"오징어젓갈무침|오짐머첫갈무침", "오징어젓갈무침"),
        (r"시금치나물|시금지나물", "시금치나물"),
        (r"셀프라면\s*&\s*배추김치|셀프라면.*배추김치|셀프라면.*배주김지", "셀프라면 & 배추김치"),
        (r"샐러드\s*&\s*드레싱|샐러드.*드레심|샐러드.*Sela", "샐러드 & 드레싱"),
        (r"숭늉\s*&\s*음료|zs\s*&\s*을료|ss\s*&\s*음료", "숭늉 & 음료"),
        (r"우엉김밥|무엄김밥", "우엉김밥"),
        (r"순두부찌개", "순두부찌개"),
        (r"소고기불고기|소.?고.?[기\)\|].*불고", "소고기불고기"),
        (r"핫도그\s*/\s*케첩|핫도그/\s*케첩|핫도그/\s*케접|핫도그/\ucf00\uc811", "핫도그 / 케첩"),
        (r"닭안심바비큐소스구이|닭안심바비[큐버]소스구[이0]|\ub2ed\uc548\uc2ec\ubc14\ube44\ud050\uc18c\uc2a4\uad6c0", "닭안심바비큐소스구이"),
        (r"오색경단|오색겸단|모색경단|모색겸단", "오색경단"),
        (r"빨강콩나물|빨감콩나물|빨강공나물", "빨강콩나물"),
        (r"셀프라면\s*&\s*배추김치|셀프라면.*배추김치|ss\s*&\s*32|a5\s*&\s*22", "셀프라면 & 배추김치"),
        (r"샐러드\s*&\s*드레싱|그린샐러드|샐러드드드.*드레싱|샐러드.*드레심|샐러드드\s*&", "샐러드 & 드레싱"),
        (r"숭늉\s*&\s*음료|숭늉.*음료|[sSaA][s5]\s*&\s*[23][22]|ss\s*&\s*SF", "숭늉 & 음료"),
        (r"[닭닥]곰[탕탐]\s*/\s*[다타]대[기\)\!]|[닭닥]곰[탕탐]다대기|[닭닥]곰[탕탐][\/\|]다대", "닭곰탕/다대기"),
        (r"치즈불닭볶음|지즈불닭볶음", "치즈불닭볶음"),
        (r"오리엔탈파채돈까스|오리엔탈파채돈가스|오리엔탈파재돈까스", "오리엔탈파채돈까스"),
        (r"참치김치볶음\s*&\s*두부|참치김치볶음.*두부|참치김치볶음6두부", "참치김치볶음&두부"),
        (r"콘스크램블드에그|곤스크램블드에그|콘스크랩블드메그", "콘스크램블드에그"),
        (r"청포묵김가루무침|청포묵김가루묻침|정포묵김가루무침|첨포묵김가루무침", "청포묵김가루무침"),
        (r"백미밥\s*&\s*잡곡밥|백미밥잡곡밥|백\[\|밥.?잡곡밥", "백미밥&잡곡밥"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    if len(found) >= max(7, config["min_items"] - 3):
        return found[: config["max_items"]]
    return []


def parse_myfood_menu(texts: list[str], config: dict) -> list[str]:
    merged = "\n".join(texts)
    patterns = [
        (r"미나리대패볶음", "미나리대패볶음"),
        (r"생선까스\s*&\s*타르소스|생선까스&타르소스", "생선까스 & 타르소스"),
        (r"해물크림짬뽕면", "해물크림짬뽕면"),
        (r"잡채어묵강정", "잡채어묵강정"),
        (r"모듬버섯볶음", "모듬버섯볶음"),
        (r"미역레몬초무침|미역레몬초무짐", "미역레몬초무침"),
        (r"고추잎무말랭이무침\s*/\s*포기김치|무말랭이무짐\s*/\s*포기김치", "고추잎무말랭이무침 / 포기김치"),
        (r"그린샐러드\s*&\s*드레싱|그린샐러드&드레싱", "그린샐러드 & 드레싱"),
        (r"우거지해장국", "우거지해장국"),
        (r"고구마맛탕", "고구마맛탕"),
        (r"잡곡밥\s*/\s*백미밥|잡곡밥 / 백미밥", "잡곡밥 / 백미밥"),
        (r"쌈채소\s*&\s*풋고추\s*/\s*한강라면\s*&\s*달콤한\s*[잼딜]?\s*토스트\s*/\s*구수한\s*[숭승]?[늉능]?\s*&\s*시원한\s*탄산음료|쌈채소[\s\S]*풋고추[\s\S]*한강라면[\s\S]*토스트[\s\S]*탄산음료", "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료"),
        (r"계림닭갈비", "계림닭갈비"),
        (r"생선까스\s*&\s*타르소스|생선까스&타르소스", "생선까스&타르소스"),
        (r"들기름메밀막국수", "들기름메밀막국수"),
        (r"참치무조림", "참치무조림"),
        (r"불어묵피망볶음|봉어묵피망볶음|글어묵피망볶음", "불어묵피망볶음"),
        (r"미역줄기양파볶음|미역술기양파볶음", "미역줄기양파볶음"),
        (r"양념마늘쫑무침\s*/\s*포기김치|양념마늘쫑무침/포기김치|양념마늘.?쫑무침.?/?.?포기.?김치|orsorsten/E7N Lal", "양념마늘쫑무침/포기김치"),
        (r"그린샐러드\s*&\s*드레싱|그린샐러드&드레싱", "그린샐러드&드레싱"),
        (r"청양콩나물국", "청양콩나물국"),
        (r"춘권튀김\s*&\s*칠리소스|준권투 김&칠리소스|춘권튀김&칠리소스", "춘권튀김&칠리소스"),
        (r"잡곡밥\s*/\s*백미밥|잡곡밥 / 백미밥", "잡곡밥 / 백미밥"),
        (r"쌈채소\s*&\s*풋고추\s*/\s*한강라면\s*&\s*달콤한\s*[잼딜]?\s*토스트\s*/\s*구수한\s*[숭승]?[늉능]?\s*&\s*시원한\s*탄산음료|쌈채소[\s\S]*풋고추[\s\S]*한강라면[\s\S]*토스트[\s\S]*탄산음료", "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료"),
    ]
    found = extract_pattern_matches_in_order(merged, patterns)
    if len(found) >= config["min_items"]:
        return found[: config["max_items"]]
    return []


def parse_restaurant_menu(name: str, texts: list[str], existing: list[str]) -> tuple[list[str], bool]:
    config = SOURCE_CONFIG[name]
    if name == "퍼블릭가산 구내식당":
        found = parse_public_gasan_menu(texts, datetime.now(SEOUL))
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name in SAFE_FALLBACK_ONLY:
        return existing, True
    if name == "아이밀":
        found = parse_imeal_menu(texts, config)
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "다시 봄":
        found = parse_dasibom_menu(texts, config)
        if found:
            return found[: config["max_items"]], False
        return existing, True
    if name == "밥(온) 구내식당":
        found = parse_babon_menu(texts, config)
        if found:
            return found[: config["max_items"]], False
        return existing, True
    if name == "구내식당라온푸드":
        found = parse_raonfood_menu(texts, config)
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "마이푸드":
        found = parse_myfood_menu(texts, config)
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "더푸드스케치":
        merged = "\n".join(texts)
        patterns = [
            (r"혼합잡곡밥", "혼합잡곡밥"),
            (r"꼬치어묵탕", "꼬치어묵탕"),
            (r"오리훈제김치볶음", "오리훈제김치볶음"),
            (r"치즈돈까스\s*/\s*데미S|치즈돈까스\s*/\s*데미[5s6]", "치즈돈까스 / 데미S"),
            (r"고추군만두\s*/\s*양념장|고주군만두\s*/\s*양념장", "고추군만두 / 양념장"),
            (r"크래미스크램블에그", "크래미스크램블에그"),
            (r"버섯두부조림", "버섯두부조림"),
            (r"견과류멸치볶음|견과류명\s*치볶음", "견과류멸치볶음"),
            (r"숙주나물", "숙주나물"),
            (r"가든샐러드\s*/\s*드레싱|가든샐러드.*드레싱", "가든샐러드 / 드레싱"),
            (r"얼갈이열무겉절이\s*/\s*음료|얼길이열무겉절이\s*/\s*음료", "얼갈이열무겉절이 / 음료"),
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
        found = extract_pattern_matches_in_order(merged, patterns)
        if len(found) >= config["min_items"]:
            return found[: config["max_items"]], False
        return existing, True
    if name == "스타밸리푸드포유":
        merged = "\n".join(texts)
        patterns = [
            (r"흑미밥\s*/\s*백미밥|흑미밥백미밥|흑미밥;\s*백미밥|라미\s*빈\s*/\s*벼미", "흑미밥 / 백미밥"),
            (r"훈제오리부추볶음|준제오리부주볶음|춘제오리부주볶슴|준제오리부주볶슴", "훈제오리부추볶음"),
            (r"얼큰꽁지어묵국|얼큰꼬지어묵국|얼콘꽁지어묵국|열콘꽁지어묵국", "얼큰꽁지어묵국"),
            (r"남도떡갈비구이|탐도떡갈비구이", "남도떡갈비구이"),
            (r"메추리알떡볶이|메주리알떡볶이|메추리알승주", "메추리알떡볶이"),
            (r"고구마튀김", "고구마튀김"),
            (r"오징어야채초무침|오징어야재초무침|오징어야채조무침|2\s*야\s*0.*채초무침", "오징어야채초무침"),
            (r"열무장무침|열무장무짐", "열무장무침"),
            (r"가든샐러드.*흑임자D|가든샐러드흑임자D|가든셀.*AtD|가든샐러드드.*흑임자|가든샐러드드.*측임자", "가든샐러드 & 흑임자D"),
            (r"포기김치", "포기김치"),
        ]
        found = extract_pattern_matches_in_order(merged, patterns)
        if len(found) >= max(8, config["min_items"] - 2):
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
    manual_overrides = load_manual_overrides()
    known_terms = collect_known_menu_terms(data, manual_overrides)
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
            mark_menu_uncollected(restaurant)
            logs.append({"name": name, "updated": False, "reason": "image_missing"})
            continue
        source_fetched_at = get_source_fetched_at(name, image_path, collection_log)
        recorded_source_at = parse_logged_time(restaurant.get("menu_recorded_source_fetched_at"))
        source_is_today = bool(source_fetched_at and source_fetched_at.date() == now.date())
        source_is_new = bool(source_fetched_at and (not recorded_source_at or recorded_source_at < source_fetched_at))
        if (
            source_fetched_at
            and recorded_source_at
            and source_is_today
            and recorded_source_at.date() == now.date()
            and recorded_source_at >= source_fetched_at
            and has_recorded_menu(restaurant)
            and menu_output_quality_ok(restaurant)
        ):
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
        source_is_current_week = is_current_week_fetch(source_fetched_at, now)
        if name == "에스제이 구내식당":
            if SJ_WEEKLY_IMAGE_PATH.exists():
                sections, today_marker = parse_sj_weekly_image(SJ_WEEKLY_IMAGE_PATH, now)
            else:
                sections = parse_sj_sections_from_hint(hint_text)
                today_marker = has_today_marker([hint_text], now)

            if sections:
                sections, sections_ok, rejected_count = validate_menu_sections(name, sections, known_terms)
            else:
                sections_ok = False
                rejected_count = 0

            if sections and sections_ok and source_is_current_week and today_marker:
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
                        "ocr_rejected_items": rejected_count,
                        "today_marker": True,
                        "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                    }
                )
                continue

            if not source_is_current_week or not today_marker or not sections_ok:
                mark_menu_uncollected(restaurant)
            logs.append(
                {
                    "name": name,
                    "items": 0,
                    "updated": False,
                    "used_existing_fallback": True,
                    "reason": "ocr_low_confidence" if source_is_current_week and today_marker else ("today_marker_not_found" if source_is_current_week else "source_not_current_week"),
                    "ocr_rejected_items": rejected_count,
                    "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                }
            )
            continue
        texts = ocr_texts(image_path)
        if name == "다시 봄":
            texts.extend(ocr_dasibom_crops(image_path))
        today_marker = has_today_marker(texts + ([hint_text] if hint_text else []), now)
        if name == "디폴리스 구내식당" and has_dipolis_meal_marker(texts + ([hint_text] if hint_text else [])):
            today_marker = True
        raon_stale_image = name == "구내식당라온푸드" and has_raon_other_day_marker(texts + ([hint_text] if hint_text else []), now)
        if name == "구내식당라온푸드" and not raon_stale_image and has_raon_today_marker(texts + ([hint_text] if hint_text else []), now):
            today_marker = True
        if name == "퍼블릭가산 구내식당" and has_public_gasan_week_marker(texts + ([hint_text] if hint_text else []), now):
            today_marker = True
        if not source_is_today or not today_marker:
            mark_menu_uncollected(restaurant)
            logs.append(
                {
                    "name": name,
                    "items": 0,
                    "updated": False,
                    "used_existing_fallback": True,
                    "reason": "stale_menu_date" if name == "구내식당라온푸드" and raon_stale_image else ("today_marker_not_found" if source_is_today else "source_not_recent"),
                    "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                }
            )
            continue
        if name == "디폴리스 구내식당":
            sections = parse_dipolis_menu_sections(texts, config)
            if sections:
                sections, sections_ok, rejected_count = validate_menu_sections(name, sections, known_terms)
                if sections_ok:
                    restaurant["menu_sections"] = [{"title": title, "items": items} for title, items in sections.items()]
                    flat_menu = []
                    for items in sections.values():
                        flat_menu.extend(items)
                    restaurant["menu"] = flat_menu
                    restaurant["message"] = ""
                    restaurant["menu_recorded_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    restaurant["menu_recorded_source_fetched_at"] = source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else now.strftime("%Y-%m-%d %H:%M:%S")
                    logs.append(
                        {
                            "name": name,
                            "items": len(flat_menu),
                            "updated": True,
                            "used_existing_fallback": False,
                            "ocr_rejected_items": rejected_count,
                            "today_marker": True,
                            "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
                        }
                    )
                    continue
        extracted_menu, used_fallback = parse_restaurant_menu(name, texts, previous_menu)
        extracted_menu, menu_ok, rejected_count = validate_extracted_menu(
            name,
            extracted_menu,
            known_terms,
            strict_min=not used_fallback,
        )
        if not menu_ok:
            used_fallback = True
        partial_ocr = False
        if used_fallback and fetched_recently and today_marker:
            candidate_menu = extract_missing_menu_candidates(name, texts)
            candidate_menu, candidate_ok, candidate_rejected = validate_extracted_menu(
                name,
                candidate_menu,
                known_terms,
                strict_min=False,
            )
            rejected_count += candidate_rejected
            if candidate_ok:
                extracted_menu = candidate_menu
                used_fallback = False
                partial_ocr = True
            else:
                extracted_menu = []
        restaurant["menu"] = extracted_menu
        if name != "에스제이 구내식당":
            restaurant.pop("menu_sections", None)
        low_confidence = fetched_recently and today_marker and not extracted_menu
        if extracted_menu and not used_fallback:
            restaurant["message"] = ""
            restaurant["menu_recorded_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            restaurant["menu_recorded_source_fetched_at"] = source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else now.strftime("%Y-%m-%d %H:%M:%S")
        logs.append(
            {
                "name": name,
                "items": len(extracted_menu),
                "updated": bool(extracted_menu) and not used_fallback,
                "used_existing_fallback": used_fallback,
                "fallback_confirmed": False,
                "reason": "partial_ocr" if partial_ocr else ("ocr_low_confidence" if low_confidence else ""),
                "ocr_rejected_items": rejected_count,
                "today_marker": today_marker,
                "source_fetched_at": source_fetched_at.strftime("%Y-%m-%d %H:%M:%S") if source_fetched_at else "",
            }
        )

    apply_manual_overrides(data, logs, now)
    data["ocr_log"] = logs
    save_data(data)


def main() -> None:
    update_json_with_ocr()
    print("menu json updated from ocr")


if __name__ == "__main__":
    main()
