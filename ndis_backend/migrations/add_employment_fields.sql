-- Migration: Add missing fields to employment_information table
-- Schema: tenant_testor_001

DECLARE @schema NVARCHAR(50) = 'tenant_testor_001';
DECLARE @tbl NVARCHAR(200) = @schema + '.employment_information';

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'employment_information' AND COLUMN_NAME = 'pay_point')
    EXEC('ALTER TABLE ' + @tbl + ' ADD pay_point NVARCHAR(30) NULL');

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'employment_information' AND COLUMN_NAME = 'position_title')
    EXEC('ALTER TABLE ' + @tbl + ' ADD position_title NVARCHAR(100) NULL');

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'employment_information' AND COLUMN_NAME = 'department')
    EXEC('ALTER TABLE ' + @tbl + ' ADD department NVARCHAR(100) NULL');

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'employment_information' AND COLUMN_NAME = 'contracted_hours_per_week')
    EXEC('ALTER TABLE ' + @tbl + ' ADD contracted_hours_per_week NUMERIC(5,2) NULL');

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'employment_information' AND COLUMN_NAME = 'notes')
    EXEC('ALTER TABLE ' + @tbl + ' ADD notes NVARCHAR(MAX) NULL');

PRINT 'Migration complete for: ' + @schema;
