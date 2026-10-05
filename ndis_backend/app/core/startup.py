"""Application startup hooks — run once when the server boots.

Startup order (all idempotent — safe on every restart):
  1. provision_common_schema()  — creates ndis_common schema + 4 platform tables
                                   if they don't exist yet (fresh database)
  2. seed_subscription_plans()  — inserts Basic/Professional/Enterprise plans
                                   into ndis_common.subscription_plan if empty
"""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ─── Migration log ────────────────────────────────────────────────────────────
# Tracks which one-time migrations have already been applied.
# Each migration that is fully schema-complete records itself here and skips
# on every subsequent restart, making hot-reloads much faster.

async def _ensure_migration_log(conn) -> None:
    """Create ndis_common.migration_log table if it doesn't exist."""
    await conn.execute(text("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ndis_common' AND TABLE_NAME = 'migration_log'
        )
        CREATE TABLE [ndis_common].[migration_log] (
            migration_name  NVARCHAR(200) NOT NULL PRIMARY KEY,
            applied_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
        )
    """))
    await conn.commit()


async def _migration_done(conn, name: str) -> bool:
    """Return True if this migration has already been recorded as complete."""
    row = await conn.scalar(text(
        "SELECT 1 FROM [ndis_common].[migration_log] WHERE migration_name = :n"
    ), {"n": name})
    return bool(row)


async def _record_migration(conn, name: str) -> None:
    """Mark a migration as complete so it is skipped on future restarts."""
    await conn.execute(text(
        "INSERT INTO [ndis_common].[migration_log] (migration_name) VALUES (:n)"
    ), {"n": name})
    await conn.commit()
    logger.info("Migration recorded as done: %s", name)


# ─── Shared helper ────────────────────────────────────────────────────────────

async def _get_provisioned_schemas(conn) -> list[str]:
    """Return tenant schema names that are active in ndis_common.tenant AND
    whose SQL Server schema actually exists in the database.
    Filters out ghost tenants whose schema was never (or partially) provisioned.
    """
    rows = (await conn.execute(text(
        """
        SELECT t.schema_name
        FROM [ndis_common].[tenant] t
        WHERE t.schema_name IS NOT NULL
          AND t.is_deleted = 0
          AND EXISTS (
              SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA s
              WHERE s.SCHEMA_NAME = t.schema_name
          )
        """
    ))).fetchall()
    return [row[0] for row in rows]


# ─── Subscription plan seed data ──────────────────────────────────────────────

_PLANS = [
    {
        "plan_code":       "BASIC",
        "plan_name":       "Basic",
        "max_branches":    1,
        "max_users":       10,
        "max_participants": 100,
        "monthly_price":   149.00,
        "monthly_fee_aud": 149.00,
        "annual_fee_aud":  1490.00,
    },
    {
        "plan_code":       "PROFESSIONAL",
        "plan_name":       "Professional",
        "max_branches":    5,
        "max_users":       50,
        "max_participants": 500,
        "monthly_price":   349.00,
        "monthly_fee_aud": 349.00,
        "annual_fee_aud":  3490.00,
    },
    {
        "plan_code":       "ENTERPRISE",
        "plan_name":       "Enterprise",
        "max_branches":    50,
        "max_users":       500,
        "max_participants": 9999,
        "monthly_price":   799.00,
        "monthly_fee_aud": 799.00,
        "annual_fee_aud":  7990.00,
    },
]


async def seed_leave_types() -> None:
    """Seed standard Australian NDIS leave types into ndis_common.leave_type if empty."""
    from app.database import engine
    _MIG = "seed_leave_types_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    LEAVE_TYPES = [
        ("ANNUAL",        "Annual Leave",              "AL",   True,  "Paid annual leave entitlement"),
        ("PERSONAL",      "Personal / Sick Leave",     "PL",   True,  "Personal or sick leave"),
        ("LONG_SERVICE",  "Long Service Leave",        "LSL",  True,  "Long service leave entitlement"),
        ("CARERS",        "Carer's Leave",             "CL",   True,  "Leave to care for an immediate family member"),
        ("COMPASSIONATE", "Compassionate Leave",       "COM",  True,  "Bereavement or compassionate leave"),
        ("PARENTAL",      "Parental Leave",            "PAR",  True,  "Maternity, paternity or adoption leave"),
        ("COMMUNITY",     "Community Service Leave",   "CSL",  False, "Jury duty or emergency management activities"),
        ("STUDY",         "Study Leave",               "STL",  False, "Leave to attend approved training or study"),
        ("UNPAID",        "Unpaid Leave",              "UL",   False, "Unpaid leave by arrangement"),
        ("OTHER",         "Other Leave",               "OTH",  False, "Other approved leave"),
    ]

    try:
        async with engine.begin() as conn:
            for lt_id, lt_name, lt_code, paid, desc in LEAVE_TYPES:
                await conn.execute(text("""
                    IF NOT EXISTS (
                        SELECT 1 FROM [ndis_common].[leave_type]
                        WHERE leave_type_id = :id
                    )
                    INSERT INTO [ndis_common].[leave_type]
                        (leave_type_id, leave_type_name, leave_code, paid_leave, description, is_active)
                    VALUES (:id, :name, :code, :paid, :desc, 1)
                """), {"id": lt_id, "name": lt_name, "code": lt_code, "paid": paid, "desc": desc})
        logger.info("seed_leave_types: seeded %d leave types", len(LEAVE_TYPES))
    except Exception as exc:
        logger.warning("seed_leave_types: failed: %s", exc)
        return

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_branch_columns() -> None:
    """Add new branch columns (3.2–3.5) to all existing tenant schemas.
    Idempotent — skips any column that already exists.
    Uses a separate auto-committed statement per column so a single failure
    does not roll back the rest.
    """
    from app.database import engine
    _MIG = "migrate_branch_columns_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    NEW_COLUMNS = [
        ("branch_type",       "NVARCHAR(100)  NULL"),
        ("parent_branch_id",  "INT            NULL"),
        ("branch_status",     "NVARCHAR(50)   NULL"),   # default handled in app layer
        ("address_line2",     "NVARCHAR(255)  NULL"),
        ("country",           "NVARCHAR(100)  NULL"),
        ("timezone",          "NVARCHAR(100)  NULL"),
        ("operating_hours",   "NVARCHAR(MAX)  NULL"),
        ("facilities",        "NVARCHAR(MAX)  NULL"),
        ("notes",             "NVARCHAR(MAX)  NULL"),
    ]

    try:
        # Fetch only schemas that are active AND actually exist in the database
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_branch_columns(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        for col_name, col_def in NEW_COLUMNS:
            try:
                async with engine.begin() as conn:
                    exists = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'branch'
                        AND COLUMN_NAME = '{col_name}'
                    """))
                    if not exists:
                        await conn.execute(text(
                            f"ALTER TABLE [{s}].[branch] ADD {col_name} {col_def}"
                        ))
                        logger.info("migrate_branch_columns: added %s to [%s].[branch]", col_name, s)
            except Exception as exc:
                logger.warning("migrate_branch_columns: failed adding %s to [%s].[branch]: %s", col_name, s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_staff_personal_info_columns() -> None:
    """Add nationality and language_spoken to staff_personal_info (idempotent)."""
    from app.database import engine
    _MIG = "migrate_staff_personal_info_columns_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    NEW_COLUMNS = [
        ("nationality",    "NVARCHAR(50)   NULL"),
        ("language_spoken","NVARCHAR(100)  NULL"),
    ]

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_staff_personal_info_columns(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        for col_name, col_def in NEW_COLUMNS:
            try:
                async with engine.begin() as conn:
                    exists = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'staff_personal_info'
                        AND COLUMN_NAME = '{col_name}'
                    """))
                    if not exists:
                        await conn.execute(text(
                            f"ALTER TABLE [{s}].[staff_personal_info] ADD {col_name} {col_def}"
                        ))
                        logger.info("migrate_staff_personal_info_columns: added %s to [%s].[staff_personal_info]", col_name, s)
            except Exception as exc:
                logger.warning("migrate_staff_personal_info_columns: failed adding %s to [%s].[staff_personal_info]: %s", col_name, s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_cross_branch_access_table() -> None:
    """Create or rebuild the cross_branch_access table in every tenant schema (4.1–4.7).

    Strategy:
      - If the table exists but uses the OLD minimal schema (has column 'user_id' instead
        of 'staff_user_id'), drop and recreate it — old data is placeholder only.
      - If the table already has 'staff_user_id', it's the new schema; add any missing columns.
      - If the table doesn't exist, create it fresh.
    Idempotent — safe on every restart.
    """
    from app.database import engine
    _MIG = "migrate_cross_branch_access_table_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    NEW_TABLE_DDL = """
        CREATE TABLE [{s}].[cross_branch_access] (
            access_id            INT IDENTITY(1,1) PRIMARY KEY,
            staff_user_id        NVARCHAR(50)  NOT NULL,
            home_branch_id       INT           NOT NULL,
            target_branch_id     INT           NOT NULL,
            participant_id       NVARCHAR(100) NULL,
            participant_name     NVARCHAR(255) NULL,
            permitted_activities NVARCHAR(MAX) NULL,
            access_reason        NVARCHAR(500) NOT NULL,
            services_description NVARCHAR(MAX) NULL,
            access_start         DATETIMEOFFSET NULL,
            access_end           DATETIMEOFFSET NULL,
            access_type          NVARCHAR(20)  NOT NULL DEFAULT 'planned',
            is_emergency         BIT           NOT NULL DEFAULT 0,
            emergency_reason     NVARCHAR(500) NULL,
            requires_review      BIT           NOT NULL DEFAULT 0,
            reviewed_by          NVARCHAR(50)  NULL,
            reviewed_at          DATETIMEOFFSET NULL,
            review_notes         NVARCHAR(500) NULL,
            status               NVARCHAR(20)  NOT NULL DEFAULT 'pending',
            requested_by         NVARCHAR(50)  NOT NULL,
            requested_at         DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            approved_by          NVARCHAR(50)  NULL,
            approved_at          DATETIMEOFFSET NULL,
            approval_comments    NVARCHAR(500) NULL,
            rejected_by          NVARCHAR(50)  NULL,
            rejected_at          DATETIMEOFFSET NULL,
            rejection_reason     NVARCHAR(500) NULL,
            revoked_by           NVARCHAR(50)  NULL,
            revoked_at           DATETIMEOFFSET NULL,
            revoke_reason        NVARCHAR(500) NULL,
            is_active            BIT           NOT NULL DEFAULT 1,
            is_deleted           BIT           NOT NULL DEFAULT 0,
            created_at           DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at           DATETIMEOFFSET NULL
        )
    """

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_cross_branch_access_table(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        try:
            async with engine.begin() as conn:
                # Check if table exists
                table_exists = await conn.scalar(text(f"""
                    SELECT COUNT(1) FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'cross_branch_access'
                """))

                if table_exists:
                    # Check if it's the OLD schema (has 'user_id' not 'staff_user_id')
                    old_col = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'cross_branch_access'
                        AND COLUMN_NAME = 'user_id'
                    """))
                    if old_col:
                        # Drop old table and recreate
                        await conn.execute(text(f"DROP TABLE [{s}].[cross_branch_access]"))
                        await conn.execute(text(NEW_TABLE_DDL.replace("{s}", s)))
                        logger.info("migrate_cross_branch_access_table: rebuilt old table in [%s]", s)
                    else:
                        logger.info("migrate_cross_branch_access_table: table already new schema in [%s]", s)
                else:
                    await conn.execute(text(NEW_TABLE_DDL.replace("{s}", s)))
                    logger.info("migrate_cross_branch_access_table: created table in [%s]", s)
        except Exception as exc:
            logger.warning("migrate_cross_branch_access_table: failed for [%s]: %s", s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_tenant_config_columns() -> None:
    """Add new tenant_config columns for 8.1–8.7 (regional, security, notifications,
    billing extras, integrations). Idempotent — skips columns that already exist.
    """
    from app.database import engine
    _MIG = "migrate_tenant_config_columns_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    NEW_COLUMNS = [
        # 8.2 Regional
        ("country",           "NVARCHAR(100)  NOT NULL DEFAULT 'Australia'"),
        ("state",             "NVARCHAR(100)  NULL"),
        ("time_format",       "NVARCHAR(10)   NOT NULL DEFAULT '24h'"),
        ("week_starts_on",    "NVARCHAR(10)   NOT NULL DEFAULT 'Monday'"),
        ("timezone",          "NVARCHAR(100)  NOT NULL DEFAULT 'Australia/Sydney'"),
        # 8.3 Currency & Tax
        ("gst_rate",          "INT            NOT NULL DEFAULT 10"),
        # 8.4 Billing extras
        ("billing_frequency",     "NVARCHAR(50)  NOT NULL DEFAULT 'Monthly'"),
        ("payment_terms",         "NVARCHAR(200) NULL"),
        ("auto_invoice_enabled",  "BIT           NOT NULL DEFAULT 0"),
        # 8.5 Notifications
        ("notify_email_enabled",          "BIT NOT NULL DEFAULT 1"),
        ("notify_sms_enabled",            "BIT NOT NULL DEFAULT 0"),
        ("notify_inapp_enabled",          "BIT NOT NULL DEFAULT 1"),
        ("notify_appointment_reminders",  "BIT NOT NULL DEFAULT 1"),
        ("notify_plan_expiry_alerts",     "BIT NOT NULL DEFAULT 1"),
        ("notify_overdue_payment_alerts", "BIT NOT NULL DEFAULT 1"),
        ("notify_budget_alerts",          "BIT NOT NULL DEFAULT 1"),
        ("notify_reminder_hours_before",  "INT NOT NULL DEFAULT 24"),
        # 8.6 Security
        ("session_timeout_minutes",    "INT NOT NULL DEFAULT 60"),
        ("password_min_length",        "INT NOT NULL DEFAULT 8"),
        ("password_require_uppercase", "BIT NOT NULL DEFAULT 1"),
        ("password_require_numbers",   "BIT NOT NULL DEFAULT 1"),
        ("password_require_symbols",   "BIT NOT NULL DEFAULT 0"),
        ("max_login_attempts",         "INT NOT NULL DEFAULT 5"),
        ("mfa_enabled",                "BIT NOT NULL DEFAULT 0"),
        # 8.7 Integration extras
        ("integration_myob_enabled",            "BIT           NOT NULL DEFAULT 0"),
        ("integration_xero_enabled",            "BIT           NOT NULL DEFAULT 0"),
        ("integration_communication_provider",  "NVARCHAR(50)  NULL"),
        ("integration_payment_provider",        "NVARCHAR(50)  NULL"),
    ]

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_tenant_config_columns(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        for col_name, col_def in NEW_COLUMNS:
            try:
                async with engine.begin() as conn:
                    exists = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'tenant_config'
                        AND COLUMN_NAME = '{col_name}'
                    """))
                    if not exists:
                        await conn.execute(text(
                            f"ALTER TABLE [{s}].[tenant_config] ADD {col_name} {col_def}"
                        ))
                        logger.info("migrate_tenant_config_columns: added %s to [%s].[tenant_config]", col_name, s)
            except Exception as exc:
                logger.warning("migrate_tenant_config_columns: failed adding %s to [%s].[tenant_config]: %s", col_name, s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_tenant_document_linked_to() -> None:
    """Add linked_to column to tenant_document in all existing tenant schemas.
    Safe to run on every restart — skips if the column already exists.
    """
    from app.database import engine
    _MIG = "migrate_tenant_document_linked_to_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_tenant_document_linked_to() failed (non-fatal): %s", exc)
        return

    for s in schemas:
        try:
            async with engine.begin() as conn:
                exists = await conn.scalar(text(f"""
                    SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'tenant_document'
                    AND COLUMN_NAME = 'linked_to'
                """))
                if not exists:
                    await conn.execute(text(f"""
                        ALTER TABLE [{s}].[tenant_document]
                        ADD linked_to NVARCHAR(255) NULL
                    """))
                    logger.info("Added linked_to column to [%s].[tenant_document]", s)
        except Exception as exc:
            logger.warning("migrate_tenant_document_linked_to() failed for [%s] (non-fatal): %s", s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_staff_tables() -> None:
    """Create all staff management tables in existing tenant schemas (idempotent).
    New tenants get these tables via provision_tenant_schema().
    This migration runs on every restart and is a no-op if tables already exist.

    _MIG bumped to v2 for the addition of staff_shift (features 4.3-4.5) —
    this re-applies the sweep for every already-provisioned tenant, not just
    new ones. Each table create is itself guarded by an existence check, so
    re-running is safe and a no-op for every table besides the new one.
    """
    from app.database import engine
    _MIG = "migrate_staff_tables_v2"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    _STAFF_TABLES = [
        ("staff_profile", """
            staff_id            NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            first_name          NVARCHAR(50)    NOT NULL,
            middle_name         NVARCHAR(50)    NULL,
            last_name           NVARCHAR(50)    NOT NULL,
            photo               NVARCHAR(255)   NULL,
            work_email          NVARCHAR(255)   NULL,
            status              NVARCHAR(30)    NOT NULL DEFAULT 'Active',
            is_deleted          BIT             NOT NULL DEFAULT 0,
            deleted_at          DATETIMEOFFSET  NULL,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_personal_info", """
            personal_id                 NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            dob                         DATE            NULL,
            gender                      NVARCHAR(20)    NULL,
            blood_group                 NVARCHAR(10)    NULL,
            nationality                 NVARCHAR(50)    NULL,
            language_spoken             NVARCHAR(100)   NULL,
            permanent_street_no         NVARCHAR(50)    NULL,
            permanent_area              NVARCHAR(50)    NULL,
            permanent_city              NVARCHAR(50)    NULL,
            permanent_state             NVARCHAR(50)    NULL,
            permanent_post_code         NVARCHAR(10)    NULL,
            permanent_country_id        INT             NULL,
            same_as_permanent_address   BIT             NULL,
            residential_street_no       NVARCHAR(50)    NULL,
            residential_area            NVARCHAR(50)    NULL,
            residential_city            NVARCHAR(50)    NULL,
            residential_state           NVARCHAR(50)    NULL,
            residential_post_code       NVARCHAR(10)    NULL,
            residential_country_id      INT             NULL,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        """),
        ("staff_contact_info", """
            staff_contact_id        NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               NVARCHAR(50)    NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            primary_email           NVARCHAR(255)   NULL,
            secondary_email         NVARCHAR(255)   NULL,
            country_id              INT             NULL,
            primary_contact_no      NVARCHAR(15)    NULL,
            secondary_contact_no    NVARCHAR(15)    NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_identification", """
            staff_iden_id           NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            identification_type     NVARCHAR(50)    NULL,
            identification_number   NVARCHAR(50)    NULL,
            document_attached       BIT             NULL,
            expiry_date             DATE            NULL,
            verified                BIT             NULL,
            verified_by             NVARCHAR(50)    NULL,
            verified_date           DATE            NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_preferences", """
            staff_pref_id                   NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                       INT             NOT NULL,
            staff_id                        NVARCHAR(50)    NOT NULL,
            preferred_shift_type            NVARCHAR(30)    NULL,
            willing_weekend_work            BIT             NULL,
            willing_public_holiday_work     BIT             NULL,
            willing_sleepover_shift         BIT             NULL,
            willing_active_overnight        BIT             NULL,
            vehicle_available               BIT             NULL,
            willing_to_travel               BIT             NULL,
            travel_limit_enabled            BIT             NULL,
            travel_radius_km                INT             NULL,
            preferred_contact_time_from     TIME            NULL,
            preferred_contact_time_to       TIME            NULL,
            preferred_participant_gender    NVARCHAR(20)    NULL,
            is_deleted                      BIT             NOT NULL DEFAULT 0,
            created_by                      NVARCHAR(50)    NULL,
            created_at                      DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                      NVARCHAR(50)    NULL,
            updated_at                      DATETIMEOFFSET  NULL
        """),
        ("staff_emergency_contact", """
            emergency_contact_id        NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            first_name                  NVARCHAR(50)    NULL,
            middle_name                 NVARCHAR(50)    NULL,
            last_name                   NVARCHAR(50)    NULL,
            relationship_with_staff     NVARCHAR(30)    NULL,
            gender                      NVARCHAR(20)    NULL,
            blood_group                 NVARCHAR(10)    NULL,
            street_no                   NVARCHAR(50)    NULL,
            area                        NVARCHAR(50)    NULL,
            city                        NVARCHAR(50)    NULL,
            state                       NVARCHAR(50)    NULL,
            post_code                   NVARCHAR(50)    NULL,
            country_id                  INT             NULL,
            primary_contact_no          NVARCHAR(15)    NULL,
            secondary_contact_no        NVARCHAR(15)    NULL,
            primary_email               NVARCHAR(255)   NULL,
            secondary_email             NVARCHAR(255)   NULL,
            is_primary_emerg_cntact     BIT             NULL,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        """),
        ("employment_information", """
            employment_info_id      NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            employment_type         NVARCHAR(30)    NULL,
            employment_status       NVARCHAR(30)    NULL,
            pay_level               NVARCHAR(30)    NULL,
            reporting_manager_id    NVARCHAR(50)    NULL,
            employment_start_date   DATE            NULL,
            employment_end_date     DATE            NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_probation", """
            probation_id                NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            probation_start_date        DATE            NULL,
            probation_end_date          DATE            NULL,
            probation_status            NVARCHAR(30)    NULL,
            reviewed_by                 NVARCHAR(50)    NULL,
            probation_review_notes      NVARCHAR(100)   NULL,
            probation_extension_date    DATE            NULL,
            confirmed_as_permanent      BIT             NULL,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        """),
        ("staff_contract", """
            contract_id             NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            contract_type           NVARCHAR(30)    NULL,
            contract_start_date     DATE            NULL,
            contract_end_date       DATE            NULL,
            contract_uploaded       BIT             NULL,
            contract_file_path      NVARCHAR(255)   NULL,
            contract_renewal_date   DATE            NULL,
            notice_period_timeline  NVARCHAR(30)    NULL,
            schads_applicable       BIT             NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_roles", """
            staff_role_id       NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            role_name           NVARCHAR(100)   NULL,
            role_level          NVARCHAR(50)    NULL,
            role_description    NVARCHAR(500)   NULL,
            role_start_date     DATE            NULL,
            role_end_date       DATE            NULL,
            is_active           BIT             NOT NULL DEFAULT 1,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_exit_process", """
            exit_process_id             NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            exit_type                   NVARCHAR(30)    NULL,
            resignation_date            DATE            NULL,
            last_working_date           DATE            NULL,
            exit_reason                 NVARCHAR(100)   NULL,
            notice_period_served        BIT             NULL,
            exit_interview_date         DATE            NULL,
            handover_completed          BIT             NULL,
            agreement_copy_uploaded     BIT             NULL,
            agreement_file_path         NVARCHAR(255)   NULL,
            access_revoked_date         DATETIMEOFFSET  NULL,
            status                      NVARCHAR(30)    NULL,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        """),
        ("staff_qualification", """
            staff_qualification_id  NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            qualification_id        NVARCHAR(20)    NOT NULL,
            issuing_institution     NVARCHAR(100)   NULL,
            year_commenced          INT             NULL,
            year_completed          INT             NULL,
            certificate_uploaded    BIT             NULL,
            verification_status     NVARCHAR(30)    NULL,
            verification_date       DATE            NULL,
            verified_by             NVARCHAR(50)    NULL,
            verify_remarks          NVARCHAR(50)    NULL,
            status                  NVARCHAR(30)    NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_certification", """
            staff_certification_id  NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            certification_id        NVARCHAR(20)    NOT NULL,
            certification_status    NVARCHAR(30)    NULL,
            issuing_provider        NVARCHAR(50)    NULL,
            issue_date              DATE            NULL,
            expiry_date             DATE            NULL,
            certificate_uploaded    BIT             NULL,
            verification_status     NVARCHAR(30)    NULL,
            verified_by             NVARCHAR(50)    NULL,
            verified_date           DATE            NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_availability", """
            availability_id             NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            availability_type           NVARCHAR(30)    NULL,
            availability_effective_from DATETIMEOFFSET  NULL,
            availability_effective_to   DATETIMEOFFSET  NULL,
            availability_status         NVARCHAR(30)    NULL,
            current_shift_id            NVARCHAR(50)    NULL,
            available_for_overtime      BIT             NULL,
            available_for_on_call       BIT             NULL,
            availability_notes          NVARCHAR(MAX)   NULL,
            is_active                   BIT             NOT NULL DEFAULT 1,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        """),
        ("staff_timesheet_header", """
            timesheet_id            NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            work_date               DATE            NULL,
            timesheet_status        NVARCHAR(30)    NULL,
            submitted_date          DATE            NULL,
            approval_date           DATE            NULL,
            approved_by             NVARCHAR(50)    NULL,
            rejection_reason        NVARCHAR(100)   NULL,
            total_overtime_hours    DECIMAL(5,2)    NULL,
            notes                   NVARCHAR(MAX)   NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_timesheet_line", """
            timesheet_line_id       NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            timesheet_id            NVARCHAR(50)    NOT NULL,
            shift_id                NVARCHAR(50)    NULL,
            ndis_no                 NVARCHAR(50)    NULL,
            scheduled_start_time    TIME            NULL,
            scheduled_end_time      TIME            NULL,
            actual_clock_on_time    TIME            NULL,
            actual_clock_off_time   TIME            NULL,
            break_taken             BIT             NULL,
            break_duration_minutes  INT             NULL,
            care_note_submitted     BIT             NULL,
            line_status             NVARCHAR(30)    NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_leave_request", """
            leave_request_id                NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id                       INT             NOT NULL,
            staff_id                        NVARCHAR(50)    NOT NULL,
            leave_type_id                   NVARCHAR(50)    NOT NULL,
            reason_for_leave                NVARCHAR(100)   NULL,
            supporting_document_uploaded    BIT             NULL,
            submitted_date                  DATE            NULL,
            submitted_time                  TIME            NULL,
            leave_status                    NVARCHAR(30)    NULL,
            approved_by                     NVARCHAR(50)    NULL,
            approval_date                   DATE            NULL,
            decline_reason                  NVARCHAR(MAX)   NULL,
            backfill_required               BIT             NULL,
            backfill_staff_id               NVARCHAR(50)    NULL,
            participants_notified           BIT             NULL,
            is_deleted                      BIT             NOT NULL DEFAULT 0,
            created_by                      NVARCHAR(50)    NULL,
            created_at                      DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                      NVARCHAR(50)    NULL,
            updated_at                      DATETIMEOFFSET  NULL
        """),
        ("staff_leave_request_date", """
            leave_request_date_id   NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            leave_request_id        NVARCHAR(20)    NOT NULL,
            leave_date              DATE            NULL,
            leave_duration          NVARCHAR(20)    NULL,
            leave_start_time        TIME            NULL,
            leave_end_time          TIME            NULL,
            leave_hours             DECIMAL(5,2)    NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_leave_balance", """
            leave_balance_id    NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            leave_type_id       NVARCHAR(50)    NOT NULL,
            leave_period        NVARCHAR(10)    NULL,
            opening_balance     DECIMAL(6,2)    NULL,
            accrued_leave       DECIMAL(6,2)    NULL,
            available_balance   DECIMAL(6,2)    NULL,
            remarks             NVARCHAR(MAX)   NULL,
            is_active           BIT             NOT NULL DEFAULT 1,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_performance_review", """
            review_id               NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            staff_id                NVARCHAR(50)    NOT NULL,
            review_period           NVARCHAR(20)    NULL,
            review_type             NVARCHAR(30)    NULL,
            review_date             DATE            NULL,
            reviewed_by             NVARCHAR(50)    NULL,
            overall_score           DECIMAL(4,2)    NULL,
            punctuality_score       DECIMAL(4,2)    NULL,
            care_quality_score      DECIMAL(4,2)    NULL,
            compliance_score        DECIMAL(4,2)    NULL,
            communication_score     DECIMAL(4,2)    NULL,
            teamwork_score          DECIMAL(4,2)    NULL,
            reviewer_comments       NVARCHAR(MAX)   NULL,
            staff_self_assessment   NVARCHAR(MAX)   NULL,
            review_status           NVARCHAR(30)    NULL,
            is_deleted              BIT             NOT NULL DEFAULT 0,
            created_by              NVARCHAR(50)    NULL,
            created_at              DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by              NVARCHAR(50)    NULL,
            updated_at              DATETIMEOFFSET  NULL
        """),
        ("staff_kpi", """
            kpi_id              NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            review_id           NVARCHAR(50)    NULL,
            kpi_name            NVARCHAR(100)   NULL,
            kpi_category        NVARCHAR(50)    NULL,
            target_value        DECIMAL(5,2)    NULL,
            actual_value        DECIMAL(5,2)    NULL,
            score               DECIMAL(4,2)    NULL,
            weight_percent      DECIMAL(5,2)    NULL,
            notes               NVARCHAR(MAX)   NULL,
            period              NVARCHAR(20)    NULL,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_goal", """
            goal_id             NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            review_id           NVARCHAR(50)    NULL,
            goal_title          NVARCHAR(200)   NULL,
            goal_description    NVARCHAR(MAX)   NULL,
            goal_category       NVARCHAR(50)    NULL,
            goal_period         NVARCHAR(20)    NULL,
            due_date            DATE            NULL,
            goal_status         NVARCHAR(30)    NULL,
            completion_date     DATE            NULL,
            set_by              NVARCHAR(50)    NULL,
            notes               NVARCHAR(MAX)   NULL,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_compliance_item", """
            compliance_item_id   NVARCHAR(36)    NOT NULL PRIMARY KEY,
            tenant_id            NVARCHAR(36)    NOT NULL,
            staff_id             NVARCHAR(36)    NOT NULL,
            requirement_name     NVARCHAR(200)   NOT NULL,
            reference_no         NVARCHAR(100)   NULL,
            category             NVARCHAR(100)   NULL,
            requirement_type     NVARCHAR(100)   NULL,
            completed_date       DATE            NULL,
            expiry_date          DATE            NULL,
            status               NVARCHAR(50)    NULL DEFAULT 'Pending',
            is_mandatory         BIT             NOT NULL DEFAULT 1,
            document_filename    NVARCHAR(300)   NULL,
            document_url         NVARCHAR(500)   NULL,
            document_uploaded_at DATETIME        NULL,
            reminder_days_before NVARCHAR(10)    NULL DEFAULT '30',
            reminder_sent_at     DATETIME        NULL,
            notes                NVARCHAR(MAX)   NULL,
            created_at           DATETIME        NOT NULL DEFAULT GETDATE(),
            updated_at           DATETIME        NOT NULL DEFAULT GETDATE()
        """),
        ("staff_compliance_audit", """
            audit_id             NVARCHAR(36)    NOT NULL PRIMARY KEY,
            tenant_id            NVARCHAR(36)    NOT NULL,
            staff_id             NVARCHAR(36)    NOT NULL,
            compliance_item_id   NVARCHAR(36)    NOT NULL,
            action_type          NVARCHAR(100)   NULL,
            action_description   NVARCHAR(500)   NULL,
            previous_status      NVARCHAR(50)    NULL,
            new_status           NVARCHAR(50)    NULL,
            changed_by_user_id   NVARCHAR(36)    NULL,
            changed_by_name      NVARCHAR(200)   NULL,
            notes                NVARCHAR(MAX)   NULL,
            created_at           DATETIME        NOT NULL DEFAULT GETDATE()
        """),
        ("staff_document_repository", """
            document_id         NVARCHAR(20)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            document_type       NVARCHAR(50)    NULL,
            document_name       NVARCHAR(50)    NULL,
            document_description NVARCHAR(500)  NULL,
            file_path           NVARCHAR(255)   NULL,
            file_url            NVARCHAR(500)   NULL,
            file_format         NVARCHAR(20)    NULL,
            document_date       DATE            NULL,
            expiry_date         DATE            NULL,
            upload_date         DATE            NULL,
            document_status     NVARCHAR(30)    NULL,
            expiry_alert_days   NVARCHAR(10)    NULL,
            uploaded_by         NVARCHAR(50)    NULL,
            uploaded_at         DATETIMEOFFSET  NULL,
            is_active           BIT             NOT NULL DEFAULT 1,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
        ("staff_shift", """
            shift_id            NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id           INT             NOT NULL,
            staff_id            NVARCHAR(50)    NOT NULL,
            day_of_week         SMALLINT        NOT NULL,
            shift_type          NVARCHAR(50)    NULL,
            start_hour          SMALLINT        NOT NULL,
            end_hour            SMALLINT        NOT NULL,
            location            NVARCHAR(200)   NULL,
            shift_status        NVARCHAR(30)    NULL DEFAULT 'Confirmed',
            is_recurring        BIT             NOT NULL DEFAULT 0,
            recurring_from      DATE            NULL,
            recurring_to        DATE            NULL,
            notes               NVARCHAR(MAX)   NULL,
            is_deleted          BIT             NOT NULL DEFAULT 0,
            created_by          NVARCHAR(50)    NULL,
            created_at          DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)    NULL,
            updated_at          DATETIMEOFFSET  NULL
        """),
    ]

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_staff_tables(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        for table_name, col_defs in _STAFF_TABLES:
            try:
                async with engine.begin() as conn:
                    exists = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = '{table_name}'
                    """))
                    if not exists:
                        await conn.execute(text(
                            f"CREATE TABLE [{s}].[{table_name}] ({col_defs})"
                        ))
                        logger.info("migrate_staff_tables: created [%s].[%s]", s, table_name)
            except Exception as exc:
                logger.warning("migrate_staff_tables: failed [%s].[%s]: %s", s, table_name, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_staff_permissions() -> None:
    """Seed staff permission codes and role assignments into every existing tenant schema.

    Idempotent — skips codes that already exist, skips role-perm rows that
    already exist (relies on the UNIQUE constraint UQ_role_perm_<schema>).
    Safe to run on every restart.
    """
    from app.database import engine
    # v2: added staff:performance (was missing — see migrate_staff_permissions
    # docstring history; ADMIN never received it because this migration had
    # already run and recorded itself done under v1 before the permission
    # existed). Bumping the version forces this to re-apply for every
    # already-provisioned tenant, not just new ones.
    _MIG = "migrate_staff_permissions_v2"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    STAFF_PERMISSIONS = [
        ("staff:view",        "staff", "view",        "View staff profiles and details"),
        ("staff:create",      "staff", "create",      "Add a new staff member"),
        ("staff:edit",        "staff", "edit",        "Edit staff details"),
        ("staff:delete",      "staff", "delete",      "Deactivate / soft-delete a staff member"),
        ("staff:timesheets",  "staff", "timesheets",  "Submit and approve staff timesheets"),
        ("staff:leave",       "staff", "leave",       "Submit and approve staff leave requests"),
        ("staff:documents",   "staff", "documents",   "Upload and manage staff documents"),
        ("staff:performance", "staff", "performance", "Create and manage staff performance reviews, goals and KPIs"),
    ]

    # Which codes each role gets (beyond ADMIN which gets all)
    ROLE_STAFF_PERMS: dict[str, list[str]] = {
        "ADMIN":              ["staff:view", "staff:create", "staff:edit", "staff:delete", "staff:timesheets", "staff:leave", "staff:documents", "staff:performance"],
        "BRANCH_MANAGER":     ["staff:view", "staff:create", "staff:edit", "staff:delete", "staff:timesheets", "staff:leave", "staff:documents"],
        "PROGRAM_MANAGER":    ["staff:view", "staff:create", "staff:edit", "staff:timesheets", "staff:leave", "staff:documents"],
        "COORDINATOR":        ["staff:view", "staff:edit", "staff:timesheets", "staff:leave"],
        "TEAM_LEADER":        ["staff:view", "staff:timesheets", "staff:leave"],
        "SUPPORT_WORKER":     ["staff:view", "staff:timesheets", "staff:leave"],
        "FINANCE_OFFICER":    ["staff:view"],
        "COMPLIANCE_OFFICER": ["staff:view", "staff:documents"],
        "ROSTERING_OFFICER":  ["staff:view", "staff:timesheets"],
        "HEALTH_SUPPORT":     ["staff:view"],
    }

    try:
        async with engine.connect() as conn:
            schemas_result = await conn.execute(text(
                "SELECT schema_name FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE schema_name LIKE 'tenant_%'"
            ))
            schemas = [row[0] for row in schemas_result.fetchall()]
    except Exception as exc:
        logger.warning("migrate_staff_permissions: could not fetch schemas: %s", exc)
        return

    for s in schemas:
        try:
            async with engine.connect() as conn:
                # 1. Insert missing permission codes
                for perm_code, module, action, description in STAFF_PERMISSIONS:
                    exists = await conn.scalar(text(f"""
                        SELECT COUNT(1) FROM [{s}].[permission]
                        WHERE permission_code = :code
                    """), {"code": perm_code})
                    if not exists:
                        await conn.execute(text(f"""
                            INSERT INTO [{s}].[permission]
                                (permission_code, module, action, description, is_active)
                            VALUES (:code, :module, :action, :desc, 1)
                        """), {"code": perm_code, "module": module, "action": action, "desc": description})
                        logger.info("migrate_staff_permissions: added [%s] %s", s, perm_code)

                # 2. Build lookup maps
                perm_rows = (await conn.execute(text(
                    f"SELECT permission_id, permission_code FROM [{s}].[permission]"
                ))).fetchall()
                perm_map = {row[1]: row[0] for row in perm_rows}

                role_rows = (await conn.execute(text(
                    f"SELECT role_id, role_code FROM [{s}].[role]"
                ))).fetchall()
                role_map = {row[1]: row[0] for row in role_rows}

                # 3. Assign permissions to roles (ignore if already assigned)
                for role_code, codes in ROLE_STAFF_PERMS.items():
                    rid = role_map.get(role_code)
                    if not rid:
                        continue
                    for perm_code in codes:
                        pid = perm_map.get(perm_code)
                        if not pid:
                            continue
                        already = await conn.scalar(text(f"""
                            SELECT COUNT(1) FROM [{s}].[role_permission]
                            WHERE role_id = :rid AND permission_id = :pid
                        """), {"rid": rid, "pid": pid})
                        if not already:
                            await conn.execute(text(f"""
                                INSERT INTO [{s}].[role_permission] (role_id, permission_id, granted)
                                VALUES (:rid, :pid, 1)
                            """), {"rid": rid, "pid": pid})

                await conn.commit()
                logger.info("migrate_staff_permissions: schema [%s] done.", s)

        except Exception as exc:
            logger.warning("migrate_staff_permissions: schema [%s] failed: %s", s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_admin_roles() -> None:
    """Ensure every is_tenant_admin=True user has the ADMIN role assigned in their tenant schema.

    Idempotent — skips users who already have the assignment.
    Runs at startup to backfill existing admins who haven't logged in since
    the auto-assign-at-login logic was added.
    """
    from app.database import engine
    _MIG = "migrate_admin_roles_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    async with engine.connect() as conn:
        # Get all (user_id, schema_name) pairs for is_tenant_admin users
        result = await conn.execute(text("""
            SELECT u.user_id, t.schema_name
            FROM ndis_common.app_user u
            JOIN ndis_common.tenant t ON t.tenant_id = u.tenant_id
            WHERE u.is_tenant_admin = 1
              AND u.is_deleted = 0
              AND t.is_deleted = 0
        """))
        admin_users = result.fetchall()

    for user_id, schema_name in admin_users:
        try:
            async with engine.connect() as conn:
                # Get ADMIN role_id in this tenant schema
                role_row = await conn.execute(text(f"""
                    SELECT role_id FROM [{schema_name}].[role]
                    WHERE role_code = 'ADMIN'
                """))
                role = role_row.fetchone()
                if not role:
                    continue
                role_id = role[0]

                # Check if already assigned
                exists = await conn.execute(text(f"""
                    SELECT 1 FROM [{schema_name}].[user_role]
                    WHERE user_id = :uid AND role_id = :rid
                """), {"uid": user_id, "rid": role_id})
                if exists.fetchone():
                    continue

                # Assign
                await conn.execute(text(f"""
                    INSERT INTO [{schema_name}].[user_role]
                        (user_id, role_id, assigned_by, is_active)
                    VALUES (:uid, :rid, 'SYSTEM', 1)
                """), {"uid": user_id, "rid": role_id})
                await conn.commit()
                logger.info("migrate_admin_roles: assigned ADMIN role to user %s in [%s]", user_id, schema_name)

        except Exception as exc:
            logger.warning("migrate_admin_roles: user %s / schema [%s] failed: %s", user_id, schema_name, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_staff_profile_user_id() -> None:
    """Add user_id column to staff_profile (if missing) and backfill StaffProfiles
    for all existing AppUsers who don't have one yet.

    Idempotent — safe on every restart.
    """
    from app.database import engine
    _MIG = "migrate_staff_profile_user_id_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    async with engine.connect() as conn:
        schemas = await _get_provisioned_schemas(conn)

    for schema in schemas:
        try:
            async with engine.connect() as conn:
                # 1. Add user_id column if it doesn't exist
                col_exists = await conn.execute(text("""
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = :s AND TABLE_NAME = 'staff_profile' AND COLUMN_NAME = 'user_id'
                """), {"s": schema})
                if not col_exists.fetchone():
                    await conn.execute(text(
                        f"ALTER TABLE [{schema}].[staff_profile] ADD user_id NVARCHAR(50) NULL"
                    ))
                    await conn.commit()
                    logger.info("migrate_staff_profile_user_id: added user_id column in [%s]", schema)

                # 2. Get tenant_id for this schema
                tid_row = await conn.execute(text(
                    "SELECT tenant_id FROM ndis_common.tenant WHERE schema_name = :s AND is_deleted = 0"
                ), {"s": schema})
                tid_row = tid_row.fetchone()
                if not tid_row:
                    continue
                tenant_id = tid_row[0]

                # 3. Find all active users in this tenant who have no StaffProfile yet
                users = await conn.execute(text("""
                    SELECT u.user_id, u.first_name, u.last_name, u.email
                    FROM ndis_common.app_user u
                    WHERE u.tenant_id = :tid
                      AND u.is_deleted = 0
                      AND NOT EXISTS (
                          SELECT 1 FROM [{schema}].[staff_profile] sp
                          WHERE sp.user_id = u.user_id AND sp.is_deleted = 0
                      )
                """.replace("{schema}", schema)), {"tid": tenant_id})
                users = users.fetchall()

                for user_id, first_name, last_name, email in users:
                    # Insert StaffProfile linked to this user
                    await conn.execute(text(f"""
                        INSERT INTO [{schema}].[staff_profile]
                            (staff_id, tenant_id, user_id, first_name, last_name, work_email,
                             status, is_deleted, created_by, created_at)
                        VALUES
                            (:sid, :tid, :uid, :fn, :ln, :em,
                             'Active', 0, 'SYSTEM', SYSDATETIMEOFFSET())
                    """), {
                        "sid": user_id,    # use same id for easy cross-reference
                        "tid": tenant_id,
                        "uid": user_id,
                        "fn":  first_name,
                        "ln":  last_name,
                        "em":  email,
                    })
                    logger.info(
                        "migrate_staff_profile_user_id: created StaffProfile for user %s in [%s]",
                        user_id, schema,
                    )

                if users:
                    await conn.commit()

        except Exception as exc:
            logger.warning("migrate_staff_profile_user_id: schema [%s] failed: %s", schema, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def migrate_timesheet_line_columns() -> None:
    """Widen staff_timesheet_line.timesheet_id/shift_id from NVARCHAR(20) to
    NVARCHAR(50) (idempotent).

    Both columns were created too narrow to hold a full UUID (36 chars) —
    timesheet_id is always a UUID (see staff_timesheets.py's _uid()), so
    every "Add Line" insert failed with a SQL Server string-truncation
    error. The matching header table's own timesheet_id column is already
    NVARCHAR(50), so this just brings the line table's columns in line.
    """
    from app.database import engine
    _MIG = "migrate_timesheet_line_columns_v1"

    async with engine.connect() as conn:
        await _ensure_migration_log(conn)
        if await _migration_done(conn, _MIG):
            logger.info("Skipping %s — already applied.", _MIG); return

    try:
        async with engine.connect() as conn:
            schemas = await _get_provisioned_schemas(conn)
    except Exception as exc:
        logger.warning("migrate_timesheet_line_columns(): could not fetch tenant list: %s", exc)
        return

    for s in schemas:
        try:
            async with engine.begin() as conn:
                table_exists = await conn.scalar(text(f"""
                    SELECT COUNT(1) FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = '{s}' AND TABLE_NAME = 'staff_timesheet_line'
                """))
                if not table_exists:
                    continue
                await conn.execute(text(
                    f"ALTER TABLE [{s}].[staff_timesheet_line] ALTER COLUMN timesheet_id NVARCHAR(50) NOT NULL"
                ))
                await conn.execute(text(
                    f"ALTER TABLE [{s}].[staff_timesheet_line] ALTER COLUMN shift_id NVARCHAR(50) NULL"
                ))
                logger.info("migrate_timesheet_line_columns: widened columns in [%s].[staff_timesheet_line]", s)
        except Exception as exc:
            logger.warning("migrate_timesheet_line_columns: failed for [%s]: %s", s, exc)

    async with engine.connect() as conn:
        await _record_migration(conn, _MIG)


async def provision_platform() -> None:
    """Ensure ndis_common schema and its 4 platform tables exist.

    Safe on every restart — provision_common_schema() uses IF NOT EXISTS guards.
    Must run before seed_subscription_plans() so the table exists.
    Uses engine.connect() (not engine.begin()) because provision_common_schema()
    calls conn.commit() internally — engine.begin() would double-commit.
    """
    from app.database import engine
    from app.core.tenant_schema import provision_common_schema

    print(">>> [startup] provision_platform() starting...", flush=True)
    try:
        async with engine.connect() as conn:
            print(">>> [startup] got DB connection, provisioning ndis_common...", flush=True)
            await provision_common_schema(conn)
            print(">>> [startup] ndis_common provisioned OK.", flush=True)
    except Exception as exc:
        import traceback
        print(f">>> [startup] provision_platform() FAILED: {exc}", flush=True)
        traceback.print_exc()
        raise


async def seed_subscription_plans() -> None:
    """Insert Basic/Professional/Enterprise plans if subscription_plan is empty.

    Safe to call on every startup — exits immediately if any rows exist.
    Uses a raw engine connection to avoid chicken-and-egg session issues at
    startup (the session factory needs the DB to be ready first).
    """
    # Import here to avoid circular imports at module load time
    from app.database import engine

    try:
        async with engine.begin() as conn:
            existing = await conn.scalar(
                text("SELECT COUNT(*) FROM [ndis_common].[subscription_plan]")
            )
            if existing and existing > 0:
                logger.info(
                    "subscription_plan already has %d row(s) — skipping seed.", existing
                )
                return

            logger.info("Seeding subscription_plan with %d default plans...", len(_PLANS))
            for plan in _PLANS:
                await conn.execute(
                    text("""
                        INSERT INTO [ndis_common].[subscription_plan]
                            (plan_code, plan_name, max_branches, max_users,
                             max_participants, monthly_price, monthly_fee_aud,
                             annual_fee_aud, is_active)
                        VALUES
                            (:plan_code, :plan_name, :max_branches, :max_users,
                             :max_participants, :monthly_price, :monthly_fee_aud,
                             :annual_fee_aud, 1)
                    """),
                    plan,
                )
            logger.info("Subscription plans seeded: %s",
                        ", ".join(p["plan_code"] for p in _PLANS))
    except Exception as exc:
        # DB may not be reachable yet on the very first boot before migrations run.
        # Log and continue — create_tenant_hierarchy() creates a fallback plan on demand.
        logger.warning(
            "seed_subscription_plans() failed (non-fatal — will use on-demand seed): %s", exc
        )
