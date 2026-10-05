/*
  One-time repair script.
  Run this in SSMS (or sqlcmd) against the NDIS_DB database.

  Why: provision_tenant_schema() originally created [tenant_config] with only
  13 columns, but the TenantConfig ORM model has 39. Any tenant schema that
  was provisioned (fully or partially) BEFORE the DDL fix in
  app/core/tenant_schema.py is missing those columns and will keep failing
  signup/config calls with "Invalid column name ..." even after the code fix,
  because provision_tenant_schema() skips schemas that already exist.

  This script is idempotent — safe to run multiple times. It:
    1. Finds every schema that has a [tenant_config] table and adds any
       column that's missing (checked via sys.columns before each ADD).
    2. Adds [must_change_password] to [ndis_common].[app_user] if missing
       (same stale-DDL issue, hits Phase D of signup next).

  After running this, retry "Skip for now" / "Complete registration" in the
  app — it should go through for tenant_myorga_006 and any other affected
  tenant without needing to delete/recreate anything.
*/

SET NOCOUNT ON;

DECLARE @schema NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

DECLARE schema_cursor CURSOR FOR
    SELECT DISTINCT s.name
    FROM sys.tables t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE t.name = 'tenant_config';

OPEN schema_cursor;
FETCH NEXT FROM schema_cursor INTO @schema;

WHILE @@FETCH_STATUS = 0
BEGIN
    PRINT 'Patching [' + @schema + '].[tenant_config] ...';

    -- Regional & Timezone
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'country')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD country NVARCHAR(100) NOT NULL DEFAULT ''Australia''');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'state')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD state NVARCHAR(100) NULL');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'time_format')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD time_format NVARCHAR(10) NOT NULL DEFAULT ''24h''');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'week_starts_on')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD week_starts_on NVARCHAR(10) NOT NULL DEFAULT ''Monday''');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'timezone')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD timezone NVARCHAR(100) NOT NULL DEFAULT ''Australia/Sydney''');

    -- Currency & Tax
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'gst_rate')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD gst_rate INT NOT NULL DEFAULT 10');

    -- Billing & Invoice
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'billing_frequency')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD billing_frequency NVARCHAR(50) NOT NULL DEFAULT ''Monthly''');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'payment_terms')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD payment_terms NVARCHAR(200) NULL');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'auto_invoice_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD auto_invoice_enabled BIT NOT NULL DEFAULT 0');

    -- default_funding_type already exists in old DDL as NULL-able; make sure it exists at all (very old schemas)
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'default_funding_type')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD default_funding_type NVARCHAR(50) NOT NULL DEFAULT ''Agency Managed''');

    -- Notification Configuration
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_email_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_email_enabled BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_sms_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_sms_enabled BIT NOT NULL DEFAULT 0');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_inapp_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_inapp_enabled BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_appointment_reminders')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_appointment_reminders BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_plan_expiry_alerts')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_plan_expiry_alerts BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_overdue_payment_alerts')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_overdue_payment_alerts BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_budget_alerts')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_budget_alerts BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'notify_reminder_hours_before')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD notify_reminder_hours_before INT NOT NULL DEFAULT 24');

    -- Security & Access
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'session_timeout_minutes')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD session_timeout_minutes INT NOT NULL DEFAULT 60');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'password_min_length')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD password_min_length INT NOT NULL DEFAULT 8');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'password_require_uppercase')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD password_require_uppercase BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'password_require_numbers')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD password_require_numbers BIT NOT NULL DEFAULT 1');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'password_require_symbols')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD password_require_symbols BIT NOT NULL DEFAULT 0');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'max_login_attempts')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD max_login_attempts INT NOT NULL DEFAULT 5');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'mfa_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD mfa_enabled BIT NOT NULL DEFAULT 0');

    -- Integration Configuration
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'integration_myob_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD integration_myob_enabled BIT NOT NULL DEFAULT 0');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'integration_xero_enabled')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD integration_xero_enabled BIT NOT NULL DEFAULT 0');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'integration_communication_provider')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD integration_communication_provider NVARCHAR(50) NULL');

    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(QUOTENAME(@schema) + '.tenant_config') AND name = 'integration_payment_provider')
        EXEC('ALTER TABLE [' + @schema + '].[tenant_config] ADD integration_payment_provider NVARCHAR(50) NULL');

    PRINT '  done.';

    FETCH NEXT FROM schema_cursor INTO @schema;
END

CLOSE schema_cursor;
DEALLOCATE schema_cursor;

-- ── app_user: must_change_password (Phase D of signup — same stale-DDL issue) ──
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('ndis_common.app_user') AND name = 'must_change_password'
)
BEGIN
    PRINT 'Patching [ndis_common].[app_user] — adding must_change_password ...';
    EXEC('ALTER TABLE [ndis_common].[app_user] ADD must_change_password BIT NOT NULL DEFAULT 0');
    PRINT '  done.';
END
ELSE
BEGIN
    PRINT '[ndis_common].[app_user] already has must_change_password — skipped.';
END

PRINT 'All done. Retry signup now.';
