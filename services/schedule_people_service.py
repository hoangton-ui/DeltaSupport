from datetime import date

from services.auth_service import (
    get_tech_schedule_api,
    get_tech_schedule_month_summary_api,
)


def get_schedule_people_snapshot_api(week_start=None, month=None, year=None):
    today = date.today()
    week_start = week_start or today.strftime("%Y-%m-%d")
    month = month or today.month
    year = year or today.year

    people_map = {}

    schedule_result = get_tech_schedule_api(week_start)
    if schedule_result.get("success"):
        for item in schedule_result.get("data", []):
            username = str(item.get("username", "")).strip()
            if not username:
                continue

            key = username.lower()
            existing = people_map.get(
                key,
                {
                    "username": username,
                    "full_name": "",
                    "department": "",
                    "team": "General",
                    "shift_name": "",
                    "vn_time_range": "",
                    "us_time_range": "",
                },
            )
            existing["full_name"] = item.get("full_name") or existing["full_name"]
            existing["department"] = item.get("department") or existing["department"]
            existing["team"] = item.get("team") or existing["team"]
            existing["shift_name"] = item.get("shift_name") or existing["shift_name"]
            existing["vn_time_range"] = item.get("vn_time_range") or existing["vn_time_range"]
            existing["us_time_range"] = item.get("us_time_range") or existing["us_time_range"]
            people_map[key] = existing

    summary_result = get_tech_schedule_month_summary_api(month, year)
    if summary_result.get("success"):
        for item in summary_result.get("data", []):
            username = str(item.get("Username", "")).strip()
            if not username:
                continue

            key = username.lower()
            existing = people_map.get(
                key,
                {
                    "username": username,
                    "full_name": "",
                    "department": "",
                    "team": "General",
                    "shift_name": "",
                    "vn_time_range": "",
                    "us_time_range": "",
                },
            )
            existing["full_name"] = item.get("full_name") or existing["full_name"]
            existing["department"] = item.get("department") or existing["department"]
            existing["team"] = item.get("team") or existing["team"]
            people_map[key] = existing

    return {
        "success": True,
        "data": list(people_map.values()),
        "schedule_success": schedule_result.get("success", False),
        "summary_success": summary_result.get("success", False),
    }
