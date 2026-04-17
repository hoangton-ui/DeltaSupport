from fastapi import APIRouter
from database import get_connection
from models import (
    TechScheduleUpdateRequest,
    ScheduleSetupSaveRequest,
    ScheduleSetupActiveRequest,
)
from services.audit_service import write_user_log, is_valid_schedule_status
from datetime import datetime, timedelta

router = APIRouter()


def normalize_team(team_value):
    team = "" if team_value is None else str(team_value).strip()
    return team if team else "General"


def users_has_team_column(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = 'Users'
          AND COLUMN_NAME = 'Team'
        """
    )
    return cursor.fetchone()[0] > 0


def ensure_schedule_setup_table(cursor):
    cursor.execute(
        """
        IF OBJECT_ID('dbo.TechScheduleEmployeeConfig', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.TechScheduleEmployeeConfig (
                Username NVARCHAR(100) NOT NULL PRIMARY KEY,
                DisplayName NVARCHAR(255) NULL,
                Department NVARCHAR(100) NULL,
                Team NVARCHAR(100) NULL,
                ShiftName NVARCHAR(100) NULL,
                VNTimeRange NVARCHAR(100) NULL,
                USTimeRange NVARCHAR(100) NULL,
                OffDays NVARCHAR(100) NULL,
                IsActive BIT NOT NULL DEFAULT 0,
                UpdatedBy NVARCHAR(100) NULL,
                UpdatedAt DATETIME NULL
            )
        END
        """
    )


def normalize_department(value):
    return str(value or "").strip()


def normalize_username(value):
    return str(value or "").strip()


def normalize_off_days(off_days):
    allowed = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}
    result = []
    for day in off_days or []:
        day_value = str(day or "").strip().upper()
        if day_value in allowed and day_value not in result:
            result.append(day_value)
    return result


def can_manage_schedule_scope(role, actor_department, actor_team, target_department, target_team):
    if role in ["Admin", "Management", "HR", "Accountant", "Leader", "Manager"]:
        return True
    if role in ["TS Leader", "Sale Leader", "MT Leader", "CS Leader"]:
        if normalize_department(actor_department).lower() != normalize_department(target_department).lower():
            return False
        if normalize_department(target_department).lower() == "sale team":
            return normalize_team(actor_team) == normalize_team(target_team)
        return True
    return False


def get_actor_context(cursor, action_by, has_team):
    actor_query = """
        SELECT Role, Department, {team_select}
        FROM dbo.Users
        WHERE Username = ?
    """.format(
        team_select="Team" if has_team else "'General' AS Team"
    )
    cursor.execute(actor_query, (action_by,))
    user_row = cursor.fetchone()

    if not user_row:
        return None

    return {
        "role": str(user_row[0] or "").strip(),
        "department": str(user_row[1] or "").strip(),
        "team": normalize_team(user_row[2]),
    }


def sync_template_rows(cursor, username, shift_name, vn_time_range, us_time_range, off_days):
    off_day_set = set(normalize_off_days(off_days))
    cursor.execute(
        "DELETE FROM dbo.TechScheduleTemplate WHERE Username = ?",
        (username,),
    )

    for day_name in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
        status_code = "OFF" if day_name in off_day_set else "WORK"
        cursor.execute(
            """
            INSERT INTO dbo.TechScheduleTemplate
            (Username, ShiftName, DayName, DefaultStatusCode, VNTimeRange, USTimeRange)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                shift_name,
                day_name,
                status_code,
                vn_time_range,
                us_time_range,
            ),
        )


def sync_schedule_rows_from_template(cursor, username, weeks_ahead=12):
    cursor.execute(
        """
        SELECT DayName, ShiftName, DefaultStatusCode, VNTimeRange, USTimeRange
        FROM dbo.TechScheduleTemplate
        WHERE Username = ?
        """,
        (username,),
    )
    rows = cursor.fetchall()
    template_by_day = {
        str(row[0] or "").strip().upper(): {
            "shift_name": str(row[1] or "").strip(),
            "status_code": str(row[2] or "WORK").strip(),
            "vn_time_range": str(row[3] or "").strip(),
            "us_time_range": str(row[4] or "").strip(),
        }
        for row in rows
        if str(row[0] or "").strip()
    }

    if not template_by_day:
        return

    monday = datetime.now() - timedelta(days=datetime.now().weekday())

    for week_index in range(weeks_ahead):
        for day_offset in range(7):
            current_date = monday + timedelta(days=(week_index * 7) + day_offset)
            day_name = current_date.strftime("%a").upper()[:3]
            template = template_by_day.get(day_name)
            if not template:
                continue

            work_date = current_date.strftime("%Y-%m-%d")
            cursor.execute(
                """
                SELECT StatusCode, UpdatedBy
                FROM dbo.TechSchedule
                WHERE Username = ? AND WorkDate = ?
                """,
                (username, work_date),
            )
            existing_row = cursor.fetchone()

            if not existing_row:
                cursor.execute(
                    """
                    INSERT INTO dbo.TechSchedule
                    (Username, ShiftName, WorkDate, DayName, VNTimeRange, USTimeRange, StatusCode)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        template["shift_name"],
                        work_date,
                        day_name,
                        template["vn_time_range"],
                        template["us_time_range"],
                        template["status_code"],
                    ),
                )
                continue

            current_status = str(existing_row[0] or "").strip().upper()
            updated_by = str(existing_row[1] or "").strip()

            if updated_by or current_status not in ["WORK", "OFF", ""]:
                continue

            cursor.execute(
                """
                UPDATE dbo.TechSchedule
                SET ShiftName = ?, DayName = ?, VNTimeRange = ?, USTimeRange = ?, StatusCode = ?
                WHERE Username = ? AND WorkDate = ?
                """,
                (
                    template["shift_name"],
                    day_name,
                    template["vn_time_range"],
                    template["us_time_range"],
                    template["status_code"],
                    username,
                    work_date,
                ),
            )


def get_employee_config_row(cursor, username):
    cursor.execute(
        """
        SELECT DisplayName, Department, Team, ShiftName, VNTimeRange, USTimeRange, OffDays, IsActive
        FROM dbo.TechScheduleEmployeeConfig
        WHERE Username = ?
        """,
        (username,),
    )
    return cursor.fetchone()


@router.get("/tech-schedule")
def get_tech_schedule(week_start: str):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.TechSchedule
            WHERE WorkDate >= ?
              AND WorkDate < DATEADD(DAY, 7, ?)
        """, (week_start, week_start))
        count = cursor.fetchone()[0]

        if count == 0:
            input_date = datetime.strptime(week_start, "%Y-%m-%d")
            start_date = input_date - timedelta(days=input_date.weekday())
            week_start = start_date.strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT Username, ShiftName, DayName, DefaultStatusCode, VNTimeRange, USTimeRange
                FROM dbo.TechScheduleTemplate
            """)
            template_rows = cursor.fetchall()

            for row in template_rows:
                username = str(row[0] or "").strip()
                shift_name = str(row[1] or "").strip()
                template_day = str(row[2] or "").strip().upper()
                status_code = str(row[3] or "WORK").strip()
                vn_time = str(row[4] or "").strip()
                us_time = str(row[5] or "").strip()

                for i in range(7):
                    current_date = start_date + timedelta(days=i)
                    date_str = current_date.strftime("%Y-%m-%d")
                    day_name = current_date.strftime("%a").upper()[:3]

                    if day_name != template_day:
                        continue

                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM dbo.TechSchedule
                        WHERE Username = ? AND WorkDate = ?
                    """, (username, date_str))
                    exists = cursor.fetchone()[0]

                    if exists == 0:
                        cursor.execute("""
                            INSERT INTO dbo.TechSchedule
                            (Username, ShiftName, WorkDate, DayName, VNTimeRange, USTimeRange, StatusCode)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            username,
                            shift_name,
                            date_str,
                            day_name,
                            vn_time,
                            us_time,
                            status_code
                        ))

            conn.commit()

        schedule_query = """
            SELECT
                ts.Id,
                ts.Username,
                COALESCE(cfg.DisplayName, u.FullName) AS DisplayName,
                u.FullName,
                COALESCE(cfg.Department, u.Department) AS Department,
                COALESCE({team_select_cfg}, {team_select_user}) AS Team,
                COALESCE(cfg.IsActive, 1) AS ScheduleActive,
                ts.ShiftName,
                ts.WorkDate,
                ts.DayName,
                ts.VNTimeRange,
                ts.USTimeRange,
                ts.StatusCode,
                ts.Note,
                ts.UpdatedBy,
                ts.UpdatedAt
            FROM dbo.TechSchedule ts
            LEFT JOIN dbo.Users u ON u.Username = ts.Username
            LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
            WHERE ts.WorkDate >= ?
              AND ts.WorkDate < DATEADD(DAY, 7, ?)
              AND COALESCE(cfg.IsActive, 1) = 1
            ORDER BY ts.ShiftName, ts.Username, ts.WorkDate
        """.format(
            team_select_cfg="cfg.Team" if has_team else "NULL",
            team_select_user="u.Team" if has_team else "'General'",
        )
        cursor.execute(schedule_query, (week_start, week_start))

        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "username": row[1],
                "display_name": row[2],
                "full_name": row[3],
                "department": row[4],
                "team": normalize_team(row[5]),
                "active": bool(row[6]),
                "shift_name": row[7],
                "work_date": str(row[8]),
                "day_name": row[9],
                "vn_time_range": row[10],
                "us_time_range": row[11],
                "status_code": row[12],
                "note": row[13],
                "updated_by": row[14],
                "updated_at": None if row[15] is None else str(row[15]),
            })

        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.post("/tech-schedule/update")
def update_tech_schedule(data: TechScheduleUpdateRequest):
    conn = None
    try:
        username = data.username.strip()
        work_date = data.work_date.strip()
        status_code = data.status_code.strip()
        action_by = data.action_by.strip()

        if not is_valid_schedule_status(status_code):
            return {"success": False, "message": f"Status không hợp lệ: {status_code}"}

        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)
        actor_context = get_actor_context(cursor, action_by, has_team)

        if not actor_context:
            return {"success": False, "message": "Không tìm thấy user"}

        role = actor_context["role"]
        actor_department = actor_context["department"]
        actor_team = actor_context["team"]

        allow_roles = [
            "Admin",
            "Management",
            "HR",
            "Accountant",
            "Leader",
            "Manager",
            "TS Leader",
            "Sale Leader",
            "MT Leader",
            "CS Leader",
        ]

        if role not in allow_roles:
            return {"success": False, "message": "Không có quyền sửa schedule"}

        target_query = """
            SELECT ts.StatusCode, COALESCE(cfg.Department, u.Department), COALESCE(cfg.Team, u.Team)
            FROM dbo.TechSchedule ts
            LEFT JOIN dbo.Users u ON u.Username = ts.Username
            LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
            WHERE ts.Username = ? AND ts.WorkDate = ?
        """
        if not has_team:
            target_query = """
                SELECT ts.StatusCode, COALESCE(cfg.Department, u.Department), COALESCE(cfg.Team, 'General') AS Team
                FROM dbo.TechSchedule ts
                LEFT JOIN dbo.Users u ON u.Username = ts.Username
                LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
                WHERE ts.Username = ? AND ts.WorkDate = ?
            """
        cursor.execute(target_query, (username, work_date))
        old_row = cursor.fetchone()

        if not old_row:
            return {"success": False, "message": "Không tìm thấy schedule"}

        old_status = str(old_row[0] or "").strip()
        target_department = str(old_row[1] or "").strip()
        target_team = normalize_team(old_row[2])

        if role in ["TS Leader", "Sale Leader", "MT Leader", "CS Leader"]:
            if actor_department.lower() != target_department.lower():
                return {"success": False, "message": "KhÃ´ng cÃ³ quyá»n sá»­a schedule khÃ¡c bá»™ pháº­n"}
            if target_department.lower() == "sale team" and actor_team != target_team:
                return {"success": False, "message": "KhÃ´ng cÃ³ quyá»n sá»­a schedule khÃ¡c team"}

        if old_status == status_code:
            return {"success": True, "message": "Không có thay đổi"}

        cursor.execute("""
            UPDATE dbo.TechSchedule
            SET StatusCode = ?, UpdatedBy = ?, UpdatedAt = GETDATE()
            WHERE Username = ? AND WorkDate = ?
        """, (status_code, action_by, username, work_date))

        if cursor.rowcount == 0:
            return {"success": False, "message": "Không update được record"}

        write_user_log(
            cursor,
            username=username,
            action_type="UPDATE_SCHEDULE",
            action_by=action_by,
            field_name="StatusCode",
            old_value=old_status,
            new_value=status_code,
        )

        conn.commit()
        return {"success": True, "message": "Cập nhật thành công"}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.get("/tech-schedule/month-summary")
def get_month_summary(month: int, year: int):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)

        query = """
        SELECT
            ts.Username,
            COALESCE(cfg.DisplayName, u.FullName) AS DisplayName,
            u.FullName,
            COALESCE(cfg.Department, u.Department) AS Department,
            COALESCE({team_select_cfg}, {team_select_user}) AS Team,
            SUM(CASE WHEN ts.StatusCode = 'A.L' THEN 1 ELSE 0 END) AS AL,
            SUM(CASE WHEN ts.StatusCode = 'S.L' THEN 1 ELSE 0 END) AS SL,
            SUM(CASE WHEN ts.StatusCode = 'C.T.O' THEN 1 ELSE 0 END) AS CTO,
            SUM(CASE WHEN ts.StatusCode = 'U.L' THEN 1 ELSE 0 END) AS UL,
            SUM(CASE WHEN ts.StatusCode = 'Other' THEN 1 ELSE 0 END) AS OtherCount
        FROM dbo.TechSchedule ts
        LEFT JOIN dbo.Users u ON u.Username = ts.Username
        LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
        WHERE MONTH(ts.WorkDate) = ? AND YEAR(ts.WorkDate) = ?
          AND COALESCE(cfg.IsActive, 1) = 1
        GROUP BY ts.Username, COALESCE(cfg.DisplayName, u.FullName), u.FullName, COALESCE(cfg.Department, u.Department), {team_group}
        """.format(
            team_select_cfg="cfg.Team" if has_team else "NULL",
            team_select_user="u.Team" if has_team else "'General'",
            team_group="COALESCE(cfg.Team, u.Team)" if has_team else "COALESCE(cfg.Team, 'General')",
        )
        cursor.execute(query, (month, year))
        rows = cursor.fetchall()

        data = []
        for row in rows:
            total = sum(int(row[i] or 0) for i in range(5, 10))
            data.append(
                {
                    "Username": row[0],
                    "display_name": row[1],
                    "full_name": row[2],
                    "department": row[3],
                    "team": normalize_team(row[4]),
                    "A.L": int(row[5] or 0),
                    "S.L": int(row[6] or 0),
                    "C.T.O": int(row[7] or 0),
                    "U.L": int(row[8] or 0),
                    "Other": int(row[9] or 0),
                    "Total": total,
                }
            )

        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.post("/tech-schedule/update-batch")
def update_tech_schedule_batch(data: dict):
    conn = None
    try:
        action_by = data.get("action_by", "").strip()
        updates = data.get("updates", [])

        if not updates:
            return {"success": False, "message": "No updates provided"}

        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)
        actor_context = get_actor_context(cursor, action_by, has_team)

        if not actor_context:
            return {"success": False, "message": "Không tìm thấy user"}

        role = actor_context["role"]
        actor_department = actor_context["department"]
        actor_team = actor_context["team"]

        allow_roles = [
            "Admin", "Management", "HR", "Accountant",
            "Leader", "Manager",
            "TS Leader", "Sale Leader", "MT Leader", "CS Leader"
        ]

        if role not in allow_roles:
            return {"success": False, "message": "Không có quyền sửa schedule"}

        failed = []

        for item in updates:
            username = item.get("username", "").strip()
            work_date = item.get("work_date", "").strip()
            status_code = item.get("status_code", "").strip()

            if not is_valid_schedule_status(status_code):
                failed.append(f"{username} - {work_date}: invalid status")
                continue

            target_query = """
                SELECT ts.StatusCode, COALESCE(cfg.Department, u.Department), COALESCE(cfg.Team, u.Team)
                FROM dbo.TechSchedule ts
                LEFT JOIN dbo.Users u ON u.Username = ts.Username
                LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
                WHERE ts.Username = ? AND ts.WorkDate = ?
            """
            if not has_team:
                target_query = """
                    SELECT ts.StatusCode, COALESCE(cfg.Department, u.Department), COALESCE(cfg.Team, 'General') AS Team
                    FROM dbo.TechSchedule ts
                    LEFT JOIN dbo.Users u ON u.Username = ts.Username
                    LEFT JOIN dbo.TechScheduleEmployeeConfig cfg ON cfg.Username = ts.Username
                    WHERE ts.Username = ? AND ts.WorkDate = ?
                """
            cursor.execute(target_query, (username, work_date))
            old_row = cursor.fetchone()

            if not old_row:
                failed.append(f"{username} - {work_date}: not found")
                continue

            old_status = str(old_row[0] or "").strip()
            target_department = str(old_row[1] or "").strip()
            target_team = normalize_team(old_row[2])

            if role in ["TS Leader", "Sale Leader", "MT Leader", "CS Leader"]:
                if actor_department.lower() != target_department.lower():
                    failed.append(f"{username} - {work_date}: forbidden department")
                    continue
                if target_department.lower() == "sale team" and actor_team != target_team:
                    failed.append(f"{username} - {work_date}: forbidden team")
                    continue

            if old_status == status_code:
                continue

            cursor.execute("""
                UPDATE dbo.TechSchedule
                SET StatusCode = ?, UpdatedBy = ?, UpdatedAt = GETDATE()
                WHERE Username = ? AND WorkDate = ?
            """, (status_code, action_by, username, work_date))

            if cursor.rowcount == 0:
                failed.append(f"{username} - {work_date}: update fail")
                continue

            write_user_log(
                cursor,
                username=username,
                action_type="UPDATE_SCHEDULE",
                action_by=action_by,
                field_name="StatusCode",
                old_value=old_status,
                new_value=status_code,
            )

        conn.commit()

        return {
            "success": True if not failed else False,
            "failed": failed
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.get("/schedule-setup/employees")
def get_schedule_setup_employees(action_by: str, department: str, team: str = "General"):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)

        action_by = normalize_username(action_by)
        department = normalize_department(department)
        team = normalize_team(team)

        actor_context = get_actor_context(cursor, action_by, has_team)
        if not actor_context:
            return {"success": False, "message": "User not found."}

        if not can_manage_schedule_scope(
            actor_context["role"],
            actor_context["department"],
            actor_context["team"],
            department,
            team,
        ):
            return {"success": False, "message": "You do not have permission to access this department."}

        cursor.execute(
            """
            SELECT DISTINCT Username
            FROM dbo.TechScheduleEmployeeConfig
            WHERE Department = ?
            """,
            (department,),
        )
        cfg_usernames = [normalize_username(row[0]) for row in cursor.fetchall() if normalize_username(row[0])]

        cursor.execute("SELECT DISTINCT Username FROM dbo.TechScheduleTemplate ORDER BY Username")
        template_usernames = [normalize_username(row[0]) for row in cursor.fetchall() if normalize_username(row[0])]

        cursor.execute("SELECT DISTINCT Username FROM dbo.TechSchedule ORDER BY Username")
        schedule_usernames = [normalize_username(row[0]) for row in cursor.fetchall() if normalize_username(row[0])]

        if has_team:
            cursor.execute(
                """
                SELECT Username, FullName, Department, Team, Role
                FROM dbo.Users
                WHERE Department = ?
                  AND IsApproved = 1
                ORDER BY Username
                """,
                (department,),
            )
        else:
            cursor.execute(
                """
                SELECT Username, FullName, Department, 'General' AS Team, Role
                FROM dbo.Users
                WHERE Department = ?
                  AND IsApproved = 1
                ORDER BY Username
                """,
                (department,),
            )
        approved_users = cursor.fetchall()
        approved_user_map = {
            normalize_username(row[0]).lower(): {
                "username": normalize_username(row[0]),
                "full_name": str(row[1] or "").strip(),
                "department": normalize_department(row[2]),
                "team": normalize_team(row[3]),
                "role": str(row[4] or "").strip(),
            }
            for row in approved_users
            if normalize_username(row[0]) and str(row[4] or "").strip().lower() != "deleted user"
        }

        all_usernames = []
        seen = set()
        for username in cfg_usernames + template_usernames + schedule_usernames + [item["username"] for item in approved_user_map.values()]:
            key = username.lower()
            if key in seen:
                continue
            seen.add(key)
            all_usernames.append(username)

        data = []
        for username in all_usernames:
            cfg_row = get_employee_config_row(cursor, username)
            approved_user = approved_user_map.get(username.lower(), {})
            cursor.execute(
                """
                SELECT TOP 1 ShiftName, VNTimeRange, USTimeRange
                FROM dbo.TechScheduleTemplate
                WHERE Username = ?
                ORDER BY ShiftName, VNTimeRange, USTimeRange
                """,
                (username,),
            )
            template_meta = cursor.fetchone()

            cursor.execute(
                """
                SELECT DayName, DefaultStatusCode
                FROM dbo.TechScheduleTemplate
                WHERE Username = ?
                ORDER BY DayName
                """,
                (username,),
            )
            template_days = cursor.fetchall()

            off_days = []
            for row in template_days:
                day_name = str(row[0] or "").strip().upper()
                status_code = str(row[1] or "WORK").strip().upper()
                if status_code != "WORK" and day_name and day_name not in off_days:
                    off_days.append(day_name)

            if cfg_row:
                merged_department = normalize_department(cfg_row[1]) or department
                merged_team = normalize_team(cfg_row[2])
                active = bool(cfg_row[7])
                display_name = str(cfg_row[0] or "").strip()
                shift_name = str(cfg_row[3] or (template_meta[0] if template_meta else "")).strip()
                vn_time_range = str(cfg_row[4] or (template_meta[1] if template_meta else "")).strip()
                us_time_range = str(cfg_row[5] or (template_meta[2] if template_meta else "")).strip()
                cfg_off_days = normalize_off_days(str(cfg_row[6] or "").split(",")) if cfg_row[6] else []
                full_name = approved_user.get("full_name", "")
            else:
                merged_department = approved_user.get("department", department) or department
                merged_team = approved_user.get("team", team if department == "Sale Team" else "General")
                active = False
                display_name = ""
                shift_name = str(template_meta[0] if template_meta else "").strip()
                vn_time_range = str(template_meta[1] if template_meta else "").strip()
                us_time_range = str(template_meta[2] if template_meta else "").strip()
                cfg_off_days = []
                full_name = approved_user.get("full_name", "")

            if not cfg_row and not approved_user:
                continue

            if merged_department != department:
                continue
            if department == "Sale Team" and merged_team != team:
                continue

            data.append(
                {
                    "username": username,
                    "display_name": display_name,
                    "full_name": full_name,
                    "department": merged_department,
                    "team": merged_team,
                    "shift_name": shift_name,
                    "vn_time_range": vn_time_range,
                    "us_time_range": us_time_range,
                    "off_days": cfg_off_days or off_days,
                    "active": active,
                }
            )

        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.post("/schedule-setup/save")
def save_schedule_setup_employee(data: ScheduleSetupSaveRequest):
    conn = None
    try:
        username = normalize_username(data.username)
        display_name = str(data.display_name or "").strip()
        department = normalize_department(data.department)
        team = normalize_team(data.team)
        shift_name = str(data.shift_name or "").strip()
        vn_time_range = str(data.vn_time_range or "").strip()
        us_time_range = str(data.us_time_range or "").strip()
        off_days = normalize_off_days(data.off_days)
        action_by = normalize_username(data.action_by)

        if not username:
            return {"success": False, "message": "Username is required."}
        if len(off_days) != 2:
            return {"success": False, "message": "Exactly 2 off days are required."}

        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)

        actor_context = get_actor_context(cursor, action_by, has_team)
        if not actor_context:
            return {"success": False, "message": "User not found."}

        if not can_manage_schedule_scope(
            actor_context["role"],
            actor_context["department"],
            actor_context["team"],
            department,
            team,
        ):
            return {"success": False, "message": "You do not have permission to manage this employee."}

        old_cfg = get_employee_config_row(cursor, username)

        cursor.execute(
            """
            MERGE dbo.TechScheduleEmployeeConfig AS target
            USING (SELECT ? AS Username) AS source
            ON target.Username = source.Username
            WHEN MATCHED THEN
                UPDATE SET
                    DisplayName = ?,
                    Department = ?,
                    Team = ?,
                    ShiftName = ?,
                    VNTimeRange = ?,
                    USTimeRange = ?,
                    OffDays = ?,
                    IsActive = 1,
                    UpdatedBy = ?,
                    UpdatedAt = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (Username, DisplayName, Department, Team, ShiftName, VNTimeRange, USTimeRange, OffDays, IsActive, UpdatedBy, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, GETDATE());
            """,
            (
                username,
                display_name,
                department,
                team,
                shift_name,
                vn_time_range,
                us_time_range,
                ",".join(off_days),
                action_by,
                username,
                display_name,
                department,
                team,
                shift_name,
                vn_time_range,
                us_time_range,
                ",".join(off_days),
                action_by,
            ),
        )

        sync_template_rows(cursor, username, shift_name, vn_time_range, us_time_range, off_days)
        sync_schedule_rows_from_template(cursor, username, weeks_ahead=12)

        old_values = old_cfg or ("", "", "", "", "", "", "", 0)
        changed_fields = [
            ("DisplayName", str(old_values[0] or "").strip(), display_name),
            ("Department", str(old_values[1] or "").strip(), department),
            ("Team", normalize_team(old_values[2]), team),
            ("ShiftName", str(old_values[3] or "").strip(), shift_name),
            ("VNTimeRange", str(old_values[4] or "").strip(), vn_time_range),
            ("USTimeRange", str(old_values[5] or "").strip(), us_time_range),
            ("OffDays", str(old_values[6] or "").strip(), ",".join(off_days)),
            ("ScheduleActive", "1" if bool(old_values[7]) else "0", "1"),
        ]
        for field_name, old_value, new_value in changed_fields:
            if str(old_value) != str(new_value):
                write_user_log(
                    cursor,
                    username=username,
                    action_type="UPDATE_SCHEDULE_SETUP",
                    action_by=action_by,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                )

        conn.commit()
        return {"success": True, "message": "Employee schedule setup has been saved successfully."}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()


@router.post("/schedule-setup/set-active")
def set_schedule_setup_active(data: ScheduleSetupActiveRequest):
    conn = None
    try:
        username = normalize_username(data.username)
        active = bool(data.active)
        action_by = normalize_username(data.action_by)

        conn = get_connection()
        cursor = conn.cursor()
        has_team = users_has_team_column(cursor)
        ensure_schedule_setup_table(cursor)

        actor_context = get_actor_context(cursor, action_by, has_team)
        if not actor_context:
            return {"success": False, "message": "User not found."}

        target_row = get_employee_config_row(cursor, username)
        if not target_row:
            return {"success": False, "message": "Please save the employee schedule setup before changing Active/Inactive."}

        target_department = normalize_department(target_row[1])
        target_team = normalize_team(target_row[2])
        old_active = bool(target_row[7]) if target_row[7] is not None else False

        if not can_manage_schedule_scope(
            actor_context["role"],
            actor_context["department"],
            actor_context["team"],
            target_department,
            target_team,
        ):
            return {"success": False, "message": "You do not have permission to update this employee."}

        cursor.execute(
            """
            MERGE dbo.TechScheduleEmployeeConfig AS target
            USING (SELECT ? AS Username) AS source
            ON target.Username = source.Username
            WHEN MATCHED THEN
                UPDATE SET
                    Department = COALESCE(target.Department, ?),
                    Team = COALESCE(target.Team, ?),
                    IsActive = ?,
                    UpdatedBy = ?,
                    UpdatedAt = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (Username, Department, Team, IsActive, UpdatedBy, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, GETDATE());
            """,
            (
                username,
                target_department,
                target_team,
                1 if active else 0,
                action_by,
                username,
                target_department,
                target_team,
                1 if active else 0,
                action_by,
            ),
        )

        if old_active != active:
            write_user_log(
                cursor,
                username=username,
                action_type="UPDATE_SCHEDULE_SETUP",
                action_by=action_by,
                field_name="ScheduleActive",
                old_value=1 if old_active else 0,
                new_value=1 if active else 0,
            )

        conn.commit()
        return {"success": True, "message": "Employee status has been updated successfully."}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            conn.close()
