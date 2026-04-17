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
    );
END;

WITH AllScheduleUsers AS (
    SELECT DISTINCT LTRIM(RTRIM(Username)) AS Username
    FROM dbo.TechSchedule
    WHERE Username IS NOT NULL AND LTRIM(RTRIM(Username)) <> ''

    UNION

    SELECT DISTINCT LTRIM(RTRIM(Username)) AS Username
    FROM dbo.TechScheduleTemplate
    WHERE Username IS NOT NULL AND LTRIM(RTRIM(Username)) <> ''
),
TemplateSummary AS (
    SELECT
        LTRIM(RTRIM(Username)) AS Username,
        MAX(LTRIM(RTRIM(ShiftName))) AS ShiftName,
        MAX(LTRIM(RTRIM(VNTimeRange))) AS VNTimeRange,
        MAX(LTRIM(RTRIM(USTimeRange))) AS USTimeRange,
        STUFF((
            SELECT ',' + t2.DayName
            FROM dbo.TechScheduleTemplate t2
            WHERE LTRIM(RTRIM(t2.Username)) = LTRIM(RTRIM(t.Username))
              AND UPPER(LTRIM(RTRIM(ISNULL(t2.DefaultStatusCode, 'WORK')))) <> 'WORK'
            ORDER BY
                CASE UPPER(LTRIM(RTRIM(t2.DayName)))
                    WHEN 'MON' THEN 1
                    WHEN 'TUE' THEN 2
                    WHEN 'WED' THEN 3
                    WHEN 'THU' THEN 4
                    WHEN 'FRI' THEN 5
                    WHEN 'SAT' THEN 6
                    WHEN 'SUN' THEN 7
                    ELSE 8
                END
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS OffDays
    FROM dbo.TechScheduleTemplate t
    GROUP BY LTRIM(RTRIM(Username))
)
MERGE dbo.TechScheduleEmployeeConfig AS target
USING (
    SELECT
        s.Username,
        NULL AS DisplayName,
        'Technical Support' AS Department,
        'General' AS Team,
        ISNULL(ts.ShiftName, 'Shift 1') AS ShiftName,
        ISNULL(ts.VNTimeRange, '') AS VNTimeRange,
        ISNULL(ts.USTimeRange, '') AS USTimeRange,
        ISNULL(ts.OffDays, '') AS OffDays,
        CAST(1 AS BIT) AS IsActive
    FROM AllScheduleUsers s
    LEFT JOIN TemplateSummary ts
        ON ts.Username = s.Username
) AS source
ON target.Username = source.Username
WHEN MATCHED THEN
    UPDATE SET
        Department = COALESCE(NULLIF(target.Department, ''), source.Department),
        Team = COALESCE(NULLIF(target.Team, ''), source.Team),
        ShiftName = COALESCE(NULLIF(target.ShiftName, ''), source.ShiftName),
        VNTimeRange = COALESCE(NULLIF(target.VNTimeRange, ''), source.VNTimeRange),
        USTimeRange = COALESCE(NULLIF(target.USTimeRange, ''), source.USTimeRange),
        OffDays = COALESCE(NULLIF(target.OffDays, ''), source.OffDays),
        IsActive = 1,
        UpdatedAt = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (
        Username,
        DisplayName,
        Department,
        Team,
        ShiftName,
        VNTimeRange,
        USTimeRange,
        OffDays,
        IsActive,
        UpdatedBy,
        UpdatedAt
    )
    VALUES (
        source.Username,
        source.DisplayName,
        source.Department,
        source.Team,
        source.ShiftName,
        source.VNTimeRange,
        source.USTimeRange,
        source.OffDays,
        source.IsActive,
        'seed-script',
        GETDATE()
    );

SELECT *
FROM dbo.TechScheduleEmployeeConfig
ORDER BY Username;
