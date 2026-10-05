"""Create ndis_common schema — platform-level tables only.

Tables: subscription_plan, tenant, tenant_subscription, app_user.
All tenant-specific data (contacts, addresses, service states, registration groups,
documents, etc.) now lives in the per-tenant schema managed by 0001_initial_tenant_schema.py.

This migration is STAMPED (not run) on existing databases created via
provision_common_schema() or direct SQL scripts.

On a brand-new database, run:
    alembic upgrade head          # runs the DDL
OR:
    alembic stamp 0002            # if ndis_common already exists

Per-tenant schemas (tenant_<id>) are NOT managed by Alembic —
they are created at signup time by provision_tenant_schema() in app/core/tenant_schema.py.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import DATETIMEOFFSET

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. ndis_common schema
    op.execute("IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ndis_common') "
               "EXEC sp_executesql N'CREATE SCHEMA [ndis_common]'")

    # 2. subscription_plan
    op.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'subscription_plan')
        CREATE TABLE [ndis_common].[subscription_plan] (
            plan_id          INT IDENTITY(1,1) PRIMARY KEY,
            plan_code        NVARCHAR(50)   NOT NULL UNIQUE,
            plan_name        NVARCHAR(150)  NOT NULL,
            max_branches     INT            NOT NULL DEFAULT 1,
            max_users        INT            NOT NULL DEFAULT 5,
            max_participants INT            NOT NULL DEFAULT 50,
            monthly_price    DECIMAL(10,2)  NOT NULL DEFAULT 0,
            monthly_fee_aud  DECIMAL(10,2)  NULL,
            annual_fee_aud   DECIMAL(10,2)  NULL,
            is_active        BIT            NOT NULL DEFAULT 1,
            created_at       DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_at       DATETIMEOFFSET NULL
        )
    """)

    # 3. tenant
    op.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'tenant')
        CREATE TABLE [ndis_common].[tenant] (
            tenant_id                INT IDENTITY(1,1) PRIMARY KEY,
            tenant_code              NVARCHAR(50)   NULL UNIQUE,
            schema_name              NVARCHAR(128)  NULL UNIQUE,
            organisation_name        NVARCHAR(255)  NOT NULL,
            trading_name             NVARCHAR(255)  NULL,
            abn                      NVARCHAR(11)   NULL UNIQUE,
            acn                      NVARCHAR(9)    NULL,
            is_registered_provider   BIT            NOT NULL DEFAULT 0,
            ndis_registration_number NVARCHAR(20)   NULL,
            registration_expiry_date DATE           NULL,
            provider_type            NVARCHAR(50)   NULL,
            organisation_type        NVARCHAR(50)   NULL,
            primary_email            NVARCHAR(255)  NOT NULL,
            primary_phone            NVARCHAR(20)   NULL,
            website_url              NVARCHAR(500)  NULL,
            logo_url                 NVARCHAR(500)  NULL,
            timezone                 NVARCHAR(100)  NOT NULL DEFAULT 'Australia/Sydney',
            status                   NVARCHAR(20)   NOT NULL DEFAULT 'Active',
            is_deleted               BIT            NOT NULL DEFAULT 0,
            deleted_at               DATETIMEOFFSET NULL,
            created_by               INT            NULL,
            created_at               DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by               INT            NULL,
            updated_at               DATETIMEOFFSET NULL
        )
    """)

    # 4. tenant_subscription
    op.execute("""
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
    """)

    # 5. app_user
    op.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables t
                       JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'ndis_common' AND t.name = 'app_user')
        CREATE TABLE [ndis_common].[app_user] (
            user_id             NVARCHAR(50)   NOT NULL PRIMARY KEY,
            tenant_id           INT            NOT NULL REFERENCES [ndis_common].[tenant](tenant_id),
            branch_id           INT            NOT NULL,
            email               NVARCHAR(255)  NOT NULL,
            password_hash       NVARCHAR(500)  NOT NULL,
            first_name          NVARCHAR(100)  NOT NULL,
            last_name           NVARCHAR(100)  NOT NULL,
            mobile              NVARCHAR(20)   NULL,
            job_title           NVARCHAR(150)  NULL,
            is_tenant_admin     BIT            NOT NULL DEFAULT 0,
            is_active           BIT            NOT NULL DEFAULT 1,
            is_deleted          BIT            NOT NULL DEFAULT 0,
            deleted_at          DATETIMEOFFSET NULL,
            last_login_at       DATETIMEOFFSET NULL,
            password_changed_at DATETIMEOFFSET NULL,
            created_by          NVARCHAR(50)   NULL,
            created_at          DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
            updated_by          NVARCHAR(50)   NULL,
            updated_at          DATETIMEOFFSET NULL,
            CONSTRAINT UQ_app_user_tenant_email UNIQUE (tenant_id, email)
        )
    """)


def downgrade() -> None:
    # Drop in reverse dependency order (4 platform tables only)
    op.execute("IF EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'ndis_common' AND t.name = 'app_user') DROP TABLE [ndis_common].[app_user]")
    op.execute("IF EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'ndis_common' AND t.name = 'tenant_subscription') DROP TABLE [ndis_common].[tenant_subscription]")
    op.execute("IF EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'ndis_common' AND t.name = 'tenant') DROP TABLE [ndis_common].[tenant]")
    op.execute("IF EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'ndis_common' AND t.name = 'subscription_plan') DROP TABLE [ndis_common].[subscription_plan]")
