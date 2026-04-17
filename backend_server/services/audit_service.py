def write_user_log(
    cursor,
    username,
    action_type,
    action_by=None,
    field_name=None,
    old_value=None,
    new_value=None,
    note=None,
):
    query = """
    INSERT INTO dbo.UserAuditLog
    (
        Username,
        ActionType,
        FieldName,
        OldValue,
        NewValue,
        ActionBy,
        ActionAt,
        Note
    )
    VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?)
    """
    cursor.execute(
        query,
        (
            username,
            action_type,
            field_name,
            None if old_value is None else str(old_value),
            None if new_value is None else str(new_value),
            action_by,
            note,
        ),
    )


def get_status_text(is_approved, is_active, role=None):
    if str(role or "").strip().lower() == "deleted user":
        return "deleted"
    if not is_active:
        return "inactive"
    if not is_approved:
        return "pending"
    return "approved"


def is_valid_pin(pin_code: str) -> bool:
    return pin_code.isdigit() and len(pin_code) == 4


def is_valid_schedule_status(status_code: str) -> bool:
    allowed = {"WORK", "OFF", "A.L", "S.L", "C.T.O", "U.L", "Other"}
    return status_code in allowed
