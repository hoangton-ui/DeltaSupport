import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCHEDULE_CONFIG_FILE = os.path.join(DATA_DIR, "schedule_config.json")

DAY_ORDER = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _default_config():
    return {"employees": []}


def ensure_schedule_config_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SCHEDULE_CONFIG_FILE):
        with open(SCHEDULE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_default_config(), f, indent=4, ensure_ascii=False)


def load_schedule_config():
    ensure_schedule_config_file()
    try:
        with open(SCHEDULE_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("employees", [])
                return data
    except Exception:
        pass
    return _default_config()


def save_schedule_config(config):
    ensure_schedule_config_file()
    with open(SCHEDULE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def _normalize_employee(employee_data):
    existing_active = employee_data.get("active", True)
    return {
        "username": str(employee_data.get("username", "")).strip(),
        "display_name": str(employee_data.get("display_name", "")).strip(),
        "department": str(employee_data.get("department", "Technical Support")).strip(),
        "team": str(employee_data.get("team", "General")).strip() or "General",
        "shift_name": str(employee_data.get("shift_name", "Shift 1")).strip() or "Shift 1",
        "vn_time_range": str(employee_data.get("vn_time_range", "")).strip(),
        "us_time_range": str(employee_data.get("us_time_range", "")).strip(),
        "off_days": [
            day for day in DAY_ORDER if day in set(employee_data.get("off_days", []))
        ],
        "active": bool(existing_active),
    }


def list_schedule_employees(include_inactive=False):
    config = load_schedule_config()
    employees = config.get("employees", [])
    if not isinstance(employees, list):
        return []

    normalized = [_normalize_employee(item) for item in employees]
    if include_inactive:
        return normalized
    return [item for item in normalized if item.get("active", True)]


def get_schedule_employee_map(include_inactive=False):
    result = {}
    for item in list_schedule_employees(include_inactive=include_inactive):
        username = str(item.get("username", "")).strip()
        if username:
            result[username.lower()] = item
    return result


def upsert_schedule_employee(employee_data):
    username = str(employee_data.get("username", "")).strip()
    if not username:
        raise ValueError("Username is required.")

    config = load_schedule_config()
    employees = config.get("employees", [])
    key = username.lower()
    updated = False

    normalized = _normalize_employee(employee_data)

    for idx, item in enumerate(employees):
        if str(item.get("username", "")).strip().lower() == key:
            employees[idx] = normalized
            updated = True
            break

    if not updated:
        employees.append(normalized)

    employees.sort(key=lambda item: str(item.get("username", "")).lower())
    config["employees"] = employees
    save_schedule_config(config)


def delete_schedule_employee(username):
    config = load_schedule_config()
    key = str(username).strip().lower()
    config["employees"] = [
        item
        for item in config.get("employees", [])
        if str(item.get("username", "")).strip().lower() != key
    ]
    save_schedule_config(config)


def set_schedule_employee_active(username, active):
    config = load_schedule_config()
    key = str(username).strip().lower()
    employees = config.get("employees", [])
    found = False

    for idx, item in enumerate(employees):
        if str(item.get("username", "")).strip().lower() == key:
            updated = _normalize_employee(item)
            updated["active"] = bool(active)
            employees[idx] = updated
            found = True
            break

    if not found:
        employees.append(
            _normalize_employee(
                {
                    "username": username,
                    "active": bool(active),
                }
            )
        )

    config["employees"] = employees
    save_schedule_config(config)
