from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "menu-today" / "menu_today.json"


MANUAL_MENUS = {
    "아이밀": {
        "menu": [
            "콩가루배추국",
            "오돈불고기",
            "생선까스&타르소스",
            "건파래쪽파무침",
            "쑥갓두부무침",
            "상추파채무침",
            "가든샐러드&망고D",
            "국내산 깍두기",
            "백미밥 / 흑미밥",
            "헛개차 / 탄산음료",
            "셀프비빔밥 / 한강라면",
            "간편식: 쉬림프샐러드",
        ],
    },
    "다시 봄": {
        "menu": [
            "시금미역국",
            "가마솥통닭다리찜닭",
            "청파래오징어까스",
            "고기손만두찜",
            "애호박새우부침개",
            "오이송송무침",
            "싱싱샐러드",
            "직접담은겉절이",
            "황태칼국수",
            "탄산음료",
            "셀프라면",
        ],
    },
    "밥(온) 구내식당": {
        "menu": [
            "흰쌀밥 / 검은쌀잡곡밥",
            "얼큰민물새우탕",
            "직화오징어제육불고기",
            "간장수제닭강정",
            "바지락미나리파스타",
            "김치메밀전병구이",
            "어묵야채볶음",
            "청경채겉절이",
            "배추겉절이김치",
            "양배추샐러드",
            "호박카스테라떡",
        ],
    },
    "구내식당라온푸드": {
        "menu": [
            "참치김치찌개",
            "양념반후라이드반치킨",
            "갈비양념목살구이",
            "모듬소시지야채볶음",
            "해물야끼소바",
            "깻잎도무침",
            "부추양파겉절이",
            "셀프라면 & 배추김치",
            "샐러드 & 드레싱",
            "숭늉 & 음료",
        ],
    },
    "마이푸드": {
        "menu": [
            "청양돼지불백",
            "치킨새우카츠&스리라차마요S",
            "참나물봉골레파스타",
            "메추리알곤약조림",
            "콘치즈버터구이",
            "오이미나리무침",
            "간장고추지/포기김치",
            "그린샐러드&드레싱",
            "얼큰순두부찌개",
            "경양식스프&크루통",
            "잡곡밥 / 백미밥",
            "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료",
        ],
    },
    "퍼블릭가산 구내식당": {
        "menu": [
            "고추장제육볶음",
            "매콤한마파두부",
            "건새우파전",
        ],
        "menu_sections": [
            {
                "title": "주간 메인메뉴",
                "items": [
                    "고추장제육볶음",
                    "매콤한마파두부",
                    "건새우파전",
                ],
            }
        ],
    },
    "더푸드스케치": {
        "menu": [
            "혼합잡곡밥",
            "소고기우거지해장국",
            "숯불돼지갈비구이",
            "후라이드치킨/청양마요S",
            "당면계란전",
            "온두부/김치볶음",
            "킬바사소세지",
            "건새우무조림",
            "봄나물겉절이",
            "가든샐러드/드레싱",
            "음료",
        ],
    },
    "스타밸리푸드포유": {
        "menu": [
            "흑미밥 / 백미밥",
            "청양찜닭",
            "얼큰호박수제비",
            "치즈돈까스",
            "가쓰오해물볶음우동",
            "킬바사소세지구이",
            "야채겉절이",
            "콩나물무침",
            "가든샐러드&딸기D",
            "포기김치",
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
        restaurant["menu"] = patch["menu"]
        if "menu_sections" in patch:
            restaurant["menu_sections"] = patch["menu_sections"]
        else:
            restaurant.pop("menu_sections", None)
        restaurant["status"] = "ready"
        restaurant["message"] = ""
        restaurant["menu_recent_source_today"] = True
        restaurant["menu_recorded_at"] = now
        restaurant["menu_recorded_source_fetched_at"] = (
            restaurant.get("menu_recorded_source_fetched_at") or now
        )

    for log in data.get("ocr_log", []):
        if log["name"] not in MANUAL_MENUS:
            continue
        log["items"] = len(MANUAL_MENUS[log["name"]]["menu"])
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
