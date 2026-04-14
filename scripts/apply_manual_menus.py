from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "menu-today" / "menu_today.json"
SEOUL = ZoneInfo("Asia/Seoul")

MANUAL_RESTAURANTS = {
    "아이밀": {
        "preview_image": "./images/imeal.png",
        "menu": [
            "감자수제비국",
            "묵은지닭볶음탕",
            "백순대볶음&양념장",
            "궁중탕평채",
            "호박나물",
            "콩나물파채무침",
            "가든샐러드&흑임자D",
            "국내산 배추겉절이",
            "백미밥 / 흑미밥",
            "헛개차 / 탄산음료",
            "셀프비빔밥 / 한강라면",
            "간편식: 훈제오리샐러드",
        ],
    },
    "다시 봄": {
        "preview_image": "./images/dasibom.png",
        "menu": [
            "소고기미역국",
            "뽕닭뽕닭",
            "바싹멘치돈까스",
            "새우미나리전",
            "쯔유냉모밀",
            "아삭오이무침",
            "싱싱샐러드",
            "직접담은겉절이",
            "셀프비빔밥",
            "탄산음료",
            "셀프라면",
        ],
    },
    "밥(온) 구내식당": {
        "preview_image": "./images/babon.png",
        "menu": [
            "흰쌀밥 / 검은쌀잡곡밥",
            "돼지고기김치찌개",
            "매콤닭다리볶음탕",
            "사각함박스테이크",
            "백순대야채볶음 * 들깨초장",
            "\"저칼로리\" 곤약비빔면",
            "설탕프렌치토스트구이",
            "청경채겉절이",
            "배추겉절이김치",
            "양배추샐러드 / 인절미떡",
        ],
    },
    "구내식당라온푸드": {
        "preview_image": "./images/raonfood.png",
        "menu": [
            "차돌김치찌개",
            "양념돼지갈비찜",
            "치킨스틱&치즈스틱",
            "청양유니짜장면",
            "떠먹는소떡소떡",
            "둥근오이무침",
            "꼬들단무지",
            "셀프라면 & 배추김치",
            "샐러드 & 드레싱",
            "숭늉 & 음료",
        ],
    },
    "마이푸드": {
        "preview_image": "./images/myfood.png",
        "menu": [
            "매운목살떡찜",
            "탕수육&후르츠소스",
            "사천짜장&중화면사리",
            "파채떡갈비조림",
            "호박새우젓볶음",
            "양념고추지 / 단무지&양파&춘장",
            "깍두기",
            "그린샐러드&드레싱",
            "무교동황태해장국",
            "고구마맛탕",
            "잡곡밥 / 백미밥",
            "쌈채소 & 풋고추 / 한강라면 & 달콤한 잼 토스트 / 구수한 숭늉 & 시원한 탄산음료",
        ],
    },
    "퍼블릭가산 구내식당": {
        "preview_image": "./images/public-gasan.png",
        "menu": [
            "순살닭강정",
            "고등어김치조림",
            "가스오부시양배추전",
        ],
    },
    "더푸드스케치": {
        "preview_image": "./images/thefoodsketch.png",
        "menu": [
            "혼합잡곡밥",
            "근대된장국",
            "다시마찜닭",
            "새우튀김/새우까스",
            "오코노미야키전",
            "옥수수바몬드카레라이스",
            "봄나물쫄면무침",
            "브로콜리두부무침",
            "고들빼기",
            "가든샐러드/드레싱",
            "배추겉절이/음료",
        ],
    },
    "스타밸리푸드포유": {
        "preview_image": "./images/starvalley-food4u-post.png",
        "menu": [
            "흑미밥 / 백미밥",
            "수제치킨&갈릭소이소스",
            "규동",
            "얼큰우거지된장국",
            "비빔냉면",
            "깻잎두부조림",
            "어묵콩나물찜",
            "야채겉절이",
            "가든샐러드&흑임자D",
            "포기김치",
        ],
    },
    "에스제이 구내식당": {
        "preview_image": "./images/sj-weekly-menu.png",
        "menu": [
            "조갯살시금치된장국",
            "백미밥 / 잡곡밥",
            "포항닭보쌈",
            "매콤깐풍육",
            "김치고기산적구이",
            "청양풍짜장면",
            "숙주나물무침",
            "배추김치",
            "그린샐러드",
            "추가찬2종",
            "계란후라이 / 토스트&딸기잼",
            "셀프 라면",
            "탄산음료, 숭늉, 매실차",
            "감자수제비국",
            "잡곡밥",
            "오징어볶음",
            "감자고로케 * 소스",
            "모듬소시지볶음",
            "고기만두찜 * 소스",
            "계절나물",
            "배추김치",
            "그린샐러드",
            "계란후라이 / 토스트&딸기잼",
            "셀프 라면",
            "탄산음료, 숭늉, 매실차",
        ],
        "menu_sections": [
            {
                "title": "중식",
                "items": [
                    "조갯살시금치된장국",
                    "백미밥 / 잡곡밥",
                    "포항닭보쌈",
                    "매콤깐풍육",
                    "김치고기산적구이",
                    "청양풍짜장면",
                    "숙주나물무침",
                    "배추김치",
                    "그린샐러드",
                    "추가찬2종",
                    "계란후라이 / 토스트&딸기잼",
                    "셀프 라면",
                    "탄산음료, 숭늉, 매실차",
                ],
            },
            {
                "title": "석식",
                "items": [
                    "감자수제비국",
                    "잡곡밥",
                    "오징어볶음",
                    "감자고로케 * 소스",
                    "모듬소시지볶음",
                    "고기만두찜 * 소스",
                    "계절나물",
                    "배추김치",
                    "그린샐러드",
                    "계란후라이 / 토스트&딸기잼",
                    "셀프 라면",
                    "탄산음료, 숭늉, 매실차",
                ],
            },
        ],
    },
}


def source_fetched_at(preview_image: str, fallback: str) -> str:
    image_path = ROOT / "menu-today" / "images" / Path(preview_image).name
    if image_path.exists():
        return datetime.fromtimestamp(image_path.stat().st_mtime, tz=SEOUL).strftime("%Y-%m-%d %H:%M:%S")
    return fallback


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))
    now = datetime.now(SEOUL).strftime("%Y-%m-%d %H:%M:%S")
    ocr_log = {entry.get("name"): entry for entry in data.get("ocr_log", [])}

    for restaurant in data.get("restaurants", []):
        name = restaurant.get("name", "")
        manual = MANUAL_RESTAURANTS.get(name)
        if not manual:
            continue
        preview_image = manual["preview_image"]
        restaurant["preview_image"] = preview_image
        restaurant["menu"] = manual["menu"]
        if "menu_sections" in manual:
            restaurant["menu_sections"] = manual["menu_sections"]
        else:
            restaurant.pop("menu_sections", None)
        restaurant["status"] = "ready"
        restaurant["message"] = ""
        restaurant["menu_recorded_at"] = now
        restaurant["menu_recent_source_today"] = True
        fallback_source = ocr_log.get(name, {}).get("source_fetched_at") or now
        restaurant["menu_recorded_source_fetched_at"] = source_fetched_at(preview_image, fallback_source)

    for entry in data.get("ocr_log", []):
        name = entry.get("name", "")
        manual = MANUAL_RESTAURANTS.get(name)
        if not manual:
            continue
        entry["updated"] = True
        entry["used_existing_fallback"] = False
        entry["fallback_confirmed"] = False
        entry["today_marker"] = True
        entry["items"] = len(manual["menu"])
        entry["source_fetched_at"] = source_fetched_at(manual["preview_image"], entry.get("source_fetched_at") or now)
        entry.pop("reason", None)

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manual menus applied safely")


if __name__ == "__main__":
    main()
