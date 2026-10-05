-- Migration: Add user_id column to staff_profile (links staff to AppUser)
-- Schema: tenant_testor_001
-- Run this in SSMS before restarting the backend.

DECLARE @schema NVARCHAR(50) = 'tenant_testor_001';

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'staff_profile' AND COLUMN_NAME = 'user_id'
)
    EXEC('ALTER TABLE ' + @schema + '.staff_profile ADD user_id NVARCHAR(50) NULL');

-- Optional index for fast lookups by user_id
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_staff_profile_user_id'
      AND object_id = OBJECT_ID(@schema + '.staff_profile')
)
    EXEC('CREATE INDEX IX_staff_profile_user_id ON ' + @schema + '.staff_profile(user_id)');

PRINT 'Migration complete for: ' + @schema;
