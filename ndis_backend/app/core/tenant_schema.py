"""Tenant Schema Provisioning — DDL engine for schema-per-tenant architecture.

Architecture:
  - ndis_common  : Central/Unique schema. Holds platform-level tables only:
                   subscription_plan, tenant, tenant_subscription, app_user
                   (login auth checks this schema first, then the tenant schema)
  - tenant_<id>  : Per-tenant schema. Created at signup. Holds ALL business tables:
                   branch, program, program_branch, role, permission, role_permission,
                   user_role, cross_branch_access, tenant_config, audit_log,
                   tenant_contact, tenant_address, tenant_service_state,
                   tenant_registration_group, tenant_document

Schema naming convention (system-controlled, never user-provided):
  tenant_code "SUNSHI-001"  →  schema_name "tenant_sunshi_001"

Usage:
  from app.core.tenant_schema import generate_schema_name, provision_tenant_schema
"""
import re
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# ─── SQLAlchemy placeholder ────────────────────────────────────────────────────
# All per-tenant ORM models declare  __table_args__ = {"schema": "tenant_schema"}
# At request time, get_tenant_db() applies:
#   schema_translate_map={"tenant_schema": actual_schema_name}
# so all generated SQL uses the real schema name.
TENANT_SCHEMA_PLACEHOLDER = "tenant_schema"

# Central/Unique schema — never changes, shared by the whole platform
UNIQUE_SCHEMA = "ndis_common"


# ─── Schema name generation ────────────────────────────────────────────────────

def generate_schema_name(tenant_code: str) -> str:
    """Convert system-generated tenant_code to a safe MSSQL schema name.

    Rules:
      - Lowercased
      - Only alphanumeric + underscore kept
      - Prefixed with "tenant_" to namespace clearly
      - Never derived from raw user input (tenant_code is system-generated)

    Examples:
      "SUNSHI-001"  →  "tenant_sunshi_001"
      "CARENG-002"  →  "tenant_careng_002"
    """
    safe = re.sub(r"[^a-zA-Z0-9]", "_", tenant_code).lower()
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe).strip("_")
    return f"tenant_{safe}"


# ─── Schema existence check ────────────────────────────────────────────────────

async def schema_exists(conn: AsyncConnection, schema_name: str) -> bool:
    """Returns True if the MSSQL schema already exists in the current database."""
    result = await conn.execute(
        text("SELECT 1 FROM sys.schemas WHERE name = :schema"),
        {"schema": schema_name},
    )
    return result.fetchone() is not None


# ─── ndis_common schema creation ──────────────────────────────────────────────

async def provision_common_schema(conn: AsyncConnection) -> None:
    """Creates the [ndis_common] (unique) schema and platform-level tables only.

    Tables: subscription_plan, tenant, tenant_subscription, app_user.
    All tenant-specific operational data lives in the per-tenant schema
    created by provision_tenant_schema().

    Safe to call multiple times — uses IF NOT EXISTS guards throughout.
    Called once at application startup or via migration.
    """
    logger.info("Provisioning [ndis_common] schema...")

    # 1. Create schema if absent
    await conn.execute(text(
        "IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ndis_common') "
        "EXEC sp_executesql N'CREATE SCHEMA [ndis_common]'"
    ))

    # 2. subscription_plan ────────────────────────────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'subscription_plan')
        CREATE TABLE [ndis_common].[subscription_plan] (
            plan_id             INT IDENTITY(1,1) PRIMARY KEY,
            plan_code           NVARCHAR(50)   NOT NULL UNIQUE,
            plan_name           NVARCHAR(150)  NOT NULL,
            max_branches        INT            NOT NULL DEFAULT 1,
            max_users           INT            NOT NULL DEFAULT 5,
            max_participants    INT            NOT NULL DEFAULT 50,
            monthly_price       DECIMAL(10,2)  NOT NULL DEFAULT 0,
            monthly_fee_aud     DECIMAL(10,2)  NOT NULL DEFAULT 0,
            annual_fee_aud      DECIMAL(10,2)  NOT NULL DEFAULT 0,
            features_json       NVARCHAR(MAX)  NULL,
            is_active           BIT            NOT NULL DEFAULT 1,
            created_at          DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at          DATETIMEOFFSET NULL
        )
    """))

    # 3. tenant ───────────────────────────────────────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'tenant')
        CREATE TABLE [ndis_common].[tenant] (
            tenant_id                   INT IDENTITY(1,1) PRIMARY KEY,
            tenant_code                 NVARCHAR(50)   NULL UNIQUE,
            schema_name                 NVARCHAR(128)  NULL UNIQUE,
            organisation_name           NVARCHAR(255)  NOT NULL,
            trading_name                NVARCHAR(255)  NULL,
            abn                         NVARCHAR(11)   NULL,
            acn                         NVARCHAR(9)    NULL,
            is_registered_provider      BIT            NOT NULL DEFAULT 0,
            ndis_registration_number    NVARCHAR(20)   NULL,
            registration_expiry_date    DATE           NULL,
            provider_type               NVARCHAR(50)   NULL,
            organisation_type           NVARCHAR(50)   NULL,
            primary_email               NVARCHAR(255)  NOT NULL,
            primary_phone               NVARCHAR(20)   NULL,
            website_url                 NVARCHAR(500)  NULL,
            logo_url                    NVARCHAR(500)  NULL,
            timezone                    NVARCHAR(100)  NOT NULL DEFAULT 'Australia/Sydney',
            status                      NVARCHAR(20)   NOT NULL DEFAULT 'Active',
            is_deleted                  BIT            NOT NULL DEFAULT 0,
            deleted_at                  DATETIMEOFFSET NULL,
            created_by                  INT            NULL,
            created_at                  DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  INT            NULL,
            updated_at                  DATETIMEOFFSET NULL
        )
    """))

    # 3b. Fix abn uniqueness — replace inline UNIQUE (blocks multiple NULLs in SQL Server)
    #     with a filtered unique index (only enforces uniqueness when abn IS NOT NULL).
    #     This block runs on every startup and is idempotent.
    await conn.execute(text("""
        -- Drop any system-generated or inline UNIQUE constraint on abn
        DECLARE @cn NVARCHAR(200)
        SELECT @cn = kc.name
        FROM sys.key_constraints kc
        JOIN sys.index_columns ic
            ON kc.unique_index_id = ic.index_id
            AND kc.parent_object_id = ic.object_id
        JOIN sys.columns c
            ON ic.object_id = c.object_id
            AND ic.column_id = c.column_id
        WHERE kc.type = 'UQ'
          AND kc.parent_object_id = OBJECT_ID('ndis_common.tenant')
          AND c.name = 'abn'

        IF @cn IS NOT NULL
            EXEC('ALTER TABLE [ndis_common].[tenant] DROP CONSTRAINT [' + @cn + ']')
    """))

    await conn.execute(text("""
        -- Create filtered unique index: ABN must be unique only when not NULL
        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'UX_tenant_abn_not_null'
              AND object_id = OBJECT_ID('ndis_common.tenant')
        )
        CREATE UNIQUE INDEX UX_tenant_abn_not_null
            ON [ndis_common].[tenant] (abn)
            WHERE abn IS NOT NULL
    """))

    await conn.execute(text("""
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns
            WHERE object_id = OBJECT_ID('ndis_common.tenant')
              AND name = 'email_domain'
        )
        ALTER TABLE [ndis_common].[tenant]
            ADD email_domain NVARCHAR(255) NULL
    """))

    # Drop the unique index first so the cleanup UPDATEs below can run freely,
    # then recreate it clean. This handles both fresh installs and re-runs.
    await conn.execute(text("""
        IF EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'UX_tenant_email_domain'
              AND object_id = OBJECT_ID('ndis_common.tenant')
        )
        DROP INDEX UX_tenant_email_domain ON [ndis_common].[tenant]
    """))

    await conn.execute(text("""
        -- Step 1: wipe all email_domain values so we start from a clean slate
        UPDATE [ndis_common].[tenant] SET email_domain = NULL
    """))

    await conn.execute(text("""
        -- Step 2: backfill only non-public, unique domains (earliest tenant wins)
        UPDATE t
        SET t.email_domain = d.domain
        FROM [ndis_common].[tenant] t
        INNER JOIN (
            SELECT
                MIN(tenant_id) AS tenant_id,
                LOWER(SUBSTRING(primary_email, CHARINDEX('@', primary_email) + 1,
                                LEN(primary_email))) AS domain
            FROM [ndis_common].[tenant]
            WHERE primary_email IS NOT NULL
              AND CHARINDEX('@', primary_email) > 0
              AND LOWER(SUBSTRING(primary_email, CHARINDEX('@', primary_email) + 1,
                                  LEN(primary_email))) NOT IN (
                    'gmail.com','googlemail.com',
                    'yahoo.com','yahoo.com.au','ymail.com',
                    'outlook.com','hotmail.com','hotmail.com.au','live.com','live.com.au',
                    'icloud.com','me.com','mac.com',
                    'aol.com','protonmail.com','proton.me','zoho.com','mail.com',
                    'bigpond.com','bigpond.net.au','optusnet.com.au','internode.on.net'
              )
            GROUP BY LOWER(SUBSTRING(primary_email, CHARINDEX('@', primary_email) + 1,
                                     LEN(primary_email)))
        ) d ON t.tenant_id = d.tenant_id
    """))

    await conn.execute(text("""
        -- Step 3: create the filtered unique index on the now-clean data
        CREATE UNIQUE INDEX UX_tenant_email_domain
            ON [ndis_common].[tenant] (email_domain)
            WHERE email_domain IS NOT NULL
    """))

    await conn.execute(text("""
        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'UX_tenant_email_domain'
              AND object_id = OBJECT_ID('ndis_common.tenant')
        )
        CREATE UNIQUE INDEX UX_tenant_email_domain
            ON [ndis_common].[tenant] (email_domain)
            WHERE email_domain IS NOT NULL
    """))

    # 4. tenant_subscription ──────────────────────────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'tenant_subscription')
        CREATE TABLE [ndis_common].[tenant_subscription] (
            subscription_id INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id       INT            NOT NULL REFERENCES [ndis_common].[tenant](tenant_id),
            plan_id         INT            NOT NULL REFERENCES [ndis_common].[subscription_plan](plan_id),
            billing_cycle   NVARCHAR(20)   NOT NULL DEFAULT 'Monthly',
            start_date      DATE           NOT NULL,
            end_date        DATE           NULL,
            status          NVARCHAR(20)   NOT NULL DEFAULT 'Active',
            created_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at      DATETIMEOFFSET NULL
        )
    """))

    # 5. app_user ──────────────────────────────────────────────────────────────
    # Note: branch_id is stored here for reference but NO FK constraint to the
    # per-tenant schema — cross-schema FKs complicate schema provisioning.
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'app_user')
        CREATE TABLE [ndis_common].[app_user] (
            user_id             NVARCHAR(50)   NOT NULL PRIMARY KEY,
            tenant_id           INT            NOT NULL REFERENCES [ndis_common].[tenant](tenant_id),
            branch_id           INT            NULL,
            email               NVARCHAR(255)  NOT NULL,
            password_hash       NVARCHAR(500)  NOT NULL,
            first_name          NVARCHAR(100)  NOT NULL,
            last_name           NVARCHAR(100)  NOT NULL,
            mobile              NVARCHAR(20)   NULL,
            job_title           NVARCHAR(150)  NULL,
            is_tenant_admin     BIT            NOT NULL DEFAULT 0,
            is_active           BIT            NOT NULL DEFAULT 1,
            is_deleted          BIT            NOT NULL DEFAULT 0,
            must_change_password BIT           NOT NULL DEFAULT 0,
            deleted_at          DATETIMEOFFSET NULL,
            last_login_at       DATETIMEOFFSET NULL,
            password_changed_at DATETIMEOFFSET NULL,
            created_by          NVARCHAR(50)   NULL,
            created_at          DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)   NULL,
            updated_at          DATETIMEOFFSET NULL,
            CONSTRAINT UQ_app_user_tenant_email UNIQUE (tenant_id, email)
        )
    """))

    # qualification — master catalogue (shared) ──────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'qualification')
        CREATE TABLE [ndis_common].[qualification] (
            qualification_id            NVARCHAR(20)    NOT NULL PRIMARY KEY,
            qualification_type          NVARCHAR(150)   NOT NULL,
            qualification_level         NVARCHAR(50)    NULL,
            qualification_description   NVARCHAR(500)   NULL,
            is_active                   BIT             NOT NULL DEFAULT 1,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        )
    """))

    # certification — master catalogue (shared) ───────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'certification')
        CREATE TABLE [ndis_common].[certification] (
            certification_id            NVARCHAR(20)    NOT NULL PRIMARY KEY,
            certification_name          NVARCHAR(150)   NOT NULL,
            certification_category      NVARCHAR(50)    NULL,
            certification_description   NVARCHAR(500)   NULL,
            expiry_applicability        BIT             NULL,
            validity_period_months      INT             NULL,
            renewal_required            BIT             NULL,
            is_active                   BIT             NOT NULL DEFAULT 1,
            is_deleted                  BIT             NOT NULL DEFAULT 0,
            created_by                  NVARCHAR(50)    NULL,
            created_at                  DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by                  NVARCHAR(50)    NULL,
            updated_at                  DATETIMEOFFSET  NULL
        )
    """))

    # leave_type — master catalogue (shared) ──────────────────────────────────
    await conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'leave_type')
        CREATE TABLE [ndis_common].[leave_type] (
            leave_type_id   NVARCHAR(50)    NOT NULL PRIMARY KEY,
            leave_type_name NVARCHAR(50)    NOT NULL,
            leave_code      NVARCHAR(10)    NULL,
            paid_leave      BIT             NULL,
            description     NVARCHAR(255)   NULL,
            is_active       BIT             NOT NULL DEFAULT 1,
            created_at      DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET()
        )
    """))

    await conn.commit()
    logger.info("[ndis_common] schema provisioned successfully.")


# ─── Per-tenant schema creation ────────────────────────────────────────────────

async def provision_tenant_schema(conn: AsyncConnection, schema_name: str) -> None:
    """Creates a new per-tenant schema and all 15 business tables inside it.

    Safe to call on retry — all CREATE TABLE statements are guarded by IF NOT EXISTS.
    The schema_name is always system-generated (never user input).

    Tables created:
      branch, program, program_branch, role, permission, role_permission,
      user_role, cross_branch_access, tenant_config, audit_log,
      tenant_contact, tenant_address, tenant_service_state,
      tenant_registration_group, tenant_document
    """
    if await schema_exists(conn, schema_name):
        logger.warning("Tenant schema [%s] already exists — skipping creation.", schema_name)
        return

    logger.info("Provisioning tenant schema [%s]...", schema_name)

    # 1. Create the schema
    await conn.execute(text(
        f"CREATE SCHEMA [{schema_name}]"
    ))

    s = schema_name  # shorthand for f-strings below

    # 2. branch ────────────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[branch] (
            branch_id         INT IDENTITY(1,1) PRIMARY KEY,
            branch_code       NVARCHAR(50)   NOT NULL,
            branch_name       NVARCHAR(255)  NOT NULL,
            branch_type       NVARCHAR(100)  NULL,
            parent_branch_id  INT            NULL,
            branch_status     NVARCHAR(50)   NULL DEFAULT 'Active',
            phone             NVARCHAR(20)   NULL,
            email             NVARCHAR(255)  NULL,
            address_line1     NVARCHAR(255)  NULL,
            address_line2     NVARCHAR(255)  NULL,
            suburb            NVARCHAR(100)  NULL,
            state_code        NVARCHAR(10)   NULL,
            postcode          NVARCHAR(10)   NULL,
            country           NVARCHAR(100)  NULL,
            timezone          NVARCHAR(100)  NULL,
            operating_hours   NVARCHAR(MAX)  NULL,
            facilities        NVARCHAR(MAX)  NULL,
            notes             NVARCHAR(MAX)  NULL,
            contact_person    NVARCHAR(255)  NULL,
            contact_title     NVARCHAR(150)  NULL,
            contact_phone     NVARCHAR(20)   NULL,
            contact_mobile    NVARCHAR(20)   NULL,
            contact_email     NVARCHAR(255)  NULL,
            is_head_office    BIT            NOT NULL DEFAULT 0,
            is_active         BIT            NOT NULL DEFAULT 1,
            is_deleted        BIT            NOT NULL DEFAULT 0,
            deleted_at        DATETIMEOFFSET NULL,
            created_by        INT            NULL,
            created_at        DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by        INT            NULL,
            updated_at        DATETIMEOFFSET NULL,
            CONSTRAINT UQ_branch_code_{s} UNIQUE (branch_code)
        )
    """))

    # 3. program ───────────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[program] (
            program_id      INT IDENTITY(1,1) PRIMARY KEY,
            program_code    NVARCHAR(50)   NOT NULL UNIQUE,
            program_name    NVARCHAR(255)  NOT NULL,
            description     NVARCHAR(MAX)  NULL,
            funding_type    NVARCHAR(100)  NULL,
            is_active       BIT            NOT NULL DEFAULT 1,
            is_deleted      BIT            NOT NULL DEFAULT 0,
            deleted_at      DATETIMEOFFSET NULL,
            created_by      INT            NULL,
            created_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by      INT            NULL,
            updated_at      DATETIMEOFFSET NULL
        )
    """))

    # 4. program_branch ────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[program_branch] (
            program_branch_id INT IDENTITY(1,1) PRIMARY KEY,
            program_id  INT NOT NULL REFERENCES [{s}].[program](program_id) ON DELETE CASCADE,
            branch_id   INT NOT NULL REFERENCES [{s}].[branch](branch_id)  ON DELETE CASCADE,
            is_active   BIT NOT NULL DEFAULT 1,
            created_at  DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            CONSTRAINT UQ_prog_branch_{s} UNIQUE (program_id, branch_id)
        )
    """))

    # 5. role ──────────────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[role] (
            role_id        INT IDENTITY(1,1) PRIMARY KEY,
            role_code      NVARCHAR(50)   NOT NULL UNIQUE,
            role_name      NVARCHAR(150)  NOT NULL,
            description    NVARCHAR(MAX)  NULL,
            is_system_role BIT            NOT NULL DEFAULT 0,
            is_active      BIT            NOT NULL DEFAULT 1,
            is_deleted     BIT            NOT NULL DEFAULT 0,
            deleted_at     DATETIMEOFFSET NULL,
            created_by     INT            NULL,
            created_at     DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by     INT            NULL,
            updated_at     DATETIMEOFFSET NULL
        )
    """))

    # 6. permission ────────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[permission] (
            permission_id   INT IDENTITY(1,1) PRIMARY KEY,
            permission_code NVARCHAR(100)  NOT NULL UNIQUE,
            module          NVARCHAR(100)  NOT NULL,
            action          NVARCHAR(50)   NOT NULL,
            description     NVARCHAR(255)  NULL,
            is_active       BIT            NOT NULL DEFAULT 1,
            created_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
        )
    """))

    # 6b. Seed default NDIS permissions ─────────────────────────────────────────
    # Codes use module:action format matching seed.py ROLE_PERMS for easy assignment
    _permissions = [
        # Branch management
        ("branches:view",   "branches", "view",   "View branch details"),
        ("branches:create", "branches", "create", "Create a new branch"),
        ("branches:edit",   "branches", "edit",   "Update branch details"),
        ("branches:delete", "branches", "delete", "Soft-delete a branch"),
        # Program management
        ("programs:view",   "programs", "view",   "View programs"),
        ("programs:create", "programs", "create", "Create programs"),
        ("programs:edit",   "programs", "edit",   "Edit programs"),
        ("programs:delete", "programs", "delete", "Delete programs"),
        # Role management
        ("roles:view",   "roles", "view",   "View roles"),
        ("roles:create", "roles", "create", "Create roles"),
        ("roles:edit",   "roles", "edit",   "Edit roles"),
        ("roles:delete", "roles", "delete", "Delete roles"),
        # Permission management
        ("permissions:view",   "permissions", "view",   "View permissions"),
        ("permissions:assign", "permissions", "assign", "Assign permissions to roles"),
        # User management
        ("users:view",        "users", "view",        "View users"),
        ("users:create",      "users", "create",      "Create users"),
        ("users:edit",        "users", "edit",        "Edit user details"),
        ("users:delete",      "users", "delete",      "Deactivate users"),
        ("users:role_assign", "users", "role_assign", "Assign roles to users"),
        # Settings / tenant config
        ("settings:view", "settings", "view", "View tenant configuration"),
        ("settings:edit", "settings", "edit", "Edit tenant configuration"),
        # Audit log
        ("audit:view", "audit", "view", "View audit logs"),
        # Participant management
        ("participants:view",   "participants", "view",   "View participants"),
        ("participants:create", "participants", "create", "Create participants"),
        ("participants:edit",   "participants", "edit",   "Edit participants"),
        ("participants:delete", "participants", "delete", "Delete participants"),
        # Schedules / shifts
        ("schedules:view",   "schedules", "view",   "View shifts and schedules"),
        ("schedules:create", "schedules", "create", "Create shifts and schedules"),
        ("schedules:edit",   "schedules", "edit",   "Edit shifts and schedules"),
        ("schedules:delete", "schedules", "delete", "Delete shifts and schedules"),
        # Progress notes
        ("progress_notes:view",   "progress_notes", "view",   "View progress notes"),
        ("progress_notes:create", "progress_notes", "create", "Create progress notes"),
        ("progress_notes:edit",   "progress_notes", "edit",   "Edit progress notes"),
        ("progress_notes:delete", "progress_notes", "delete", "Delete progress notes"),
        # Incidents
        ("incidents:view",   "incidents", "view",   "View incidents"),
        ("incidents:create", "incidents", "create", "Create incidents"),
        ("incidents:edit",   "incidents", "edit",   "Edit incidents"),
        ("incidents:delete", "incidents", "delete", "Delete incidents"),
        # Documents
        ("documents:view",   "documents", "view",   "View documents"),
        ("documents:create", "documents", "create", "Upload documents"),
        ("documents:edit",   "documents", "edit",   "Edit documents"),
        ("documents:delete", "documents", "delete", "Delete documents"),
        # Support plans
        ("plans:view",   "plans", "view",   "View support plans"),
        ("plans:create", "plans", "create", "Create support plans"),
        ("plans:edit",   "plans", "edit",   "Edit support plans"),
        ("plans:delete", "plans", "delete", "Delete support plans"),
        # Reports
        ("reports:view",   "reports", "view",   "View reports"),
        ("reports:create", "reports", "create", "Create reports"),
        ("reports:edit",   "reports", "edit",   "Edit reports"),
        # Invoices
        ("invoices:view",   "invoices", "view",   "View invoices"),
        ("invoices:create", "invoices", "create", "Create invoices"),
        ("invoices:edit",   "invoices", "edit",   "Edit invoices"),
        ("invoices:delete", "invoices", "delete", "Delete invoices"),
        # Staff management
        ("staff:view",       "staff", "view",       "View staff profiles and details"),
        ("staff:create",     "staff", "create",     "Add a new staff member"),
        ("staff:edit",       "staff", "edit",       "Edit staff details"),
        ("staff:delete",     "staff", "delete",     "Deactivate / soft-delete a staff member"),
        ("staff:timesheets", "staff", "timesheets", "Submit and approve staff timesheets"),
        ("staff:leave",      "staff", "leave",      "Submit and approve staff leave requests"),
        ("staff:documents",  "staff", "documents",  "Upload and manage staff documents"),
        ("staff:performance", "staff", "performance", "Create and manage staff performance reviews, goals and KPIs"),
    ]
    for perm_code, module, action, description in _permissions:
        await conn.execute(text(f"""
            INSERT INTO [{s}].[permission] (permission_code, module, action, description, is_active)
            VALUES (:code, :module, :action, :description, 1)
        """), {"code": perm_code, "module": module, "action": action, "description": description})

    # 7. role_permission ───────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[role_permission] (
            role_permission_id  INT IDENTITY(1,1) PRIMARY KEY,
            role_id             INT NOT NULL REFERENCES [{s}].[role](role_id)             ON DELETE CASCADE,
            permission_id       INT NOT NULL REFERENCES [{s}].[permission](permission_id) ON DELETE CASCADE,
            granted             BIT           NOT NULL DEFAULT 1,
            granted_by          INT           NULL,
            granted_at          DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            CONSTRAINT UQ_role_perm_{s} UNIQUE (role_id, permission_id)
        )
    """))

    # 8. user_role ─────────────────────────────────────────────────────────────
    # user_id references ndis_common.app_user — logical ref, no DB FK constraint
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[user_role] (
            user_role_id INT IDENTITY(1,1) PRIMARY KEY,
            user_id      NVARCHAR(50)   NOT NULL,
            role_id      INT            NOT NULL REFERENCES [{s}].[role](role_id) ON DELETE CASCADE,
            assigned_by  NVARCHAR(50)   NULL,
            assigned_at  DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            is_active    BIT            NOT NULL DEFAULT 1,
            CONSTRAINT UQ_user_role_{s} UNIQUE (user_id, role_id)
        )
    """))

    # 9. cross_branch_access ─── full schema (4.1–4.7) ───────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[cross_branch_access] (
            access_id            INT IDENTITY(1,1) PRIMARY KEY,
            staff_user_id        NVARCHAR(50)   NOT NULL,
            home_branch_id       INT            NOT NULL,
            target_branch_id     INT            NOT NULL,
            participant_id       NVARCHAR(100)  NULL,
            participant_name     NVARCHAR(255)  NULL,
            permitted_activities NVARCHAR(MAX)  NULL,
            access_reason        NVARCHAR(500)  NOT NULL,
            services_description NVARCHAR(MAX)  NULL,
            access_start         DATETIMEOFFSET NULL,
            access_end           DATETIMEOFFSET NULL,
            access_type          NVARCHAR(20)   NOT NULL DEFAULT 'planned',
            is_emergency         BIT            NOT NULL DEFAULT 0,
            emergency_reason     NVARCHAR(500)  NULL,
            requires_review      BIT            NOT NULL DEFAULT 0,
            reviewed_by          NVARCHAR(50)   NULL,
            reviewed_at          DATETIMEOFFSET NULL,
            review_notes         NVARCHAR(500)  NULL,
            status               NVARCHAR(20)   NOT NULL DEFAULT 'pending',
            requested_by         NVARCHAR(50)   NOT NULL,
            requested_at         DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            approved_by          NVARCHAR(50)   NULL,
            approved_at          DATETIMEOFFSET NULL,
            approval_comments    NVARCHAR(500)  NULL,
            rejected_by          NVARCHAR(50)   NULL,
            rejected_at          DATETIMEOFFSET NULL,
            rejection_reason     NVARCHAR(500)  NULL,
            revoked_by           NVARCHAR(50)   NULL,
            revoked_at           DATETIMEOFFSET NULL,
            revoke_reason        NVARCHAR(500)  NULL,
            is_active            BIT            NOT NULL DEFAULT 1,
            is_deleted           BIT            NOT NULL DEFAULT 0,
            created_at           DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at           DATETIMEOFFSET NULL
        )
    """))

    # 10. tenant_config ────────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_config] (
            config_id                           INT IDENTITY(1,1) PRIMARY KEY,

            -- 8.2 Regional & Timezone
            country                             NVARCHAR(100)  NOT NULL DEFAULT 'Australia',
            state                                NVARCHAR(100)  NULL,
            date_format                          NVARCHAR(20)   NOT NULL DEFAULT 'DD/MM/YYYY',
            time_format                          NVARCHAR(10)   NOT NULL DEFAULT '24h',
            week_starts_on                       NVARCHAR(10)   NOT NULL DEFAULT 'Monday',
            timezone                             NVARCHAR(100)  NOT NULL DEFAULT 'Australia/Sydney',

            -- 8.3 Currency & Tax
            currency_code                        NVARCHAR(3)    NOT NULL DEFAULT 'AUD',
            enable_gst                           BIT            NOT NULL DEFAULT 1,
            gst_rate                             INT            NOT NULL DEFAULT 10,
            enable_schads_award                  BIT            NOT NULL DEFAULT 1,

            -- 8.4 Billing & Invoice
            invoice_prefix                       NVARCHAR(20)   NOT NULL DEFAULT 'INV',
            invoice_due_days                     INT            NOT NULL DEFAULT 14,
            billing_frequency                    NVARCHAR(50)   NOT NULL DEFAULT 'Monthly',
            payment_terms                        NVARCHAR(200)  NULL,
            auto_invoice_enabled                 BIT            NOT NULL DEFAULT 0,
            default_funding_type                 NVARCHAR(50)   NOT NULL DEFAULT 'Agency Managed',

            -- 8.5 Notification Configuration
            notify_email_enabled                 BIT            NOT NULL DEFAULT 1,
            notify_sms_enabled                    BIT            NOT NULL DEFAULT 0,
            notify_inapp_enabled                  BIT            NOT NULL DEFAULT 1,
            notify_appointment_reminders          BIT            NOT NULL DEFAULT 1,
            notify_plan_expiry_alerts             BIT            NOT NULL DEFAULT 1,
            notify_overdue_payment_alerts         BIT            NOT NULL DEFAULT 1,
            notify_budget_alerts                  BIT            NOT NULL DEFAULT 1,
            notify_reminder_hours_before          INT            NOT NULL DEFAULT 24,

            -- 8.6 Security & Access
            session_timeout_minutes              INT            NOT NULL DEFAULT 60,
            password_min_length                  INT            NOT NULL DEFAULT 8,
            password_require_uppercase           BIT            NOT NULL DEFAULT 1,
            password_require_numbers             BIT            NOT NULL DEFAULT 1,
            password_require_symbols             BIT            NOT NULL DEFAULT 0,
            max_login_attempts                   INT            NOT NULL DEFAULT 5,
            mfa_enabled                          BIT            NOT NULL DEFAULT 0,

            -- 8.7 Integration Configuration
            enable_pace_integration              BIT            NOT NULL DEFAULT 0,
            enable_proda_integration             BIT            NOT NULL DEFAULT 0,
            integration_myob_enabled             BIT            NOT NULL DEFAULT 0,
            integration_xero_enabled             BIT            NOT NULL DEFAULT 0,
            integration_communication_provider   NVARCHAR(50)   NULL,
            integration_payment_provider          NVARCHAR(50)   NULL,

            -- Metadata
            updated_by                           INT            NULL,
            created_at                           DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at                           DATETIMEOFFSET NULL
        )
    """))

    # 11. audit_log ────────────────────────────────────────────────────────────
    # PK is BIGINT (audit_id) to match the AuditLog ORM model (BigInteger).
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[audit_log] (
            audit_id    BIGINT IDENTITY(1,1) PRIMARY KEY,
            user_id     NVARCHAR(50)   NULL,
            action      NVARCHAR(100)  NOT NULL,
            table_name  NVARCHAR(100)  NOT NULL,
            record_id   NVARCHAR(100)  NULL,
            old_values  NVARCHAR(MAX)  NULL,
            new_values  NVARCHAR(MAX)  NULL,
            ip_address  NVARCHAR(45)   NULL,
            user_agent  NVARCHAR(500)  NULL,
            created_at  DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
        )
    """))

    # 12. tenant_contact ───────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_contact] (
            contact_id      INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id       INT            NOT NULL,
            contact_type    NVARCHAR(50)   NOT NULL DEFAULT 'Primary',
            first_name      NVARCHAR(100)  NOT NULL,
            last_name       NVARCHAR(100)  NOT NULL,
            position_title  NVARCHAR(150)  NULL,
            email           NVARCHAR(255)  NULL,
            phone           NVARCHAR(20)   NULL,
            mobile          NVARCHAR(20)   NULL,
            is_active       BIT            NOT NULL DEFAULT 1,
            created_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at      DATETIMEOFFSET NULL,
            CONSTRAINT UQ_tenant_contact_type_{s} UNIQUE (tenant_id, contact_type)
        )
    """))

    # 13. tenant_address ───────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_address] (
            address_id      INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id       INT            NOT NULL,
            address_type    NVARCHAR(50)   NOT NULL DEFAULT 'Head Office',
            address_line1   NVARCHAR(255)  NULL,
            address_line2   NVARCHAR(255)  NULL,
            suburb          NVARCHAR(100)  NULL,
            state_code      NVARCHAR(10)   NULL,
            postcode        NVARCHAR(10)   NULL,
            country_code    NVARCHAR(3)    NOT NULL DEFAULT 'AUS',
            is_primary      BIT            NOT NULL DEFAULT 1,
            created_at      DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at      DATETIMEOFFSET NULL
        )
    """))

    # 14. tenant_service_state ─────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_service_state] (
            service_state_id INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id        INT            NOT NULL,
            state_code       NVARCHAR(10)   NOT NULL,
            is_active        BIT            NOT NULL DEFAULT 1,
            created_at       DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            CONSTRAINT UQ_tenant_service_state_{s} UNIQUE (tenant_id, state_code)
        )
    """))

    # 15. tenant_registration_group ────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_registration_group] (
            tenant_reg_group_id      INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id                INT            NOT NULL,
            registration_group_code  NVARCHAR(20)   NOT NULL,
            registration_group_name  NVARCHAR(255)  NOT NULL,
            is_active                BIT            NOT NULL DEFAULT 1,
            created_at               DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            CONSTRAINT UQ_tenant_reg_group_{s} UNIQUE (tenant_id, registration_group_code)
        )
    """))

    # 16. tenant_document ──────────────────────────────────────────────────────
    await conn.execute(text(f"""
        CREATE TABLE [{s}].[tenant_document] (
            document_id       INT IDENTITY(1,1) PRIMARY KEY,
            tenant_id         INT             NOT NULL,
            document_category NVARCHAR(100)   NOT NULL,
            document_name     NVARCHAR(255)   NOT NULL,
            file_path         NVARCHAR(1000)  NOT NULL,
            file_size_kb      INT             NULL,
            mime_type         NVARCHAR(100)   NULL,
            linked_to         NVARCHAR(255)   NULL,
            expiry_date       DATE            NULL,
            uploaded_by       NVARCHAR(50)    NOT NULL,
            uploaded_at       DATETIMEOFFSET  NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            is_deleted        BIT             NOT NULL DEFAULT 0,
            deleted_at        DATETIMEOFFSET  NULL
        )
    """))

    # 17. Staff Management tables ─────────────────────────────────────────────
    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_profile')
        CREATE TABLE [{s}].[staff_profile] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_personal_info')
        CREATE TABLE [{s}].[staff_personal_info] (
            personal_id                 NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id                   INT             NOT NULL,
            staff_id                    NVARCHAR(50)    NOT NULL,
            dob                         DATE            NULL,
            gender                      NVARCHAR(20)    NULL,
            blood_group                 NVARCHAR(10)    NULL,
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_contact_info')
        CREATE TABLE [{s}].[staff_contact_info] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_identification')
        CREATE TABLE [{s}].[staff_identification] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_preferences')
        CREATE TABLE [{s}].[staff_preferences] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_emergency_contact')
        CREATE TABLE [{s}].[staff_emergency_contact] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='employment_information')
        CREATE TABLE [{s}].[employment_information] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_probation')
        CREATE TABLE [{s}].[staff_probation] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_contract')
        CREATE TABLE [{s}].[staff_contract] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_roles')
        CREATE TABLE [{s}].[staff_roles] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_exit_process')
        CREATE TABLE [{s}].[staff_exit_process] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_qualification')
        CREATE TABLE [{s}].[staff_qualification] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_certification')
        CREATE TABLE [{s}].[staff_certification] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_availability')
        CREATE TABLE [{s}].[staff_availability] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_timesheet_header')
        CREATE TABLE [{s}].[staff_timesheet_header] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_timesheet_line')
        CREATE TABLE [{s}].[staff_timesheet_line] (
            timesheet_line_id       NVARCHAR(50)    NOT NULL PRIMARY KEY,
            tenant_id               INT             NOT NULL,
            timesheet_id            NVARCHAR(20)    NOT NULL,
            shift_id                NVARCHAR(20)    NULL,
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_leave_request')
        CREATE TABLE [{s}].[staff_leave_request] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_leave_request_date')
        CREATE TABLE [{s}].[staff_leave_request_date] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_leave_balance')
        CREATE TABLE [{s}].[staff_leave_balance] (
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
        )
    """))

    await conn.execute(text(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                       WHERE TABLE_SCHEMA='{s}' AND TABLE_NAME='staff_document_repository')
        CREATE TABLE [{s}].[staff_document_repository] (
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
        )
    """))

    # 18. Seed default NDIS roles ─────────────────────────────────────────────
    # Every new tenant starts with the standard 10 NDIS roles + Admin.
    # Tenants can edit, delete, or add more roles via the Roles & Permissions screen.
    _default_roles = [
        ("SUPPORT_WORKER",    "Support Worker",    "Delivers direct support to NDIS participants in daily living activities."),
        ("TEAM_LEADER",       "Team Leader",       "Supervises support workers and coordinates day-to-day team operations."),
        ("COORDINATOR",       "Coordinator",       "Coordinates support plans and services for a caseload of participants."),
        ("BRANCH_MANAGER",    "Branch Manager",    "Oversees branch operations, staffing, compliance and service quality."),
        ("PROGRAM_MANAGER",   "Program Manager",   "Manages specific support programs including planning and reporting."),
        ("FINANCE_OFFICER",   "Finance Officer",   "Handles invoicing, claims, budgets, and financial reporting."),
        ("COMPLIANCE_OFFICER","Compliance Officer","Monitors regulatory compliance, incident reporting, and audits."),
        ("ROSTERING_OFFICER", "Rostering Officer", "Manages staff rosters, shift scheduling, and leave management."),
        ("HEALTH_SUPPORT",    "Health Support",    "Provides health-related support and monitors participant wellbeing."),
        ("ADMIN",             "Admin",             "Full system access. Manages users, roles, branches, programs, settings and all operational data."),
    ]
    for role_code, role_name, description in _default_roles:
        await conn.execute(text(f"""
            INSERT INTO [{s}].[role] (role_code, role_name, description, is_system_role, is_active, is_deleted)
            VALUES (:code, :name, :desc, 0, 1, 0)
        """), {"code": role_code, "name": role_name, "desc": description})

    # 18. Seed role-permission assignments ────────────────────────────────────
    # Build a lookup: permission_code -> permission_id
    perm_rows = (await conn.execute(text(f"SELECT permission_id, permission_code FROM [{s}].[permission]"))).fetchall()
    perm_map = {row[1]: row[0] for row in perm_rows}

    role_rows_db = (await conn.execute(text(f"SELECT role_id, role_code FROM [{s}].[role]"))).fetchall()
    role_map = {row[1]: row[0] for row in role_rows_db}

    _all_perms = list(perm_map.keys())

    _role_perms = {
        "ADMIN": _all_perms,
        "BRANCH_MANAGER": [
            "branches:view", "branches:edit",
            "programs:view", "programs:create", "programs:edit", "programs:delete",
            "users:view", "users:create", "users:edit", "users:role_assign",
            "roles:view", "permissions:view",
            "participants:view", "participants:create", "participants:edit",
            "schedules:view", "schedules:create", "schedules:edit", "schedules:delete",
            "progress_notes:view", "progress_notes:create", "progress_notes:edit",
            "incidents:view", "incidents:create", "incidents:edit",
            "documents:view", "documents:create", "documents:edit",
            "plans:view", "plans:create", "plans:edit",
            "reports:view", "reports:create", "reports:edit",
            "invoices:view",
            "settings:view",
            "audit:view",
            # staff
            "staff:view", "staff:create", "staff:edit", "staff:delete",
            "staff:timesheets", "staff:leave", "staff:documents",
        ],
        "PROGRAM_MANAGER": [
            "branches:view",
            "programs:view", "programs:create", "programs:edit",
            "users:view",
            "participants:view", "participants:create", "participants:edit",
            "schedules:view", "schedules:create", "schedules:edit",
            "progress_notes:view", "progress_notes:create", "progress_notes:edit",
            "incidents:view", "incidents:create", "incidents:edit",
            "documents:view", "documents:create", "documents:edit",
            "plans:view", "plans:create", "plans:edit",
            "reports:view", "reports:create",
            "invoices:view",
            # staff
            "staff:view", "staff:create", "staff:edit",
            "staff:timesheets", "staff:leave", "staff:documents",
        ],
        "COORDINATOR": [
            "branches:view",
            "programs:view",
            "users:view",
            "participants:view", "participants:create", "participants:edit",
            "schedules:view", "schedules:create", "schedules:edit",
            "progress_notes:view", "progress_notes:create", "progress_notes:edit",
            "incidents:view", "incidents:create",
            "documents:view", "documents:create",
            "plans:view", "plans:create", "plans:edit",
            "reports:view",
            "invoices:view",
            # staff
            "staff:view", "staff:edit",
            "staff:timesheets", "staff:leave",
        ],
        "TEAM_LEADER": [
            "branches:view",
            "programs:view",
            "users:view",
            "participants:view", "participants:edit",
            "schedules:view", "schedules:create", "schedules:edit",
            "progress_notes:view", "progress_notes:create", "progress_notes:edit",
            "incidents:view", "incidents:create",
            "documents:view", "documents:create",
            "plans:view",
            "reports:view",
            # staff
            "staff:view", "staff:timesheets", "staff:leave",
        ],
        "SUPPORT_WORKER": [
            "participants:view",
            "schedules:view",
            "progress_notes:view", "progress_notes:create",
            "incidents:view", "incidents:create",
            "documents:view",
            "plans:view",
            # staff — can only view and submit their own timesheets/leave
            "staff:view", "staff:timesheets", "staff:leave",
        ],
        "FINANCE_OFFICER": [
            "branches:view",
            "programs:view",
            "participants:view",
            "invoices:view", "invoices:create", "invoices:edit", "invoices:delete",
            "reports:view", "reports:create", "reports:edit",
            "documents:view", "documents:create",
            "settings:view",
            # staff — view-only for payroll context
            "staff:view",
        ],
        "COMPLIANCE_OFFICER": [
            "branches:view",
            "programs:view",
            "users:view",
            "participants:view",
            "incidents:view", "incidents:create", "incidents:edit",
            "documents:view", "documents:create", "documents:edit",
            "plans:view",
            "reports:view", "reports:create", "reports:edit",
            "audit:view",
            "settings:view",
            # staff — view and manage compliance documents
            "staff:view", "staff:documents",
        ],
        "ROSTERING_OFFICER": [
            "branches:view",
            "programs:view",
            "users:view",
            "participants:view",
            "schedules:view", "schedules:create", "schedules:edit", "schedules:delete",
            "documents:view",
            "reports:view",
            # staff — view and manage timesheets/availability for rostering
            "staff:view", "staff:timesheets",
        ],
        "HEALTH_SUPPORT": [
            "participants:view", "participants:edit",
            "schedules:view",
            "progress_notes:view", "progress_notes:create", "progress_notes:edit",
            "incidents:view", "incidents:create",
            "documents:view", "documents:create",
            "plans:view", "plans:edit",
            # staff — view only
            "staff:view",
        ],
    }

    for role_code, perm_codes in _role_perms.items():
        rid = role_map.get(role_code)
        if not rid:
            continue
        for perm_code in perm_codes:
            pid = perm_map.get(perm_code)
            if not pid:
                continue
            await conn.execute(text(f"""
                INSERT INTO [{s}].[role_permission] (role_id, permission_id, granted)
                VALUES (:rid, :pid, 1)
            """), {"rid": rid, "pid": pid})

    await conn.commit()
    logger.info("Tenant schema [%s] provisioned with 16 tables, %d default roles.", schema_name, len(_default_roles))
