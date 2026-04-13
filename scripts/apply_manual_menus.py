from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "menu-today" / "menu_today.json"
SEOUL = ZoneInfo("Asia/Seoul")

MENU_BY_IMAGE = {
    "./images/imeal.png": [
        "순두부찌개",
        "파채간장돈불고기",
        "청파래오징어까스 & 타르소스",
        "실곤약무침",
        "오이양파무침",
        "오복지무침",
        "가든샐러드 & 포도D",
        "국내산 포기김치",
        "백미밥 / 흑미밥",
        "헛개차 / 탄산음료",
        "셀프비빔밥 / 한강라면",
        "간편식: 치킨텐더샐러드",
    ],
    "./images/dasibom.png": [
        "황태해장국",
        "통갈비김치찜",
        "손두부철판구이",
        "한식잡채",
        "고감콘고로케",
        "파래자반볶음",
        "싱싱샐러드",
        "직접담은쪽파김치",
        "셀프토스트",
        "탄산음료",
        "셀프라면",
    ],
    "./images/babon.png": [
        "흰쌀밥 / 검은쌀잡곡밥",
        "황태해장국",
        "새송이돈목살갈비구이",
        "후라이드순살치킨",
        "중화돈재짜장면",
        "고기*김치손만두찜",
        "치커리유자청무침",
        "배추겉절이김치",
        "양배추샐러드 / 과일",
    ],
    "./images/raonfood.png": [
        "호박고추장찌개",
        "수제순살닭강정",
        "간장돼지불백",
        "소시지전, 동그랑땡전",
        "야채쫄면 & 교자만두",
        "연두부 / 양념장",
        "된장깻잎지",
        "셀프라면 & 배추김치",
        "샐러드 & 드레싱",
        "숭늉 & 음료",
    ],
    "./images/myfood.png": [
        "열탄파채불고기",
        "치킨까스유린기",
        "크림카레우동",
        "가리비살야채무침",
        "햄마늘쫑볶음",
        "참나물겉절이",
        "무말랭이무침 / 포기김치",
        "그린샐러드 & 드레싱",
        "얼큰쑥갓어묵탕",
        "미니찐빵튀김",
        "잡곡밥 / 백미밥",
        "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료",
    ],
    "./images/public-gasan.png": [
        "간장제육 & 파채무침",
        "매운두부조림",
        "참치김치전",
    ],
    "./images/thefoodsketch.png": [
        "혼합잡곡밥",
        "김치콩나물국",
        "고추장불고기",
        "후라이드치킨 / 갈릭마요S",
        "일본식계란말이",
        "로제파스타",
        "꿀버터감자조림",
        "상추 / 배추 / 쌈장",
        "마늘쫑무침",
        "가든샐러드 / 드레싱",
        "배추겉절이 / 음료",
    ],
    "./images/starvalley-food4u-post.png": [
        "흑미밥 / 백미밥",
        "연탄불고기",
        "고기짬뽕국",
        "해물짜조롤 & 느억맘소스",
        "미트볼토마토스파게티",
        "소세지오븐구이",
        "야채겉절이",
        "오징어젓갈무무침",
        "가든샐러드 & 딸기D",
        "포기김치",
    ],
}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))
    now = datetime.now(SEOUL).strftime("%Y-%m-%d %H:%M:%S")
    names_to_update: set[str] = set()
    ocr_log = {entry.get("name"): entry for entry in data.get("ocr_log", [])}

    for restaurant in data.get("restaurants", []):
        preview_image = restaurant.get("preview_image")
        if preview_image in MENU_BY_IMAGE:
            restaurant["menu"] = MENU_BY_IMAGE[preview_image]
            restaurant["menu_recorded_at"] = now
            names_to_update.add(restaurant.get("name", ""))
            source_fetched_at = ocr_log.get(restaurant.get("name", ""), {}).get("source_fetched_at")
            if source_fetched_at:
                restaurant["menu_recorded_source_fetched_at"] = source_fetched_at

    for entry in data.get("ocr_log", []):
        if entry.get("name") in names_to_update:
            entry["updated"] = True
            entry["used_existing_fallback"] = False
            entry["items"] = len(
                next(
                    restaurant.get("menu", [])
                    for restaurant in data.get("restaurants", [])
                    if restaurant.get("name") == entry.get("name")
                )
            )
            entry.pop("reason", None)

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manual menus applied safely")


if __name__ == "__main__":
    main()
