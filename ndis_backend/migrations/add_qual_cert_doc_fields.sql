-- Migration: Add expiry_date + document_url to staff_qualification,
--            and document_url to staff_certification
-- Schema: tenant_testor_001

DECLARE @schema NVARCHAR(50) = 'tenant_testor_001';

-- staff_qualification
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'staff_qualification' AND COLUMN_NAME = 'expiry_date')
    EXEC('ALTER TABLE ' + @schema + '.staff_qualification ADD expiry_date DATE NULL');

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'staff_qualification' AND COLUMN_NAME = 'document_url')
    EXEC('ALTER TABLE ' + @schema + '.staff_qualification ADD document_url NVARCHAR(MAX) NULL');

-- staff_certification
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @schema AND TABLE_NAME = 'staff_certification' AND COLUMN_NAME = 'document_url')
    EXEC('ALTER TABLE ' + @schema + '.staff_certification ADD document_url NVARCHAR(MAX) NULL');

PRINT 'Migration complete for: ' + @schema;
