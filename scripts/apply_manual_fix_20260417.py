from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "menu-today" / "menu_today.json"


MANUAL_MENUS = {
    "아이밀": {
        "menu": [
            "어묵탕",
            "수제순살치킨&어니언소스",
            "카레라이스",
            "물만두&초간장",
            "들깨무나물",
            "청경채사과무침",
            "가든샐러드&케요네즈D",
            "국내산 포기김치",
            "흑미밥 / 백미밥",
            "헛개차 / 탄산음료",
            "셀프비빔밥 / 한강라면",
            "간편식: 쉬림프샐러드",
        ],
    },
    "다시 봄": {
        "menu": [
            "콩나물국",
            "직화불제육",
            "바싹통살치킨",
            "킬바사스테이크구이",
            "고추잡채완자",
            "봄채소도토리묵무침",
            "싱싱샐러드",
            "깍두기",
            "모듬쌈채소",
            "탄산음료",
            "셀프라면",
        ],
    },
    "밥(온) 구내식당": {
        "menu": [
            "흰쌀밥 / 검은쌀잡곡밥",
            "우거지된장국",
            "고구마춘천닭갈비",
            "부먹등심탕수육",
            "떡갈비야채볶음밥",
            "통순두부찜*양념장",
            "통후랑크소시지구이",
            "숙주나물무침",
            "배추겉절이김치",
            "양배추샐러드",
            "수정과/후식과자",
        ],
    },
    "구내식당라온푸드": {
        "menu": [
            "후식볶음밥",
            "미니잔치국수",
            "삼겹살,목살 캠핑구이",
            "통살새우까스",
            "김말이튀김떡볶이",
            "브로콜리숙회/초고추장",
            "상추치커리겉절이",
            "연근조림",
            "셀프라면 & 배추김치",
            "샐러드 & 드레싱",
            "숭늉 & 음료",
        ],
    },
    "마이푸드": {
        "menu": [
            "봄나물볶음밥&양념장",
            "철판훈제오리볶음",
            "옥수수*단호박고로케&케찹",
            "동그랑땡전*김치떡산적",
            "산채도토리묵무침",
            "가지볶음/부추양파무침",
            "와사비쌈무/김치겉절이",
            "그린샐러드&드레싱",
            "목살김치찌개",
            "삼색꿀떡",
            "백미밥",
            "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료",
        ],
    },
    "퍼블릭가산 구내식당": {
        "menu": [
            "버섯소불고기",
            "군만두튀김",
            "초장비빔파스타",
        ],
        "menu_sections": [
            {
                "title": "주간 메인메뉴",
                "items": [
                    "버섯소불고기",
                    "군만두튀김",
                    "초장비빔파스타",
                ],
            }
        ],
    },
    "더푸드스케치": {
        "menu": [
            "버터계란볶음밥",
            "짬뽕라면",
            "직화닭불고기",
            "몬테크리스토",
            "궁중너비아니구이",
            "김말이",
            "바질크림떡볶이",
            "해파리냉채",
            "무생채",
            "가든샐러드/드레싱",
            "배추겉절이/음료",
        ],
    },
    "스타밸리푸드포유": {
        "menu": [
            "베이컨김치볶음밥",
            "백미밥",
            "직화제육볶음",
            "차돌라면",
            "고기손만두찜",
            "모듬튀김",
            "중식가지볶음",
            "우엉땅콩조림",
            "야채겉절이",
            "가든샐러드&포도D",
            "포기김치",
        ],
    },
    "에스제이 구내식당": {
        "menu": [
            "미역국",
            "백미밥 / 잡곡밥",
            "매콤닭볶음탕",
            "돈까스",
            "베이컨스크램블에그",
            "매운어묵볶음",
            "오이고추장무침",
            "배추김치",
            "그린샐러드",
            "추가찬2종",
            "김치찌개",
            "잡곡밥",
            "들깨불고기",
            "치킨너겟 * 소스",
            "불닭완자구이",
            "조미김구이",
            "계절나물",
            "계란후라이 / 토스트&딸기잼",
            "셀프 라면",
            "탄산음료, 숭늉, 매실차",
        ],
        "menu_sections": [
            {
                "title": "중식",
                "items": [
                    "미역국",
                    "백미밥 / 잡곡밥",
                    "매콤닭볶음탕",
                    "돈까스",
                    "베이컨스크램블에그",
                    "매운어묵볶음",
                    "오이고추장무침",
                    "배추김치",
                    "그린샐러드",
                    "추가찬2종",
                ],
            },
            {
                "title": "석식",
                "items": [
                    "김치찌개",
                    "잡곡밥",
                    "들깨불고기",
                    "치킨너겟 * 소스",
                    "불닭완자구이",
                    "조미김구이",
                    "계절나물",
                    "배추김치",
                    "그린샐러드",
                ],
            },
            {
                "title": "플러스메뉴",
                "items": [
                    "계란후라이 / 토스트&딸기잼",
                    "셀프 라면",
                    "탄산음료, 숭늉, 매실차",
                ],
            },
        ],
    },
}


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for restaurant in data["restaurants"]:
        name = restaurant["name"]
        if name not in MANUAL_MENUS:
            continue
        patch = MANUAL_MENUS[name]
        restaurant["menu"] = patch.get("menu", [])
        if "menu_sections" in patch:
            restaurant["menu_sections"] = patch["menu_sections"]
        elif "menu_sections" in restaurant:
            restaurant.pop("menu_sections", None)
        restaurant["status"] = "ready"
        restaurant["message"] = ""
        restaurant["menu_recent_source_today"] = True
        restaurant["menu_recorded_at"] = now
        source_fetched_at = restaurant.get("menu_recorded_source_fetched_at") or ""
        if not source_fetched_at:
            source_fetched_at = now
        restaurant["menu_recorded_source_fetched_at"] = source_fetched_at

    for log in data.get("ocr_log", []):
        if log["name"] not in MANUAL_MENUS:
            continue
        menu = MANUAL_MENUS[log["name"]]["menu"]
        log["items"] = len(menu)
        log["updated"] = True
        log["used_existing_fallback"] = False
        log["fallback_confirmed"] = False
        log["today_marker"] = True
        log.pop("reason", None)

    data["updated_at"] = now
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("manual menu fix applied")


if __name__ == "__main__":
    main()
