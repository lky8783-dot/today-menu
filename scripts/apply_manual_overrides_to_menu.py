from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MENU_PATH = ROOT / "menu-today" / "menu_today.json"
OVERRIDES_PATH = ROOT / "menu-today" / "manual_menu_overrides.json"
SEOUL = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_menu_items(restaurant: dict) -> int:
    if restaurant.get("menu_sections"):
        return sum(len(section.get("items", [])) for section in restaurant["menu_sections"])
    return len(restaurant.get("menu", []))


def apply_date(date_key: str) -> None:
    data = load_json(MENU_PATH)
    overrides_root = load_json(OVERRIDES_PATH) if OVERRIDES_PATH.exists() else {}
    date_entry = overrides_root.get(date_key, {})
    restaurant_overrides = date_entry.get("restaurants", {})
    now = datetime.now(SEOUL)
    recorded_at = now.strftime("%Y-%m-%d %H:%M:%S")
    data["updated_at"] = recorded_at
    data["date_label"] = f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAYS[now.weekday()]}"

    logs = []
    for restaurant in data.get("restaurants", []):
        name = restaurant.get("name", "")
        override = restaurant_overrides.get(name)
        if override:
            restaurant["status"] = override.get("status", restaurant.get("status", "ready"))
            restaurant["message"] = override.get("message", "")
            if "preview_image" in override:
                restaurant["preview_image"] = override["preview_image"]
            if "menu_sections" in override:
                restaurant["menu_sections"] = override["menu_sections"]
                flat_menu: list[str] = []
                for section in override["menu_sections"]:
                    flat_menu.extend(section.get("items", []))
                restaurant["menu"] = flat_menu
            else:
                restaurant["menu"] = override.get("menu", [])
                restaurant.pop("menu_sections", None)
            restaurant["menu_recorded_at"] = recorded_at
            restaurant["menu_recorded_source_fetched_at"] = restaurant.get("menu_recorded_source_fetched_at") or recorded_at
            restaurant["menu_recent_source_today"] = True
            logs.append(
                {
                    "name": name,
                    "items": count_menu_items(restaurant),
                    "updated": True,
                    "used_existing_fallback": False,
                    "manual_override": True,
                    "today_marker": True,
                    "source_fetched_at": restaurant.get("menu_recorded_source_fetched_at", ""),
                }
            )
            continue

        logs.append(
            {
                "name": name,
                "items": count_menu_items(restaurant),
                "updated": bool(restaurant.get("menu") or restaurant.get("menu_sections")),
                "used_existing_fallback": True,
                "reason": restaurant.get("message", "") or "not_updated",
                "source_fetched_at": restaurant.get("menu_recorded_source_fetched_at", ""),
            }
        )

    data["ocr_log"] = logs
    write_json(MENU_PATH, data)
    print(f"manual overrides applied: {date_key} -> {recorded_at}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now(SEOUL).strftime("%Y-%m-%d"))
    args = parser.parse_args()
    apply_date(args.date)


if __name__ == "__main__":
    main()
