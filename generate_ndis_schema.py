# Python script to generate complete, production-ready MSSQL schema for NDIS SaaS Application
import os

sql_content = """-- ============================================================================
-- NDIS MANAGEMENT SYSTEM (SaaS) — COMPLETE MSSQL DATABASE SCHEMA
-- ============================================================================
-- Application: NDIS Management System SaaS
-- Target Database: Microsoft SQL Server 2019+ (MSSQL)
-- Compliance: NDIS Quality & Safeguards Commission, NDIA PRODA/PACE, SCHADS Award, ATO GST
-- Architecture: Multi-tenant B2B SaaS with Schema-based logical segregation
-- ORM Compatibility: SQLAlchemy reflection & Alembic migration ready
-- Schemas: [master] -> [tenant] -> [participant] -> [staff]
-- ============================================================================

SET NOCOUNT ON;
GO

-- ============================================================================
-- SCHEMA CREATION
-- Order: master -> tenant -> participant -> staff
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'master')
BEGIN
    EXEC('CREATE SCHEMA [master]');
END
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'tenant')
BEGIN
    EXEC('CREATE SCHEMA [tenant]');
END
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'participant')
BEGIN
    EXEC('CREATE SCHEMA [participant]');
END
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'staff')
BEGIN
    EXEC('CREATE SCHEMA [staff]');
END
GO

-- ============================================================================
-- MODULE 1: MASTER SCHEMA TABLES
-- Reference and lookup data shared across all tenants
-- ============================================================================

-- 1.1 master.country
-- ISO country reference table. Used by addresses across all modules.
CREATE TABLE [master].[country] (
    [country_id] INT IDENTITY(1,1) NOT NULL,
    [country_code] NVARCHAR(5) NOT NULL,    -- ISO 3166-1 alpha-2 / alpha-3 e.g. 'AU'
    [country_name] NVARCHAR(100) NOT NULL,
    [dial_code] NVARCHAR(10) NULL,           -- International dial code e.g. '+61'
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_country] PRIMARY KEY CLUSTERED ([country_id]),
    CONSTRAINT [UQ_country_country_code] UNIQUE ([country_code])
);
GO

-- 1.2 master.state
-- Australian states and territories. Used by all address fields.
CREATE TABLE [master].[state] (
    [state_id] INT IDENTITY(1,1) NOT NULL,
    [country_id] INT NOT NULL,              -- FK to master.country
    [state_code] NVARCHAR(10) NOT NULL,     -- State code e.g. 'NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT'
    [state_name] NVARCHAR(100) NOT NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_state] PRIMARY KEY CLUSTERED ([state_id]),
    CONSTRAINT [FK_state_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [UQ_state_country_state_code] UNIQUE ([country_id], [state_code])
);
GO

-- 1.3 master.disability_type
-- NDIS disability categories for participant profiles.
CREATE TABLE [master].[disability_type] (
    [disability_type_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,           -- Identifier e.g. 'AUTISM', 'PSYCHOSOCIAL', 'INTELLECTUAL'
    [label] NVARCHAR(200) NOT NULL,         -- Human-readable disability label
    [description] NVARCHAR(500) NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_disability_type] PRIMARY KEY CLUSTERED ([disability_type_id]),
    CONSTRAINT [UQ_disability_type_code] UNIQUE ([code])
);
GO

-- 1.4 master.document_category
-- Defines document types used across participant, staff, and tenant document repositories.
CREATE TABLE [master].[document_category] (
    [document_category_id] INT IDENTITY(1,1) NOT NULL,
    [module] NVARCHAR(50) NOT NULL,         -- Target subsystem
    [category_code] NVARCHAR(50) NOT NULL,  -- Unique category code within module
    [category_name] NVARCHAR(150) NOT NULL, -- Display name e.g. 'NDIS Plan PDF', 'Police Check'
    [requires_expiry] BIT DEFAULT 0 NOT NULL, -- Whether documents under this category must track expiry
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_document_category] PRIMARY KEY CLUSTERED ([document_category_id]),
    CONSTRAINT [CK_document_category_module] CHECK ([module] IN ('PARTICIPANT','STAFF','TENANT','ALL')),
    CONSTRAINT [UQ_document_category_module_code] UNIQUE ([module], [category_code])
);
GO

-- 1.5 master.ndis_support_category
-- NDIS funding categories from the NDIS Support Catalogue. Used in plan funding allocation.
CREATE TABLE [master].[ndis_support_category] (
    [support_category_id] INT IDENTITY(1,1) NOT NULL,
    [category_number] NVARCHAR(10) NOT NULL, -- Official NDIA category number e.g. '01', '02', '03'
    [category_code] NVARCHAR(50) NOT NULL,   -- e.g. 'DAILY_ACTIVITIES', 'TRANSPORT'
    [category_name] NVARCHAR(300) NOT NULL,  -- e.g. 'Daily Activities'
    [funding_type] NVARCHAR(30) NOT NULL,    -- Core, Capacity Building, or Capital
    [is_active] BIT DEFAULT 1 NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    CONSTRAINT [PK_master_ndis_support_category] PRIMARY KEY CLUSTERED ([support_category_id]),
    CONSTRAINT [UQ_ndis_support_category_category_number] UNIQUE ([category_number]),
    CONSTRAINT [UQ_ndis_support_category_category_code] UNIQUE ([category_code]),
    CONSTRAINT [CK_ndis_support_category_funding_type] CHECK ([funding_type] IN ('Core','Capacity Building','Capital'))
);
GO

-- 1.6 master.ndis_support_item
-- Individual NDIS support items with price caps from the NDIS Support Catalogue / Price Guide.
CREATE TABLE [master].[ndis_support_item] (
    [support_item_id] INT IDENTITY(1,1) NOT NULL,
    [support_category_id] INT NOT NULL,       -- FK to master.ndis_support_category
    [item_number] NVARCHAR(20) NOT NULL,      -- Full item reference e.g. '01_002_0107_1_1'
    [item_name] NVARCHAR(500) NOT NULL,
    [unit_type] NVARCHAR(10) NOT NULL,        -- Unit measure: H (Hour), EA (Each), D (Day), WK (Week), MON (Month)
    [max_price_standard] DECIMAL(10,4) NULL,  -- Standard weekday daytime price cap
    [max_price_evening] DECIMAL(10,4) NULL,   -- Evening price cap
    [max_price_saturday] DECIMAL(10,4) NULL,  -- Saturday price cap
    [max_price_sunday] DECIMAL(10,4) NULL,    -- Sunday price cap
    [max_price_public_holiday] DECIMAL(10,4) NULL, -- Public holiday price cap
    [gst_applicable] BIT DEFAULT 0 NOT NULL,  -- NDIS supports are typically GST-free under ATO ruling
    [is_active] BIT DEFAULT 1 NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    CONSTRAINT [PK_master_ndis_support_item] PRIMARY KEY CLUSTERED ([support_item_id]),
    CONSTRAINT [FK_ndis_support_item_ndis_support_category] FOREIGN KEY ([support_category_id]) REFERENCES [master].[ndis_support_category]([support_category_id]),
    CONSTRAINT [UQ_ndis_support_item_item_number] UNIQUE ([item_number]),
    CONSTRAINT [CK_ndis_support_item_unit_type] CHECK ([unit_type] IN ('H','EA','D','WK','MON'))
);
GO

-- 1.7 master.registration_group
-- NDIS registration groups. Registered providers select applicable registration groups.
CREATE TABLE [master].[registration_group] (
    [reg_group_id] INT IDENTITY(1,1) NOT NULL,
    [group_number] NVARCHAR(10) NOT NULL,   -- 4-digit code e.g. '0107', '0104'
    [group_code] NVARCHAR(100) NOT NULL,
    [group_name] NVARCHAR(300) NOT NULL,    -- e.g. 'Assist-Personal Activities High'
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_registration_group] PRIMARY KEY CLUSTERED ([reg_group_id]),
    CONSTRAINT [UQ_registration_group_group_number] UNIQUE ([group_number])
);
GO

-- 1.8 master.qualification_type
-- Types of qualifications that staff can hold (e.g. Certificate III, Degree).
CREATE TABLE [master].[qualification_type] (
    [qualification_type_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,           -- Unique identifier code
    [name] NVARCHAR(200) NOT NULL,          -- e.g. 'Certificate III in Individual Support'
    [level] NVARCHAR(50) NULL,              -- e.g. 'Certificate','Diploma','Degree','Postgraduate'
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_qualification_type] PRIMARY KEY CLUSTERED ([qualification_type_id]),
    CONSTRAINT [UQ_qualification_type_code] UNIQUE ([code])
);
GO

-- 1.9 master.compliance_type
-- Types of compliance checks required for staff (e.g. WWCC, Police Check, First Aid, NDIS Worker Screening).
CREATE TABLE [master].[compliance_type] (
    [compliance_type_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,
    [name] NVARCHAR(200) NOT NULL,          -- Full clearance name
    [short_name] NVARCHAR(50) NULL,         -- Abbreviation e.g. 'WWCC', 'NDIS_WSC', 'CPR'
    [is_mandatory] BIT DEFAULT 1 NOT NULL,  -- Mandatory check for service delivery
    [renewal_required] BIT DEFAULT 0 NOT NULL,
    [renewal_period_months] INT NULL,       -- Months before expiry warning
    [applies_to_state] BIT DEFAULT 0 NOT NULL, -- Whether check rules differ per state (e.g. WWCC)
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_compliance_type] PRIMARY KEY CLUSTERED ([compliance_type_id]),
    CONSTRAINT [UQ_compliance_type_code] UNIQUE ([code])
);
GO

-- 1.10 master.relationship_type
-- Relationship types for participant emergency contacts.
CREATE TABLE [master].[relationship_type] (
    [relationship_type_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,           -- e.g. 'FATHER', 'MOTHER', 'GUARDIAN'
    [label] NVARCHAR(100) NOT NULL,         -- e.g. 'Father', 'Guardian'
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_relationship_type] PRIMARY KEY CLUSTERED ([relationship_type_id]),
    CONSTRAINT [UQ_relationship_type_code] UNIQUE ([code])
);
GO

-- 1.11 master.leave_type
-- Types of staff leave according to SCHADS Award and National Employment Standards (NES).
CREATE TABLE [master].[leave_type] (
    [leave_type_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,           -- e.g. 'ANNUAL', 'SICK', 'LSL'
    [name] NVARCHAR(100) NOT NULL,
    [is_paid] BIT DEFAULT 1 NOT NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_leave_type] PRIMARY KEY CLUSTERED ([leave_type_id]),
    CONSTRAINT [UQ_leave_type_code] UNIQUE ([code])
);
GO

-- 1.12 master.risk_category
-- Categories of risk flags for participants and safety assessments.
CREATE TABLE [master].[risk_category] (
    [risk_category_id] INT IDENTITY(1,1) NOT NULL,
    [code] NVARCHAR(50) NOT NULL,           -- e.g. 'FALLS', 'MEDICATION', 'BEHAVIOUR'
    [name] NVARCHAR(200) NOT NULL,          -- Display category name
    [description] NVARCHAR(500) NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_master_risk_category] PRIMARY KEY CLUSTERED ([risk_category_id]),
    CONSTRAINT [UQ_risk_category_code] UNIQUE ([code])
);
GO

-- ============================================================================
-- MODULE 2: TENANT SCHEMA TABLES
-- Tenant, organisation, branch, program, user, and RBAC tables
-- ============================================================================

-- 2.1 tenant.subscription_plan
-- SaaS subscription tiers available to tenants. Top of subscription hierarchy.
CREATE TABLE [tenant].[subscription_plan] (
    [plan_id] INT IDENTITY(1,1) NOT NULL,
    [plan_code] NVARCHAR(50) NOT NULL,       -- e.g. 'STARTER', 'GROWTH', 'ENTERPRISE'
    [plan_name] NVARCHAR(100) NOT NULL,
    [description] NVARCHAR(500) NULL,
    [max_participants] INT NULL,             -- NULL = unlimited
    [max_staff] INT NULL,                    -- NULL = unlimited
    [max_branches] INT NULL,                 -- NULL = unlimited
    [max_users] INT NULL,                    -- NULL = unlimited
    [monthly_price_aud] DECIMAL(10,2) NOT NULL,
    [annual_price_aud] DECIMAL(10,2) NULL,
    [features_json] NVARCHAR(MAX) NULL,      -- JSON list of feature flags enabled for tier
    [is_active] BIT DEFAULT 1 NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    CONSTRAINT [PK_tenant_subscription_plan] PRIMARY KEY CLUSTERED ([plan_id]),
    CONSTRAINT [UQ_subscription_plan_plan_code] UNIQUE ([plan_code])
);
GO

-- 2.2 tenant.tenant
-- Core tenant/organisation record. Top of the operational hierarchy. Every other tenant table references this.
CREATE TABLE [tenant].[tenant] (
    [tenant_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_code] NVARCHAR(50) NOT NULL,     -- System-generated unique slug e.g. 'CARE-001'
    [org_legal_name] NVARCHAR(255) NOT NULL, -- Legal registered entity name
    [org_trading_name] NVARCHAR(255) NULL,   -- Trading name if different
    [abn] NVARCHAR(11) NOT NULL,             -- Australian Business Number, exactly 11 digits
    [acn] NVARCHAR(9) NULL,                  -- Australian Company Number, 9 digits if Pty Ltd
    [business_type] NVARCHAR(50) NOT NULL,   -- Business structure
    [provider_type] NVARCHAR(20) NOT NULL,   -- Registered or Non-Registered NDIS provider
    [ndis_registration_no] NVARCHAR(20) NULL, -- Format: 4XXXXXXXX (NDIS Commission issued)
    [ndis_registration_expiry] DATE NULL,    -- Required for Registered providers
    [plan_id] INT NULL,                      -- Current SaaS subscription plan
    [participant_count_range] NVARCHAR(20) NULL, -- '1-10','11-50','51-200','200+'
    [staff_count_range] NVARCHAR(20) NULL,       -- '1-5','6-20','21-100','100+'
    [primary_service_types] NVARCHAR(500) NULL,  -- Comma-separated service lines
    [logo_url] NVARCHAR(500) NULL,
    [tenant_status] NVARCHAR(20) DEFAULT 'Pending' NOT NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant] PRIMARY KEY CLUSTERED ([tenant_id]),
    CONSTRAINT [FK_tenant_subscription_plan] FOREIGN KEY ([plan_id]) REFERENCES [tenant].[subscription_plan]([plan_id]),
    CONSTRAINT [UQ_tenant_tenant_code] UNIQUE ([tenant_code]),
    CONSTRAINT [UQ_tenant_abn] UNIQUE ([abn]),
    CONSTRAINT [CK_tenant_business_type] CHECK ([business_type] IN ('Sole Trader','Partnership','Pty Ltd','Trust','Association','Incorporated Body','Other')),
    CONSTRAINT [CK_tenant_provider_type] CHECK ([provider_type] IN ('Registered','Non-Registered')),
    CONSTRAINT [CK_tenant_tenant_status] CHECK ([tenant_status] IN ('Pending','Active','Suspended','Deactivated','Restricted'))
);
GO

-- 2.3 tenant.tenant_subscription
-- Tracks which subscription plan a tenant is actively on and recurring billing history.
CREATE TABLE [tenant].[tenant_subscription] (
    [subscription_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [plan_id] INT NOT NULL,
    [billing_cycle] NVARCHAR(20) NOT NULL,   -- 'Monthly' or 'Annual'
    [start_date] DATE NOT NULL,
    [end_date] DATE NULL,
    [next_billing_date] DATE NULL,
    [subscription_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL,
    [trial_ends_at] DATE NULL,
    [cancelled_at] DATETIMEOFFSET NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant_subscription] PRIMARY KEY CLUSTERED ([subscription_id]),
    CONSTRAINT [FK_tenant_subscription_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_tenant_subscription_plan_ref] FOREIGN KEY ([plan_id]) REFERENCES [tenant].[subscription_plan]([plan_id]),
    CONSTRAINT [CK_tenant_subscription_billing_cycle] CHECK ([billing_cycle] IN ('Monthly','Annual')),
    CONSTRAINT [CK_tenant_subscription_status] CHECK ([subscription_status] IN ('Active','Expired','Cancelled','Suspended','Trial'))
);
GO

-- 2.4 tenant.tenant_contact
-- Primary and secondary key contact persons for the tenant organisation.
CREATE TABLE [tenant].[tenant_contact] (
    [contact_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [first_name] NVARCHAR(100) NOT NULL,
    [last_name] NVARCHAR(100) NOT NULL,
    [position_title] NVARCHAR(100) NOT NULL, -- e.g. 'CEO','Director','Operations Manager'
    [email] NVARCHAR(255) NOT NULL,
    [phone] NVARCHAR(20) NOT NULL,
    [mobile] NVARCHAR(20) NULL,
    [is_primary] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant_contact] PRIMARY KEY CLUSTERED ([contact_id]),
    CONSTRAINT [FK_tenant_contact_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id])
);
GO

-- 2.5 tenant.tenant_address
-- Business address(es) of the tenant organisation (supports multiple operational types).
CREATE TABLE [tenant].[tenant_address] (
    [address_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [address_type] NVARCHAR(30) NOT NULL,    -- 'Registered','Postal','Service Delivery','Billing'
    [street_address] NVARCHAR(255) NOT NULL,
    [suburb] NVARCHAR(100) NOT NULL,
    [state_id] INT NOT NULL,
    [postcode] NVARCHAR(10) NOT NULL,
    [country_id] INT NOT NULL,
    [is_primary] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant_address] PRIMARY KEY CLUSTERED ([address_id]),
    CONSTRAINT [FK_tenant_address_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_tenant_address_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_tenant_address_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [CK_tenant_address_type] CHECK ([address_type] IN ('Registered','Postal','Service Delivery','Billing'))
);
GO

-- 2.6 tenant.tenant_service_state
-- The Australian states and territories in which the tenant organisation delivers services.
CREATE TABLE [tenant].[tenant_service_state] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [state_id] INT NOT NULL,
    CONSTRAINT [PK_tenant_tenant_service_state] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_tenant_service_state_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_tenant_service_state_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [UQ_tenant_service_state_tenant_state] UNIQUE ([tenant_id], [state_id])
);
GO

-- 2.7 tenant.tenant_registration_group
-- NDIS registration groups held by the tenant organisation (Registered providers only).
CREATE TABLE [tenant].[tenant_registration_group] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [reg_group_id] INT NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    CONSTRAINT [PK_tenant_tenant_registration_group] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_tenant_registration_group_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_tenant_registration_group_registration_group] FOREIGN KEY ([reg_group_id]) REFERENCES [master].[registration_group]([reg_group_id]),
    CONSTRAINT [UQ_tenant_registration_group_tenant_reg_group] UNIQUE ([tenant_id], [reg_group_id])
);
GO

-- 2.8 tenant.tenant_document
-- Organisation-level compliance and operational documents (insurances, NDIS audit certificates).
CREATE TABLE [tenant].[tenant_document] (
    [document_id] NVARCHAR(50) NOT NULL,     -- UUID primary key
    [tenant_id] INT NOT NULL,
    [document_category_id] INT NOT NULL,
    [document_name] NVARCHAR(255) NOT NULL,
    [description] NVARCHAR(500) NULL,
    [file_url] NVARCHAR(500) NOT NULL,
    [file_name] NVARCHAR(255) NOT NULL,
    [file_size_kb] INT NULL,
    [file_type] NVARCHAR(50) NULL,           -- e.g. 'pdf','docx','jpg'
    [expiry_date] DATE NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [uploaded_by] NVARCHAR(50) NOT NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant_document] PRIMARY KEY CLUSTERED ([document_id]),
    CONSTRAINT [FK_tenant_document_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_tenant_document_document_category] FOREIGN KEY ([document_category_id]) REFERENCES [master].[document_category]([document_category_id])
);
GO

-- 2.9 tenant.tenant_change_history
-- Tracks every change made to org profile, ABN, and registration details for regulatory audit.
CREATE TABLE [tenant].[tenant_change_history] (
    [history_id] BIGINT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [field_changed] NVARCHAR(100) NOT NULL,
    [old_value] NVARCHAR(MAX) NULL,
    [new_value] NVARCHAR(MAX) NULL,
    [changed_by] NVARCHAR(50) NOT NULL,
    [changed_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [change_reason] NVARCHAR(500) NULL,
    CONSTRAINT [PK_tenant_tenant_change_history] PRIMARY KEY CLUSTERED ([history_id]),
    CONSTRAINT [FK_tenant_change_history_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id])
);
GO

-- 2.10 tenant.branch
-- Branches and physical service delivery locations under each tenant organisation.
CREATE TABLE [tenant].[branch] (
    [branch_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [parent_branch_id] INT NULL,             -- Self-reference for hierarchical structure
    [branch_code] NVARCHAR(50) NOT NULL,     -- Branch natural key per tenant
    [branch_name] NVARCHAR(200) NOT NULL,
    [branch_type] NVARCHAR(50) NOT NULL,     -- 'Head Office','Branch Office','Sub-Branch','Service Location','Community Location','SIL Location'
    [street_address] NVARCHAR(255) NOT NULL,
    [suburb] NVARCHAR(100) NOT NULL,
    [state_id] INT NOT NULL,
    [postcode] NVARCHAR(10) NOT NULL,
    [country_id] INT NOT NULL,
    [phone] NVARCHAR(20) NULL,
    [email] NVARCHAR(255) NULL,
    [timezone] NVARCHAR(100) DEFAULT 'Australia/Sydney' NULL,
    [operating_hours_json] NVARCHAR(1000) NULL, -- JSON formatted hours
    [branch_status] NVARCHAR(30) DEFAULT 'Active' NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_branch] PRIMARY KEY CLUSTERED ([branch_id]),
    CONSTRAINT [FK_branch_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_branch_parent_branch] FOREIGN KEY ([parent_branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_branch_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_branch_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [UQ_branch_tenant_branch_code] UNIQUE ([tenant_id], [branch_code]),
    CONSTRAINT [CK_branch_branch_type] CHECK ([branch_type] IN ('Head Office','Branch Office','Sub-Branch','Service Location','Community Location','SIL Location')),
    CONSTRAINT [CK_branch_branch_status] CHECK ([branch_status] IN ('Active','Inactive','Temporarily Closed','Permanently Closed'))
);
GO

-- 2.11 tenant.program
-- Service programs / service lines offered by the provider, aligned with NDIS support categories.
CREATE TABLE [tenant].[program] (
    [program_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [program_code] NVARCHAR(50) NOT NULL,     -- Natural program code per tenant
    [program_name] NVARCHAR(200) NOT NULL,
    [service_type] NVARCHAR(100) NOT NULL,    -- e.g. 'In-Home Support','Community Access','SIL','Therapy','Support Coordination'
    [description] NVARCHAR(1000) NULL,
    [support_category_id] INT NULL,           -- Primary mapped NDIS support category
    [delivery_mode] NVARCHAR(50) NULL,        -- 'In-Person','Remote','Hybrid'
    [program_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_program] PRIMARY KEY CLUSTERED ([program_id]),
    CONSTRAINT [FK_program_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_program_ndis_support_category] FOREIGN KEY ([support_category_id]) REFERENCES [master].[ndis_support_category]([support_category_id]),
    CONSTRAINT [UQ_program_tenant_program_code] UNIQUE ([tenant_id], [program_code]),
    CONSTRAINT [CK_program_delivery_mode] CHECK ([delivery_mode] IS NULL OR [delivery_mode] IN ('In-Person','Remote','Hybrid')),
    CONSTRAINT [CK_program_program_status] CHECK ([program_status] IN ('Draft','Active','Inactive','Suspended','Archived'))
);
GO

-- 2.12 tenant.program_branch
-- Many-to-many relationship mapping which service programs are available at which branches.
CREATE TABLE [tenant].[program_branch] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [program_id] INT NOT NULL,
    [branch_id] INT NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    CONSTRAINT [PK_tenant_program_branch] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_program_branch_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_program_branch_program] FOREIGN KEY ([program_id]) REFERENCES [tenant].[program]([program_id]),
    CONSTRAINT [FK_program_branch_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [UQ_program_branch_program_branch] UNIQUE ([program_id], [branch_id])
);
GO

-- 2.13 tenant.role
-- System and tenant-defined RBAC roles. NULL tenant_id indicates a global system role.
CREATE TABLE [tenant].[role] (
    [role_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NULL,                     -- NULL for built-in platform system roles
    [role_code] NVARCHAR(50) NOT NULL,
    [role_name] NVARCHAR(100) NOT NULL,
    [description] NVARCHAR(500) NULL,
    [is_system_role] BIT DEFAULT 0 NOT NULL,  -- System roles cannot be deleted or renamed by tenants
    [is_active] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_role] PRIMARY KEY CLUSTERED ([role_id]),
    CONSTRAINT [FK_role_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [UQ_role_tenant_role_code] UNIQUE ([tenant_id], [role_code])
);
GO

-- 2.14 tenant.permission
-- Granular system permissions across all modules and sub-modules.
CREATE TABLE [tenant].[permission] (
    [permission_id] INT IDENTITY(1,1) NOT NULL,
    [module] NVARCHAR(100) NOT NULL,          -- e.g. 'PARTICIPANT','STAFF','BILLING','TENANT'
    [sub_module] NVARCHAR(100) NULL,          -- e.g. 'PLAN','CARE_NOTES','DOCUMENTS'
    [action] NVARCHAR(50) NOT NULL,           -- CRUD and workflow actions
    [permission_code] NVARCHAR(200) NOT NULL, -- e.g. 'PARTICIPANT.PLAN.VIEW'
    [description] NVARCHAR(500) NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    CONSTRAINT [PK_tenant_permission] PRIMARY KEY CLUSTERED ([permission_id]),
    CONSTRAINT [UQ_permission_permission_code] UNIQUE ([permission_code]),
    CONSTRAINT [CK_permission_action] CHECK ([action] IN ('VIEW','CREATE','EDIT','DELETE','APPROVE','REJECT','EXPORT','SUBMIT','IMPORT','PRINT'))
);
GO

-- 2.15 tenant.role_permission
-- Assigns granular permissions to roles.
CREATE TABLE [tenant].[role_permission] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [role_id] INT NOT NULL,
    [permission_id] INT NOT NULL,
    [is_granted] BIT DEFAULT 1 NOT NULL,
    [granted_by] NVARCHAR(50) NOT NULL,
    [granted_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    CONSTRAINT [PK_tenant_role_permission] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_role_permission_role] FOREIGN KEY ([role_id]) REFERENCES [tenant].[role]([role_id]),
    CONSTRAINT [FK_role_permission_permission] FOREIGN KEY ([permission_id]) REFERENCES [tenant].[permission]([permission_id]),
    CONSTRAINT [UQ_role_permission_role_permission] UNIQUE ([role_id], [permission_id])
);
GO

-- 2.16 tenant.app_user
-- Master user identity and authentication credentials across all tenants.
CREATE TABLE [tenant].[app_user] (
    [user_id] NVARCHAR(50) NOT NULL,          -- UUID string primary key
    [tenant_id] INT NOT NULL,
    [branch_id] INT NOT NULL,                 -- Primary home branch
    [email] NVARCHAR(255) NOT NULL,
    [password_hash] NVARCHAR(500) NOT NULL,   -- Argon2/bcrypt hash
    [first_name] NVARCHAR(100) NOT NULL,
    [last_name] NVARCHAR(100) NOT NULL,
    [phone] NVARCHAR(20) NULL,
    [mobile] NVARCHAR(20) NULL,
    [position_title] NVARCHAR(100) NULL,
    [user_type] NVARCHAR(50) NOT NULL,        -- Primary role designation
    [user_status] NVARCHAR(20) DEFAULT 'Pending' NOT NULL,
    [profile_photo_url] NVARCHAR(500) NULL,
    [last_login_at] DATETIMEOFFSET NULL,
    [failed_login_count] INT DEFAULT 0 NOT NULL,
    [locked_at] DATETIMEOFFSET NULL,
    [invite_token] NVARCHAR(500) NULL,
    [invite_expires_at] DATETIMEOFFSET NULL,
    [invite_accepted_at] DATETIMEOFFSET NULL,
    [password_reset_token] NVARCHAR(500) NULL,
    [password_reset_expires_at] DATETIMEOFFSET NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_app_user] PRIMARY KEY CLUSTERED ([user_id]),
    CONSTRAINT [FK_app_user_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_app_user_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [UQ_app_user_email] UNIQUE ([email]),
    CONSTRAINT [CK_app_user_type] CHECK ([user_type] IN ('System Admin','Admin','Support Coordinator','Finance Officer','Claims Officer','Team Leader','Support Worker','Compliance Team','Auditor','Viewer')),
    CONSTRAINT [CK_app_user_status] CHECK ([user_status] IN ('Pending','Active','Inactive','Suspended','Locked'))
);
GO

-- 2.17 tenant.user_role
-- Assigns one or more roles to an application user.
CREATE TABLE [tenant].[user_role] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [user_id] NVARCHAR(50) NOT NULL,
    [role_id] INT NOT NULL,
    [assigned_by] NVARCHAR(50) NOT NULL,
    [assigned_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [revoked_at] DATETIMEOFFSET NULL,
    [revoked_by] NVARCHAR(50) NULL,
    CONSTRAINT [PK_tenant_user_role] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_user_role_app_user] FOREIGN KEY ([user_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_user_role_role] FOREIGN KEY ([role_id]) REFERENCES [tenant].[role]([role_id]),
    CONSTRAINT [UQ_user_role_user_role] UNIQUE ([user_id], [role_id])
);
GO

-- 2.18 tenant.cross_branch_access
-- Temporary or emergency cross-branch participant and record access delegation.
CREATE TABLE [tenant].[cross_branch_access] (
    [access_id] NVARCHAR(50) NOT NULL,        -- UUID
    [tenant_id] INT NOT NULL,
    [user_id] NVARCHAR(50) NOT NULL,
    [home_branch_id] INT NOT NULL,
    [target_branch_id] INT NOT NULL,
    [access_type] NVARCHAR(30) NOT NULL,      -- 'Temporary','Emergency','Permanent'
    [reason] NVARCHAR(1000) NULL,
    [access_start] DATETIMEOFFSET NOT NULL,
    [access_end] DATETIMEOFFSET NULL,         -- NULL indicates permanent
    [approved_by] NVARCHAR(50) NULL,
    [approved_at] DATETIMEOFFSET NULL,
    [access_status] NVARCHAR(20) DEFAULT 'Pending' NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_cross_branch_access] PRIMARY KEY CLUSTERED ([access_id]),
    CONSTRAINT [FK_cross_branch_access_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_cross_branch_access_app_user] FOREIGN KEY ([user_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_cross_branch_access_home_branch] FOREIGN KEY ([home_branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_cross_branch_access_target_branch] FOREIGN KEY ([target_branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [CK_cross_branch_access_type] CHECK ([access_type] IN ('Temporary','Emergency','Permanent')),
    CONSTRAINT [CK_cross_branch_access_status] CHECK ([access_status] IN ('Pending','Approved','Rejected','Expired','Revoked'))
);
GO

-- 2.19 tenant.tenant_config
-- Key-value configuration settings per tenant (currency, formatting, API integrations).
CREATE TABLE [tenant].[tenant_config] (
    [config_id] INT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [config_group] NVARCHAR(50) NOT NULL,     -- 'General','Regional','Currency','Billing','Notification','Security','Integration'
    [config_key] NVARCHAR(100) NOT NULL,
    [config_value] NVARCHAR(2000) NULL,
    [is_encrypted] BIT DEFAULT 0 NOT NULL,    -- For API tokens, PRODA keystore secrets
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_tenant_tenant_config] PRIMARY KEY CLUSTERED ([config_id]),
    CONSTRAINT [FK_tenant_config_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [UQ_tenant_config_tenant_config_key] UNIQUE ([tenant_id], [config_key]),
    CONSTRAINT [CK_tenant_config_group] CHECK ([config_group] IN ('General','Regional','Currency','Billing','Notification','Security','Integration'))
);
GO

-- 2.20 tenant.audit_log
-- Immutable security and compliance audit trail. Never allows UPDATE or DELETE.
CREATE TABLE [tenant].[audit_log] (
    [log_id] BIGINT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [user_id] NVARCHAR(50) NULL,
    [session_id] NVARCHAR(100) NULL,
    [module] NVARCHAR(100) NOT NULL,
    [action] NVARCHAR(100) NOT NULL,
    [entity_type] NVARCHAR(100) NULL,         -- Affected table name
    [entity_id] NVARCHAR(100) NULL,           -- Affected record PK
    [old_value] NVARCHAR(MAX) NULL,           -- JSON snapshot before change
    [new_value] NVARCHAR(MAX) NULL,           -- JSON snapshot after change
    [change_summary] NVARCHAR(500) NULL,
    [ip_address] NVARCHAR(50) NULL,
    [user_agent] NVARCHAR(500) NULL,
    [performed_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    CONSTRAINT [PK_tenant_audit_log] PRIMARY KEY CLUSTERED ([log_id]),
    CONSTRAINT [FK_audit_log_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id])
);
GO

-- 2.21 tenant.rbac_change_log
-- Dedicated compliance log for RBAC role/permission assignments and revocations.
CREATE TABLE [tenant].[rbac_change_log] (
    [log_id] BIGINT IDENTITY(1,1) NOT NULL,
    [tenant_id] INT NOT NULL,
    [changed_by] NVARCHAR(50) NOT NULL,
    [change_type] NVARCHAR(50) NOT NULL,      -- 'ROLE_CREATED','ROLE_UPDATED','PERMISSION_GRANTED','PERMISSION_REVOKED','ROLE_ASSIGNED','ROLE_REVOKED','USER_ACTIVATED','USER_DEACTIVATED'
    [affected_user_id] NVARCHAR(50) NULL,
    [role_id] INT NULL,
    [permission_id] INT NULL,
    [old_value] NVARCHAR(MAX) NULL,
    [new_value] NVARCHAR(MAX) NULL,
    [changed_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    CONSTRAINT [PK_tenant_rbac_change_log] PRIMARY KEY CLUSTERED ([log_id]),
    CONSTRAINT [FK_rbac_change_log_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_rbac_change_log_role] FOREIGN KEY ([role_id]) REFERENCES [tenant].[role]([role_id]),
    CONSTRAINT [FK_rbac_change_log_permission] FOREIGN KEY ([permission_id]) REFERENCES [tenant].[permission]([permission_id]),
    CONSTRAINT [CK_rbac_change_log_change_type] CHECK ([change_type] IN ('ROLE_CREATED','ROLE_UPDATED','PERMISSION_GRANTED','PERMISSION_REVOKED','ROLE_ASSIGNED','ROLE_REVOKED','USER_ACTIVATED','USER_DEACTIVATED'))
);
GO

-- ============================================================================
-- MODULE 3: PARTICIPANT SCHEMA TABLES
-- All participant-related operational, plan, goal, and clinical support tables
-- ============================================================================

-- 3.1 participant.participant_profile
-- Core participant identity record. NDIS number is the natural primary key.
CREATE TABLE [participant].[participant_profile] (
    [ndis_no] NVARCHAR(50) NOT NULL,          -- Official NDIA Participant Number
    [tenant_id] INT NOT NULL,
    [branch_id] INT NOT NULL,                 -- Assigned service delivery branch
    [program_id] INT NULL,                    -- Primary service program
    [support_coordinator_id] NVARCHAR(50) NULL, -- Assigned Support Coordinator (app_user)
    [first_name] NVARCHAR(100) NOT NULL,
    [middle_name] NVARCHAR(100) NULL,
    [last_name] NVARCHAR(100) NOT NULL,
    [preferred_name] NVARCHAR(100) NULL,
    [disability_type_id] INT NULL,            -- Primary diagnosed disability
    [secondary_disability_type_id] INT NULL,  -- Secondary diagnosed disability
    [photo_url] NVARCHAR(500) NULL,
    [participant_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL,
    [onboarding_status] NVARCHAR(30) DEFAULT 'Profile Created' NOT NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_profile] PRIMARY KEY CLUSTERED ([ndis_no]),
    CONSTRAINT [FK_participant_profile_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_profile_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_participant_profile_program] FOREIGN KEY ([program_id]) REFERENCES [tenant].[program]([program_id]),
    CONSTRAINT [FK_participant_profile_support_coordinator] FOREIGN KEY ([support_coordinator_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_participant_profile_disability_type] FOREIGN KEY ([disability_type_id]) REFERENCES [master].[disability_type]([disability_type_id]),
    CONSTRAINT [FK_participant_profile_secondary_disability_type] FOREIGN KEY ([secondary_disability_type_id]) REFERENCES [master].[disability_type]([disability_type_id]),
    CONSTRAINT [CK_participant_profile_status] CHECK ([participant_status] IN ('Active','Inactive','On Hold','Exited','Deceased')),
    CONSTRAINT [CK_participant_profile_onboarding] CHECK ([onboarding_status] IN ('Profile Created','Personal Info Added','Plan Added','Documents Added','Complete'))
);
GO

-- 3.2 participant.participant_personal_info
-- Demographic and address information for the participant (permanent and residential).
CREATE TABLE [participant].[participant_personal_info] (
    [personal_id] NVARCHAR(50) NOT NULL,      -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [dob] DATE NOT NULL,
    [gender] NVARCHAR(30) NOT NULL,           -- 'Male','Female','Non-Binary','Transgender Male','Transgender Female','Prefer Not to Say','Other'
    [blood_group] NVARCHAR(10) NULL,
    [marital_status] NVARCHAR(30) NULL,
    [nationality] NVARCHAR(100) DEFAULT 'Australian' NOT NULL,
    [indigenous_status] NVARCHAR(50) NULL,    -- 'Aboriginal','Torres Strait Islander','Both','Neither','Prefer Not to Say'
    -- Permanent Address
    [perm_street] NVARCHAR(255) NOT NULL,
    [perm_suburb] NVARCHAR(100) NOT NULL,
    [perm_city] NVARCHAR(100) NOT NULL,
    [perm_state_id] INT NOT NULL,
    [perm_postcode] NVARCHAR(10) NOT NULL,
    [perm_country_id] INT NOT NULL,
    -- Residential Address (if different from permanent)
    [same_as_permanent] BIT DEFAULT 0 NOT NULL,
    [res_street] NVARCHAR(255) NULL,
    [res_suburb] NVARCHAR(100) NULL,
    [res_city] NVARCHAR(100) NULL,
    [res_state_id] INT NULL,
    [res_postcode] NVARCHAR(10) NULL,
    [res_country_id] INT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_personal_info] PRIMARY KEY CLUSTERED ([personal_id]),
    CONSTRAINT [FK_participant_personal_info_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_personal_info_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_personal_info_perm_state] FOREIGN KEY ([perm_state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_participant_personal_info_perm_country] FOREIGN KEY ([perm_country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [FK_participant_personal_info_res_state] FOREIGN KEY ([res_state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_participant_personal_info_res_country] FOREIGN KEY ([res_country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [UQ_participant_personal_info_ndis_no] UNIQUE ([ndis_no]),
    CONSTRAINT [CK_participant_personal_info_gender] CHECK ([gender] IN ('Male','Female','Non-Binary','Transgender Male','Transgender Female','Prefer Not to Say','Other')),
    CONSTRAINT [CK_participant_personal_info_blood_group] CHECK ([blood_group] IS NULL OR [blood_group] IN ('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown')),
    CONSTRAINT [CK_participant_personal_info_marital_status] CHECK ([marital_status] IS NULL OR [marital_status] IN ('Single','Married','De Facto','Widowed','Divorced','Separated')),
    CONSTRAINT [CK_participant_personal_info_indigenous] CHECK ([indigenous_status] IS NULL OR [indigenous_status] IN ('Aboriginal','Torres Strait Islander','Both','Neither','Prefer Not to Say'))
);
GO

-- 3.3 participant.participant_contact_info
-- Direct communication contact details for the participant.
CREATE TABLE [participant].[participant_contact_info] (
    [contact_id] NVARCHAR(50) NOT NULL,       -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [primary_email] NVARCHAR(255) NULL,
    [secondary_email] NVARCHAR(255) NULL,
    [country_id] INT NOT NULL,
    [primary_contact_no] NVARCHAR(20) NOT NULL,
    [secondary_contact_no] NVARCHAR(20) NULL,
    [preferred_contact_method] NVARCHAR(20) NULL, -- 'Email','Phone','SMS','Portal'
    [best_contact_time] NVARCHAR(100) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_contact_info] PRIMARY KEY CLUSTERED ([contact_id]),
    CONSTRAINT [FK_participant_contact_info_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_contact_info_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_contact_info_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [UQ_participant_contact_info_tenant_ndis_no] UNIQUE ([tenant_id], [ndis_no]),
    CONSTRAINT [CK_participant_contact_info_preferred_method] CHECK ([preferred_contact_method] IS NULL OR [preferred_contact_method] IN ('Email','Phone','SMS','Portal'))
);
GO

-- 3.4 participant.participant_emergency_contact
-- Emergency contacts and authorized decision-makers (guardians, advocates, next of kin).
CREATE TABLE [participant].[participant_emergency_contact] (
    [emergency_contact_id] NVARCHAR(50) NOT NULL, -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [first_name] NVARCHAR(100) NOT NULL,
    [middle_name] NVARCHAR(100) NULL,
    [last_name] NVARCHAR(100) NOT NULL,
    [relationship_type_id] INT NOT NULL,
    [gender] NVARCHAR(30) NULL,
    [primary_contact_no] NVARCHAR(20) NOT NULL,
    [secondary_contact_no] NVARCHAR(20) NULL,
    [primary_email] NVARCHAR(255) NOT NULL,
    [secondary_email] NVARCHAR(255) NULL,
    [street_address] NVARCHAR(255) NULL,
    [suburb] NVARCHAR(100) NULL,
    [state_id] INT NULL,
    [postcode] NVARCHAR(10) NULL,
    [country_id] INT NOT NULL,
    [is_primary] BIT DEFAULT 0 NOT NULL,
    [is_authorised_decision_maker] BIT DEFAULT 0 NOT NULL,
    [sort_order] INT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_emergency_contact] PRIMARY KEY CLUSTERED ([emergency_contact_id]),
    CONSTRAINT [FK_participant_emergency_contact_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_emergency_contact_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_emergency_contact_relationship_type] FOREIGN KEY ([relationship_type_id]) REFERENCES [master].[relationship_type]([relationship_type_id]),
    CONSTRAINT [FK_participant_emergency_contact_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_participant_emergency_contact_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id])
);
GO

-- 3.5 participant.participant_preferences
-- Cultural, dietary, language, worker gender, and clinical care preferences.
CREATE TABLE [participant].[participant_preferences] (
    [preference_id] NVARCHAR(50) NOT NULL,    -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [primary_language] NVARCHAR(100) DEFAULT 'English' NOT NULL,
    [secondary_language] NVARCHAR(100) NULL,
    [interpreter_required] BIT DEFAULT 0 NOT NULL,
    [interpreter_type] NVARCHAR(30) NULL,     -- 'In-Person','Phone','Video','None'
    [interpreter_gender_preference] NVARCHAR(20) NULL, -- 'Male','Female','No Preference'
    [worker_gender_preference] NVARCHAR(20) NULL,      -- 'Male','Female','No Preference'
    [smoking_preference] NVARCHAR(30) NULL,   -- 'No Smoking','Non-Smoker Worker','No Preference'
    [cultural_background] NVARCHAR(200) NULL,
    [religious_requirements] NVARCHAR(500) NULL,
    [dietary_requirements] NVARCHAR(500) NULL,
    [preferred_hospital] NVARCHAR(200) NULL,
    [mobility_aid] NVARCHAR(200) NULL,        -- 'Wheelchair','Walker','None'
    [communication_needs] NVARCHAR(500) NULL,
    [care_notes] NVARCHAR(2000) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_preferences] PRIMARY KEY CLUSTERED ([preference_id]),
    CONSTRAINT [FK_participant_preferences_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_preferences_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [UQ_participant_preferences_tenant_ndis_no] UNIQUE ([tenant_id], [ndis_no]),
    CONSTRAINT [CK_participant_preferences_interpreter_type] CHECK ([interpreter_type] IS NULL OR [interpreter_type] IN ('In-Person','Phone','Video','None')),
    CONSTRAINT [CK_participant_preferences_interpreter_gender] CHECK ([interpreter_gender_preference] IS NULL OR [interpreter_gender_preference] IN ('Male','Female','No Preference')),
    CONSTRAINT [CK_participant_preferences_worker_gender] CHECK ([worker_gender_preference] IS NULL OR [worker_gender_preference] IN ('Male','Female','No Preference')),
    CONSTRAINT [CK_participant_preferences_smoking] CHECK ([smoking_preference] IS NULL OR [smoking_preference] IN ('No Smoking','Non-Smoker Worker','No Preference'))
);
GO

-- 3.6 participant.participant_plan
-- Official NDIS funding plan header per participant. Supports plan versions over time.
CREATE TABLE [participant].[participant_plan] (
    [plan_id] NVARCHAR(50) NOT NULL,          -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [plan_number] NVARCHAR(100) NULL,         -- NDIA assigned plan identifier
    [plan_start_date] DATE NOT NULL,
    [plan_end_date] DATE NOT NULL,
    [funding_type] NVARCHAR(30) NOT NULL,     -- 'Agency Managed','Plan Managed','Self Managed','Combination'
    [plan_manager_name] NVARCHAR(200) NULL,   -- Required if Plan Managed
    [plan_manager_email] NVARCHAR(255) NULL,
    [plan_manager_phone] NVARCHAR(20) NULL,
    [plan_manager_abn] NVARCHAR(11) NULL,
    [total_budget_aud] DECIMAL(12,2) NOT NULL,
    [plan_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL,
    [is_current] BIT DEFAULT 1 NOT NULL,      -- Flag for active working plan
    [plan_review_date] DATE NULL,
    [notes] NVARCHAR(1000) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_plan] PRIMARY KEY CLUSTERED ([plan_id]),
    CONSTRAINT [FK_participant_plan_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_plan_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [CK_participant_plan_funding_type] CHECK ([funding_type] IN ('Agency Managed','Plan Managed','Self Managed','Combination')),
    CONSTRAINT [CK_participant_plan_status] CHECK ([plan_status] IN ('Draft','Active','Expiring','Expired','Replaced','Cancelled'))
);
GO

-- 3.7 participant.participant_plan_funding
-- Budget allocation per NDIS support category within a plan with auto-calculated remaining balance.
CREATE TABLE [participant].[participant_plan_funding] (
    [funding_id] NVARCHAR(50) NOT NULL,       -- UUID string
    [tenant_id] INT NOT NULL,
    [plan_id] NVARCHAR(50) NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [support_category_id] INT NOT NULL,
    [allocated_budget_aud] DECIMAL(12,2) NOT NULL,
    [utilised_amount_aud] DECIMAL(12,2) DEFAULT 0.00 NOT NULL,
    [remaining_balance_aud] AS ([allocated_budget_aud] - [utilised_amount_aud]) PERSISTED, -- Computed persisted balance
    [last_updated_at] DATETIMEOFFSET NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_plan_funding] PRIMARY KEY CLUSTERED ([funding_id]),
    CONSTRAINT [FK_participant_plan_funding_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_plan_funding_plan] FOREIGN KEY ([plan_id]) REFERENCES [participant].[participant_plan]([plan_id]),
    CONSTRAINT [FK_participant_plan_funding_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_plan_funding_support_category] FOREIGN KEY ([support_category_id]) REFERENCES [master].[ndis_support_category]([support_category_id]),
    CONSTRAINT [UQ_participant_plan_funding_plan_category] UNIQUE ([plan_id], [support_category_id])
);
GO

-- 3.8 participant.participant_plan_support_item
-- Specific NDIS line items authorized and contracted under each category allocation.
CREATE TABLE [participant].[participant_plan_support_item] (
    [support_item_mapping_id] NVARCHAR(50) NOT NULL, -- UUID string
    [tenant_id] INT NOT NULL,
    [funding_id] NVARCHAR(50) NOT NULL,
    [support_item_id] INT NOT NULL,
    [agreed_price] DECIMAL(10,4) NULL,         -- Negotiated unit price <= price guide cap
    [service_booking_no] NVARCHAR(100) NULL,   -- NDIA PACE / PRODA service booking number
    [booking_start_date] DATE NULL,
    [booking_end_date] DATE NULL,
    [booking_budget_aud] DECIMAL(12,2) NULL,
    [is_active] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_plan_support_item] PRIMARY KEY CLUSTERED ([support_item_mapping_id]),
    CONSTRAINT [FK_participant_plan_support_item_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_plan_support_item_funding] FOREIGN KEY ([funding_id]) REFERENCES [participant].[participant_plan_funding]([funding_id]),
    CONSTRAINT [FK_participant_plan_support_item_support_item] FOREIGN KEY ([support_item_id]) REFERENCES [master].[ndis_support_item]([support_item_id]),
    CONSTRAINT [UQ_participant_plan_support_item_funding_item] UNIQUE ([funding_id], [support_item_id])
);
GO

-- 3.9 participant.participant_document
-- Participant document repository (NDIS plans, Service Agreements, Clinical Assessments).
CREATE TABLE [participant].[participant_document] (
    [document_id] NVARCHAR(50) NOT NULL,      -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [document_category_id] INT NOT NULL,
    [document_name] NVARCHAR(255) NOT NULL,
    [description] NVARCHAR(500) NULL,
    [file_url] NVARCHAR(500) NOT NULL,
    [file_name] NVARCHAR(255) NOT NULL,
    [file_size_kb] INT NULL,
    [file_type] NVARCHAR(50) NULL,
    [expiry_date] DATE NULL,
    [access_level] NVARCHAR(30) DEFAULT 'Internal' NOT NULL, -- 'Internal','Restricted','Participant','All'
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [uploaded_by] NVARCHAR(50) NOT NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_document] PRIMARY KEY CLUSTERED ([document_id]),
    CONSTRAINT [FK_participant_document_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_document_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_document_document_category] FOREIGN KEY ([document_category_id]) REFERENCES [master].[document_category]([document_category_id]),
    CONSTRAINT [CK_participant_document_access_level] CHECK ([access_level] IN ('Internal','Restricted','Participant','All'))
);
GO

-- 3.10 participant.participant_goal
-- NDIS participant goals tied to funding categories and plan outcomes.
CREATE TABLE [participant].[participant_goal] (
    [goal_id] NVARCHAR(50) NOT NULL,          -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [plan_id] NVARCHAR(50) NULL,
    [support_category_id] INT NULL,
    [goal_category] NVARCHAR(100) NOT NULL,   -- e.g. 'Daily Living','Social','Employment','Health'
    [goal_title] NVARCHAR(300) NOT NULL,
    [goal_description] NVARCHAR(2000) NULL,
    [goal_status] NVARCHAR(30) DEFAULT 'Not Started' NOT NULL,
    [priority] NVARCHAR(10) NULL,             -- 'High','Medium','Low'
    [target_date] DATE NULL,
    [achieved_date] DATE NULL,
    [sort_order] INT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_goal] PRIMARY KEY CLUSTERED ([goal_id]),
    CONSTRAINT [FK_participant_goal_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_goal_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_goal_plan] FOREIGN KEY ([plan_id]) REFERENCES [participant].[participant_plan]([plan_id]),
    CONSTRAINT [FK_participant_goal_support_category] FOREIGN KEY ([support_category_id]) REFERENCES [master].[ndis_support_category]([support_category_id]),
    CONSTRAINT [CK_participant_goal_status] CHECK ([goal_status] IN ('Not Started','In Progress','Achieved','Partially Achieved','Discontinued','On Hold')),
    CONSTRAINT [CK_participant_goal_priority] CHECK ([priority] IS NULL OR [priority] IN ('High','Medium','Low'))
);
GO

-- 3.11 participant.participant_goal_review
-- Periodic evaluation reviews for participant goal attainment.
CREATE TABLE [participant].[participant_goal_review] (
    [review_id] NVARCHAR(50) NOT NULL,        -- UUID string
    [tenant_id] INT NOT NULL,
    [goal_id] NVARCHAR(50) NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [review_date] DATE NOT NULL,
    [progress_rating] NVARCHAR(30) NULL,      -- 'Excellent','Good','Satisfactory','Needs Improvement','Not Making Progress'
    [goal_status_at_review] NVARCHAR(30) NULL,
    [review_notes] NVARCHAR(2000) NULL,
    [next_review_date] DATE NULL,
    [reviewed_by] NVARCHAR(50) NOT NULL,      -- FK to tenant.app_user
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_goal_review] PRIMARY KEY CLUSTERED ([review_id]),
    CONSTRAINT [FK_participant_goal_review_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_goal_review_goal] FOREIGN KEY ([goal_id]) REFERENCES [participant].[participant_goal]([goal_id]),
    CONSTRAINT [FK_participant_goal_review_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_goal_review_reviewed_by] FOREIGN KEY ([reviewed_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_participant_goal_review_rating] CHECK ([progress_rating] IS NULL OR [progress_rating] IN ('Excellent','Good','Satisfactory','Needs Improvement','Not Making Progress'))
);
GO

-- 3.12 participant.participant_care_note
-- Session and progress notes recorded by support workers, coordinators, and allied health staff.
CREATE TABLE [participant].[participant_care_note] (
    [care_note_id] NVARCHAR(50) NOT NULL,     -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [note_type] NVARCHAR(50) NOT NULL,        -- 'Session Note','Progress Note','Incident Note','General Note','Handover Note','Medical Note'
    [note_date] DATE NOT NULL,
    [note_start_time] TIME NULL,
    [note_end_time] TIME NULL,
    [note_content] NVARCHAR(MAX) NOT NULL,
    [related_goal_id] NVARCHAR(50) NULL,
    [related_support_item_id] INT NULL,
    [support_worker_id] NVARCHAR(50) NULL,    -- Worker who performed support
    [attachment_url] NVARCHAR(500) NULL,
    [note_status] NVARCHAR(20) DEFAULT 'Draft' NOT NULL, -- 'Draft','Submitted','Approved','Rejected'
    [rejection_reason] NVARCHAR(500) NULL,
    [submitted_at] DATETIMEOFFSET NULL,
    [submitted_by] NVARCHAR(50) NULL,
    [approved_by] NVARCHAR(50) NULL,
    [approved_at] DATETIMEOFFSET NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_care_note] PRIMARY KEY CLUSTERED ([care_note_id]),
    CONSTRAINT [FK_participant_care_note_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_care_note_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_care_note_goal] FOREIGN KEY ([related_goal_id]) REFERENCES [participant].[participant_goal]([goal_id]),
    CONSTRAINT [FK_participant_care_note_support_item] FOREIGN KEY ([related_support_item_id]) REFERENCES [master].[ndis_support_item]([support_item_id]),
    CONSTRAINT [FK_participant_care_note_support_worker] FOREIGN KEY ([support_worker_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_participant_care_note_submitted_by] FOREIGN KEY ([submitted_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_participant_care_note_approved_by] FOREIGN KEY ([approved_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_participant_care_note_type] CHECK ([note_type] IN ('Session Note','Progress Note','Incident Note','General Note','Handover Note','Medical Note')),
    CONSTRAINT [CK_participant_care_note_status] CHECK ([note_status] IN ('Draft','Submitted','Approved','Rejected'))
);
GO

-- 3.13 participant.participant_interaction
-- CRM log of calls, meetings, portal messages, and home visits with or regarding the participant.
CREATE TABLE [participant].[participant_interaction] (
    [interaction_id] NVARCHAR(50) NOT NULL,   -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [interaction_type] NVARCHAR(50) NOT NULL, -- 'Phone Call','Email','In-Person Meeting','Home Visit','Video Call','Portal Message','Other'
    [interaction_date] DATE NOT NULL,
    [interaction_time] TIME NULL,
    [duration_minutes] INT NULL,
    [summary] NVARCHAR(2000) NOT NULL,
    [outcome] NVARCHAR(1000) NULL,
    [follow_up_required] BIT DEFAULT 0 NOT NULL,
    [follow_up_due_date] DATE NULL,
    [follow_up_notes] NVARCHAR(500) NULL,
    [attachment_url] NVARCHAR(500) NULL,
    [interacted_by] NVARCHAR(50) NOT NULL,    -- Staff user who logged interaction
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_interaction] PRIMARY KEY CLUSTERED ([interaction_id]),
    CONSTRAINT [FK_participant_interaction_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_interaction_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_interaction_interacted_by] FOREIGN KEY ([interacted_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_participant_interaction_type] CHECK ([interaction_type] IN ('Phone Call','Email','In-Person Meeting','Home Visit','Video Call','Portal Message','Other'))
);
GO

-- 3.14 participant.participant_risk_flag
-- Safety alerts, behaviour support plans, falls risk, and critical safeguards.
CREATE TABLE [participant].[participant_risk_flag] (
    [risk_flag_id] NVARCHAR(50) NOT NULL,     -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [risk_category_id] INT NOT NULL,
    [risk_title] NVARCHAR(300) NOT NULL,
    [risk_description] NVARCHAR(2000) NULL,
    [severity] NVARCHAR(20) NOT NULL,         -- 'Low','Medium','High','Critical'
    [risk_status] NVARCHAR(20) DEFAULT 'Open' NOT NULL, -- 'Open','Under Review','Resolved','Closed','Escalated'
    [identified_date] DATE NOT NULL,
    [identified_by] NVARCHAR(50) NOT NULL,
    [reviewed_date] DATE NULL,
    [reviewed_by] NVARCHAR(50) NULL,
    [resolved_date] DATE NULL,
    [resolved_by] NVARCHAR(50) NULL,
    [resolution_notes] NVARCHAR(1000) NULL,
    [next_review_date] DATE NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_risk_flag] PRIMARY KEY CLUSTERED ([risk_flag_id]),
    CONSTRAINT [FK_participant_risk_flag_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_risk_flag_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_participant_risk_flag_risk_category] FOREIGN KEY ([risk_category_id]) REFERENCES [master].[risk_category]([risk_category_id]),
    CONSTRAINT [FK_participant_risk_flag_identified_by] FOREIGN KEY ([identified_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_participant_risk_flag_reviewed_by] FOREIGN KEY ([reviewed_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_participant_risk_flag_resolved_by] FOREIGN KEY ([resolved_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_participant_risk_flag_severity] CHECK ([severity] IN ('Low','Medium','High','Critical')),
    CONSTRAINT [CK_participant_risk_flag_status] CHECK ([risk_status] IN ('Open','Under Review','Resolved','Closed','Escalated'))
);
GO

-- 3.15 participant.participant_alert
-- System-generated operational alerts (plan expiring, budget run-out rate, missing consents).
CREATE TABLE [participant].[participant_alert] (
    [alert_id] NVARCHAR(50) NOT NULL,         -- UUID string
    [tenant_id] INT NOT NULL,
    [ndis_no] NVARCHAR(50) NOT NULL,
    [alert_type] NVARCHAR(100) NOT NULL,      -- 'Plan Expiring','Budget Low','Budget Exhausted','Document Expiring','Goal Overdue','Risk Flag Open','Compliance Issue','Other'
    [alert_title] NVARCHAR(300) NOT NULL,
    [alert_message] NVARCHAR(1000) NULL,
    [severity] NVARCHAR(20) NOT NULL,         -- 'Info','Warning','Critical'
    [is_read] BIT DEFAULT 0 NOT NULL,
    [is_dismissed] BIT DEFAULT 0 NOT NULL,
    [due_date] DATE NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [dismissed_at] DATETIMEOFFSET NULL,
    [dismissed_by] NVARCHAR(50) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_participant_participant_alert] PRIMARY KEY CLUSTERED ([alert_id]),
    CONSTRAINT [FK_participant_alert_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_participant_alert_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [CK_participant_alert_type] CHECK ([alert_type] IN ('Plan Expiring','Budget Low','Budget Exhausted','Document Expiring','Goal Overdue','Risk Flag Open','Compliance Issue','Other')),
    CONSTRAINT [CK_participant_alert_severity] CHECK ([severity] IN ('Info','Warning','Critical'))
);
GO

-- ============================================================================
-- MODULE 4: STAFF SCHEMA TABLES
-- Staff identity, qualifications, WWCC compliance, rostering, and timesheets
-- ============================================================================

-- 4.1 staff.staff_profile
-- Core staff member record. Connects HR data to tenant.app_user identity.
CREATE TABLE [staff].[staff_profile] (
    [staff_id] NVARCHAR(50) NOT NULL,         -- UUID or STF-XXXX identifier
    [tenant_id] INT NOT NULL,
    [branch_id] INT NOT NULL,                 -- Primary home branch
    [user_id] NVARCHAR(50) NULL,              -- System login account if staff has system access
    [employee_code] NVARCHAR(50) NOT NULL,    -- Unique internal payroll / employee code per tenant
    [first_name] NVARCHAR(100) NOT NULL,
    [middle_name] NVARCHAR(100) NULL,
    [last_name] NVARCHAR(100) NOT NULL,
    [preferred_name] NVARCHAR(100) NULL,
    [dob] DATE NULL,
    [gender] NVARCHAR(30) NULL,
    [photo_url] NVARCHAR(500) NULL,
    -- Employment Details
    [employment_type] NVARCHAR(30) NOT NULL,  -- 'Full-Time','Part-Time','Casual','Contractor','Volunteer'
    [position_title] NVARCHAR(200) NOT NULL,
    [department] NVARCHAR(100) NULL,
    [start_date] DATE NOT NULL,
    [end_date] DATE NULL,
    [probation_end_date] DATE NULL,
    [reporting_manager_id] NVARCHAR(50) NULL, -- Self-reference to staff.staff_profile
    [award_classification] NVARCHAR(100) NULL, -- SCHADS Award Level e.g. 'Level 2.1', 'Level 3.2'
    [pay_rate_type] NVARCHAR(30) NULL,        -- 'Hourly','Salary','Casual'
    [staff_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL, -- 'Active','Inactive','On Leave','Terminated','Suspended','Pending Onboarding'
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_profile] PRIMARY KEY CLUSTERED ([staff_id]),
    CONSTRAINT [FK_staff_profile_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_profile_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_staff_profile_app_user] FOREIGN KEY ([user_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [FK_staff_profile_reporting_manager] FOREIGN KEY ([reporting_manager_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [UQ_staff_profile_tenant_employee_code] UNIQUE ([tenant_id], [employee_code]),
    CONSTRAINT [CK_staff_profile_employment_type] CHECK ([employment_type] IN ('Full-Time','Part-Time','Casual','Contractor','Volunteer')),
    CONSTRAINT [CK_staff_profile_pay_rate_type] CHECK ([pay_rate_type] IS NULL OR [pay_rate_type] IN ('Hourly','Salary','Casual')),
    CONSTRAINT [CK_staff_profile_status] CHECK ([staff_status] IN ('Active','Inactive','On Leave','Terminated','Suspended','Pending Onboarding'))
);
GO

-- 4.2 staff.staff_contact
-- Contact information, residential address, and emergency contact for staff.
CREATE TABLE [staff].[staff_contact] (
    [contact_id] NVARCHAR(50) NOT NULL,       -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [primary_email] NVARCHAR(255) NOT NULL,
    [secondary_email] NVARCHAR(255) NULL,
    [primary_phone] NVARCHAR(20) NOT NULL,
    [secondary_phone] NVARCHAR(20) NULL,
    [street_address] NVARCHAR(255) NULL,
    [suburb] NVARCHAR(100) NULL,
    [state_id] INT NULL,
    [postcode] NVARCHAR(10) NULL,
    [country_id] INT NULL,
    -- Emergency Contact
    [emergency_contact_name] NVARCHAR(200) NULL,
    [emergency_contact_phone] NVARCHAR(20) NULL,
    [emergency_contact_relationship] NVARCHAR(50) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_contact] PRIMARY KEY CLUSTERED ([contact_id]),
    CONSTRAINT [FK_staff_contact_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_contact_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_contact_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_staff_contact_country] FOREIGN KEY ([country_id]) REFERENCES [master].[country]([country_id]),
    CONSTRAINT [UQ_staff_contact_staff_id] UNIQUE ([staff_id])
);
GO

-- 4.3 staff.staff_identification
-- Government identification records for identity verification and right-to-work audits.
CREATE TABLE [staff].[staff_identification] (
    [identification_id] NVARCHAR(50) NOT NULL, -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [id_type] NVARCHAR(50) NOT NULL,          -- 'Passport','Driver Licence','Medicare Card','Birth Certificate','Visa','Other'
    [id_number] NVARCHAR(100) NOT NULL,
    [issuing_authority] NVARCHAR(200) NULL,
    [issue_date] DATE NULL,
    [expiry_date] DATE NULL,
    [is_verified] BIT DEFAULT 0 NOT NULL,
    [verified_by] NVARCHAR(50) NULL,
    [verified_at] DATETIMEOFFSET NULL,
    [document_url] NVARCHAR(500) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_identification] PRIMARY KEY CLUSTERED ([identification_id]),
    CONSTRAINT [FK_staff_identification_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_identification_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_identification_verified_by] FOREIGN KEY ([verified_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_staff_identification_type] CHECK ([id_type] IN ('Passport','Driver Licence','Medicare Card','Birth Certificate','Visa','Other'))
);
GO

-- 4.4 staff.staff_qualification
-- Formal educational qualifications, trade degrees, and tertiary certifications.
CREATE TABLE [staff].[staff_qualification] (
    [qualification_id] NVARCHAR(50) NOT NULL, -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [qualification_type_id] INT NOT NULL,
    [institution_name] NVARCHAR(300) NULL,
    [qualification_name] NVARCHAR(300) NOT NULL,
    [field_of_study] NVARCHAR(200) NULL,
    [obtained_date] DATE NULL,
    [expiry_date] DATE NULL,
    [document_url] NVARCHAR(500) NULL,
    [qualification_status] NVARCHAR(20) DEFAULT 'Active' NOT NULL, -- 'Active','Expired','Pending Verification','Verified','Revoked'
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_qualification] PRIMARY KEY CLUSTERED ([qualification_id]),
    CONSTRAINT [FK_staff_qualification_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_qualification_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_qualification_qualification_type] FOREIGN KEY ([qualification_type_id]) REFERENCES [master].[qualification_type]([qualification_type_id]),
    CONSTRAINT [CK_staff_qualification_status] CHECK ([qualification_status] IN ('Active','Expired','Pending Verification','Verified','Revoked'))
);
GO

-- 4.5 staff.staff_compliance
-- Mandatory compliance clearances (WWCC, Police Check, First Aid, NDIS Worker Screening Check).
CREATE TABLE [staff].[staff_compliance] (
    [compliance_id] NVARCHAR(50) NOT NULL,    -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [compliance_type_id] INT NOT NULL,
    [state_id] INT NULL,                      -- Jurisdiction for state-specific checks (WWCC)
    [compliance_number] NVARCHAR(100) NULL,   -- Card/registration reference number
    [issue_date] DATE NULL,
    [expiry_date] DATE NULL,
    [issuing_authority] NVARCHAR(200) NULL,
    [document_url] NVARCHAR(500) NULL,
    [compliance_status] NVARCHAR(30) DEFAULT 'Compliant' NOT NULL, -- 'Compliant','Non-Compliant','Expiring Soon','Expired','Pending','Not Required','Exempt'
    [verified_by] NVARCHAR(50) NULL,
    [verified_at] DATETIMEOFFSET NULL,
    [notes] NVARCHAR(500) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_compliance] PRIMARY KEY CLUSTERED ([compliance_id]),
    CONSTRAINT [FK_staff_compliance_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_compliance_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_compliance_compliance_type] FOREIGN KEY ([compliance_type_id]) REFERENCES [master].[compliance_type]([compliance_type_id]),
    CONSTRAINT [FK_staff_compliance_state] FOREIGN KEY ([state_id]) REFERENCES [master].[state]([state_id]),
    CONSTRAINT [FK_staff_compliance_verified_by] FOREIGN KEY ([verified_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [UQ_staff_compliance_staff_type_state] UNIQUE ([staff_id], [compliance_type_id], [state_id]),
    CONSTRAINT [CK_staff_compliance_status] CHECK ([compliance_status] IN ('Compliant','Non-Compliant','Expiring Soon','Expired','Pending','Not Required','Exempt'))
);
GO

-- 4.6 staff.staff_program
-- Maps which service programs a staff member is certified and authorized to deliver.
CREATE TABLE [staff].[staff_program] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [staff_id] NVARCHAR(50) NOT NULL,
    [program_id] INT NOT NULL,
    [tenant_id] INT NOT NULL,
    [is_primary] BIT DEFAULT 0 NOT NULL,
    [assigned_by] NVARCHAR(50) NOT NULL,
    [assigned_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    CONSTRAINT [PK_staff_staff_program] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_staff_program_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_program_program] FOREIGN KEY ([program_id]) REFERENCES [tenant].[program]([program_id]),
    CONSTRAINT [FK_staff_program_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [UQ_staff_program_staff_program] UNIQUE ([staff_id], [program_id])
);
GO

-- 4.7 staff.staff_branch_assignment
-- Branch allocations for staff who work across multiple operational locations.
CREATE TABLE [staff].[staff_branch_assignment] (
    [id] INT IDENTITY(1,1) NOT NULL,
    [staff_id] NVARCHAR(50) NOT NULL,
    [branch_id] INT NOT NULL,
    [tenant_id] INT NOT NULL,
    [is_primary] BIT DEFAULT 0 NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    CONSTRAINT [PK_staff_staff_branch_assignment] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_staff_branch_assignment_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_branch_assignment_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_staff_branch_assignment_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [UQ_staff_branch_assignment_staff_branch] UNIQUE ([staff_id], [branch_id])
);
GO

-- 4.8 staff.staff_availability
-- Regular weekly recurring availability schedule for staff rostering.
CREATE TABLE [staff].[staff_availability] (
    [availability_id] NVARCHAR(50) NOT NULL,  -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [day_of_week] TINYINT NOT NULL,           -- 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
    [start_time] TIME NOT NULL,
    [end_time] TIME NOT NULL,
    [is_available] BIT DEFAULT 1 NOT NULL,
    [effective_from] DATE NOT NULL,
    [effective_to] DATE NULL,
    [notes] NVARCHAR(200) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_availability] PRIMARY KEY CLUSTERED ([availability_id]),
    CONSTRAINT [FK_staff_availability_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_availability_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [CK_staff_availability_day] CHECK ([day_of_week] BETWEEN 0 AND 6)
);
GO

-- 4.9 staff.timesheet
-- Pay period timesheet header record per staff member.
CREATE TABLE [staff].[timesheet] (
    [timesheet_id] NVARCHAR(50) NOT NULL,     -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [branch_id] INT NOT NULL,
    [period_start] DATE NOT NULL,
    [period_end] DATE NOT NULL,
    [total_hours] DECIMAL(6,2) NULL,          -- Aggregated sum of billable/payable shift hours
    [total_overtime_hours] DECIMAL(6,2) NULL,
    [timesheet_status] NVARCHAR(20) DEFAULT 'Draft' NOT NULL, -- 'Draft','Submitted','Under Review','Approved','Rejected','Paid'
    [submitted_at] DATETIMEOFFSET NULL,
    [submitted_by] NVARCHAR(50) NULL,
    [approved_by] NVARCHAR(50) NULL,
    [approved_at] DATETIMEOFFSET NULL,
    [rejection_reason] NVARCHAR(500) NULL,
    [notes] NVARCHAR(500) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_timesheet] PRIMARY KEY CLUSTERED ([timesheet_id]),
    CONSTRAINT [FK_timesheet_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_timesheet_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_timesheet_branch] FOREIGN KEY ([branch_id]) REFERENCES [tenant].[branch]([branch_id]),
    CONSTRAINT [FK_timesheet_approved_by] FOREIGN KEY ([approved_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [UQ_timesheet_tenant_staff_period] UNIQUE ([tenant_id], [staff_id], [period_start]),
    CONSTRAINT [CK_staff_timesheet_status] CHECK ([timesheet_status] IN ('Draft','Submitted','Under Review','Approved','Rejected','Paid'))
);
GO

-- 4.10 staff.timesheet_entry
-- Individual timesheet line items / shift records tied to participant supports and NDIS line items.
CREATE TABLE [staff].[timesheet_entry] (
    [entry_id] NVARCHAR(50) NOT NULL,         -- UUID string
    [timesheet_id] NVARCHAR(50) NOT NULL,
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [work_date] DATE NOT NULL,
    [shift_type] NVARCHAR(50) NULL,           -- 'Standard','Evening','Saturday','Sunday','Public Holiday','Sleepover','Active Night'
    [start_time] TIME NOT NULL,
    [end_time] TIME NOT NULL,
    [break_minutes] INT DEFAULT 0 NOT NULL,
    [ndis_no] NVARCHAR(50) NULL,              -- Target participant profile
    [support_item_id] INT NULL,               -- NDIS support item catalog item
    [activity_type] NVARCHAR(100) NULL,
    [location_type] NVARCHAR(50) NULL,        -- 'In-Home','Community','Office','Other'
    [notes] NVARCHAR(1000) NULL,
    [km_travelled] DECIMAL(8,2) NULL,         -- Travel distance claim under NDIS travel guidelines
    [is_billable] BIT DEFAULT 1 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_timesheet_entry] PRIMARY KEY CLUSTERED ([entry_id]),
    CONSTRAINT [FK_timesheet_entry_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_timesheet_entry_timesheet] FOREIGN KEY ([timesheet_id]) REFERENCES [staff].[timesheet]([timesheet_id]),
    CONSTRAINT [FK_timesheet_entry_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_timesheet_entry_participant_profile] FOREIGN KEY ([ndis_no]) REFERENCES [participant].[participant_profile]([ndis_no]),
    CONSTRAINT [FK_timesheet_entry_support_item] FOREIGN KEY ([support_item_id]) REFERENCES [master].[ndis_support_item]([support_item_id]),
    CONSTRAINT [CK_staff_timesheet_entry_shift_type] CHECK ([shift_type] IS NULL OR [shift_type] IN ('Standard','Evening','Saturday','Sunday','Public Holiday','Sleepover','Active Night')),
    CONSTRAINT [CK_staff_timesheet_entry_location_type] CHECK ([location_type] IS NULL OR [location_type] IN ('In-Home','Community','Office','Other'))
);
GO

-- 4.11 staff.leave_request
-- Staff leave submissions and manager approvals with roster conflict checking.
CREATE TABLE [staff].[leave_request] (
    [leave_id] NVARCHAR(50) NOT NULL,         -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [leave_type_id] INT NOT NULL,
    [start_date] DATE NOT NULL,
    [end_date] DATE NOT NULL,
    [total_days] DECIMAL(5,2) NULL,
    [is_half_day] BIT DEFAULT 0 NOT NULL,
    [half_day_session] NVARCHAR(10) NULL,     -- 'AM' or 'PM'
    [reason] NVARCHAR(1000) NULL,
    [supporting_doc_url] NVARCHAR(500) NULL,
    [leave_status] NVARCHAR(20) DEFAULT 'Pending' NOT NULL, -- 'Pending','Approved','Rejected','Cancelled','Withdrawn'
    [approved_by] NVARCHAR(50) NULL,
    [approved_at] DATETIMEOFFSET NULL,
    [rejection_reason] NVARCHAR(500) NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) DEFAULT 'SYSTEM' NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_leave_request] PRIMARY KEY CLUSTERED ([leave_id]),
    CONSTRAINT [FK_leave_request_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_leave_request_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_leave_request_leave_type] FOREIGN KEY ([leave_type_id]) REFERENCES [master].[leave_type]([leave_type_id]),
    CONSTRAINT [FK_leave_request_approved_by] FOREIGN KEY ([approved_by]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_staff_leave_request_half_day] CHECK ([half_day_session] IS NULL OR [half_day_session] IN ('AM','PM')),
    CONSTRAINT [CK_staff_leave_request_status] CHECK ([leave_status] IN ('Pending','Approved','Rejected','Cancelled','Withdrawn'))
);
GO

-- 4.12 staff.staff_document
-- Staff document repository (employment contracts, payslips, training certificates).
CREATE TABLE [staff].[staff_document] (
    [document_id] NVARCHAR(50) NOT NULL,      -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [document_category_id] INT NOT NULL,
    [document_name] NVARCHAR(255) NOT NULL,
    [description] NVARCHAR(500) NULL,
    [file_url] NVARCHAR(500) NOT NULL,
    [file_name] NVARCHAR(255) NOT NULL,
    [file_size_kb] INT NULL,
    [file_type] NVARCHAR(50) NULL,
    [expiry_date] DATE NULL,
    [is_confidential] BIT DEFAULT 0 NOT NULL,
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [uploaded_by] NVARCHAR(50) NOT NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_document] PRIMARY KEY CLUSTERED ([document_id]),
    CONSTRAINT [FK_staff_document_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_document_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_document_document_category] FOREIGN KEY ([document_category_id]) REFERENCES [master].[document_category]([document_category_id])
);
GO

-- 4.13 staff.staff_performance_review
-- Formal staff performance appraisals, goal achievements, and SCHADS classification reviews.
CREATE TABLE [staff].[staff_performance_review] (
    [review_id] NVARCHAR(50) NOT NULL,        -- UUID string
    [staff_id] NVARCHAR(50) NOT NULL,
    [tenant_id] INT NOT NULL,
    [review_period_start] DATE NOT NULL,
    [review_period_end] DATE NOT NULL,
    [review_date] DATE NOT NULL,
    [overall_rating] NVARCHAR(30) NULL,       -- 'Exceptional','Exceeds Expectations','Meets Expectations','Below Expectations','Unsatisfactory'
    [reviewer_id] NVARCHAR(50) NOT NULL,      -- Evaluator (tenant.app_user)
    [review_notes] NVARCHAR(MAX) NULL,
    [goals_next_period] NVARCHAR(2000) NULL,
    [staff_acknowledgement] BIT DEFAULT 0 NOT NULL,
    [acknowledged_at] DATETIMEOFFSET NULL,
    [review_status] NVARCHAR(20) DEFAULT 'Draft' NOT NULL, -- 'Draft','In Progress','Completed','Acknowledged'
    [is_deleted] BIT DEFAULT 0 NOT NULL,
    [deleted_at] DATETIMEOFFSET NULL,
    [created_by] NVARCHAR(50) NOT NULL,
    [created_at] DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET() NOT NULL,
    [updated_by] NVARCHAR(50) NULL,
    [updated_at] DATETIMEOFFSET NULL,
    CONSTRAINT [PK_staff_staff_performance_review] PRIMARY KEY CLUSTERED ([review_id]),
    CONSTRAINT [FK_staff_performance_review_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenant].[tenant]([tenant_id]),
    CONSTRAINT [FK_staff_performance_review_staff_profile] FOREIGN KEY ([staff_id]) REFERENCES [staff].[staff_profile]([staff_id]),
    CONSTRAINT [FK_staff_performance_review_reviewer] FOREIGN KEY ([reviewer_id]) REFERENCES [tenant].[app_user]([user_id]),
    CONSTRAINT [CK_staff_performance_review_rating] CHECK ([overall_rating] IS NULL OR [overall_rating] IN ('Exceptional','Exceeds Expectations','Meets Expectations','Below Expectations','Unsatisfactory')),
    CONSTRAINT [CK_staff_performance_review_status] CHECK ([review_status] IN ('Draft','In Progress','Completed','Acknowledged'))
);
GO

-- ============================================================================
-- INDEX DEFINITIONS
-- Grouped by Schema: master -> tenant -> participant -> staff
-- Enforcing tenant isolation (CU_ prefix) & high-performance query execution
-- ============================================================================

-- ----------------------------------------------------------------------------
-- MASTER SCHEMA INDEXES
-- ----------------------------------------------------------------------------
CREATE NONCLUSTERED INDEX [IX_master_state_country] 
    ON [master].[state] ([country_id]);
GO

CREATE NONCLUSTERED INDEX [IX_master_ndis_support_category_active] 
    ON [master].[ndis_support_category] ([is_active], [category_number]);
GO

CREATE NONCLUSTERED INDEX [IX_master_ndis_support_item_category_active] 
    ON [master].[ndis_support_item] ([support_category_id], [is_active]);
GO

CREATE NONCLUSTERED INDEX [IX_master_document_category_module] 
    ON [master].[document_category] ([module], [is_active]);
GO

CREATE NONCLUSTERED INDEX [IX_master_compliance_type_mandatory] 
    ON [master].[compliance_type] ([is_mandatory], [is_active]);
GO

-- ----------------------------------------------------------------------------
-- TENANT SCHEMA INDEXES
-- ----------------------------------------------------------------------------
-- Filtered unique index for nullable NDIS registration number on tenant
CREATE UNIQUE NONCLUSTERED INDEX [UQ_tenant_ndis_registration_no] 
    ON [tenant].[tenant] ([ndis_registration_no]) 
    WHERE [ndis_registration_no] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_tenant_tenant_status_active_deleted] 
    ON [tenant].[tenant] ([tenant_status], [is_active], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_tenant_plan_id] 
    ON [tenant].[tenant] ([plan_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_subscription_tenant_status] 
    ON [tenant].[tenant_subscription] ([tenant_id], [subscription_status]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_subscription_plan_id] 
    ON [tenant].[tenant_subscription] ([plan_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_contact_tenant_id] 
    ON [tenant].[tenant_contact] ([tenant_id], [is_primary]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_address_tenant_type] 
    ON [tenant].[tenant_address] ([tenant_id], [address_type]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_address_state_id] 
    ON [tenant].[tenant_address] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_address_country_id] 
    ON [tenant].[tenant_address] ([country_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_service_state_state_id] 
    ON [tenant].[tenant_service_state] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_registration_group_reg_group_id] 
    ON [tenant].[tenant_registration_group] ([reg_group_id]);
GO

-- Composite tenant isolation index for tenant_document
CREATE NONCLUSTERED INDEX [CU_tenant_document] 
    ON [tenant].[tenant_document] ([tenant_id], [document_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_document_tenant_category] 
    ON [tenant].[tenant_document] ([tenant_id], [document_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_document_expiry] 
    ON [tenant].[tenant_document] ([tenant_id], [expiry_date]) 
    WHERE [expiry_date] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_tenant_change_history_tenant_changed_at] 
    ON [tenant].[tenant_change_history] ([tenant_id], [changed_at] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_branch_tenant_status_deleted] 
    ON [tenant].[branch] ([tenant_id], [branch_status], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_branch_tenant_parent_branch] 
    ON [tenant].[branch] ([tenant_id], [parent_branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_branch_state_id] 
    ON [tenant].[branch] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_branch_country_id] 
    ON [tenant].[branch] ([country_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_program_tenant_status_deleted] 
    ON [tenant].[program] ([tenant_id], [program_status], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_program_support_category_id] 
    ON [tenant].[program] ([support_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_program_branch_tenant_branch] 
    ON [tenant].[program_branch] ([tenant_id], [branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_program_branch_program] 
    ON [tenant].[program_branch] ([program_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_role_tenant_active] 
    ON [tenant].[role] ([tenant_id], [is_active]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_role_permission_role_id] 
    ON [tenant].[role_permission] ([role_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_role_permission_permission_id] 
    ON [tenant].[role_permission] ([permission_id]);
GO

-- Composite tenant isolation index for app_user
CREATE NONCLUSTERED INDEX [CU_app_user] 
    ON [tenant].[app_user] ([tenant_id], [user_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_app_user_tenant_status_deleted] 
    ON [tenant].[app_user] ([tenant_id], [user_status], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_app_user_branch_id] 
    ON [tenant].[app_user] ([tenant_id], [branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_app_user_invite_token] 
    ON [tenant].[app_user] ([invite_token]) 
    WHERE [invite_token] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_tenant_app_user_reset_token] 
    ON [tenant].[app_user] ([password_reset_token]) 
    WHERE [password_reset_token] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_tenant_user_role_user_id] 
    ON [tenant].[user_role] ([user_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_user_role_role_id] 
    ON [tenant].[user_role] ([role_id]);
GO

-- Composite tenant isolation index for cross_branch_access
CREATE NONCLUSTERED INDEX [CU_cross_branch_access] 
    ON [tenant].[cross_branch_access] ([tenant_id], [access_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_cross_branch_access_user_status] 
    ON [tenant].[cross_branch_access] ([tenant_id], [user_id], [access_status]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_cross_branch_access_target_branch] 
    ON [tenant].[cross_branch_access] ([tenant_id], [target_branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_cross_branch_access_home_branch] 
    ON [tenant].[cross_branch_access] ([tenant_id], [home_branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_tenant_config_group] 
    ON [tenant].[tenant_config] ([tenant_id], [config_group]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_audit_log_module_time] 
    ON [tenant].[audit_log] ([tenant_id], [module], [performed_at] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_audit_log_entity] 
    ON [tenant].[audit_log] ([tenant_id], [entity_type], [entity_id]);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_audit_log_user_time] 
    ON [tenant].[audit_log] ([tenant_id], [user_id], [performed_at] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_rbac_change_log_tenant_time] 
    ON [tenant].[rbac_change_log] ([tenant_id], [changed_at] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_tenant_rbac_change_log_user] 
    ON [tenant].[rbac_change_log] ([affected_user_id]);
GO

-- ----------------------------------------------------------------------------
-- PARTICIPANT SCHEMA INDEXES
-- ----------------------------------------------------------------------------
-- Composite tenant isolation index for participant_profile
CREATE NONCLUSTERED INDEX [CU_participant_profile] 
    ON [participant].[participant_profile] ([tenant_id], [ndis_no]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_status_deleted] 
    ON [participant].[participant_profile] ([tenant_id], [participant_status], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_branch] 
    ON [participant].[participant_profile] ([tenant_id], [branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_support_coordinator] 
    ON [participant].[participant_profile] ([tenant_id], [support_coordinator_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_program] 
    ON [participant].[participant_profile] ([tenant_id], [program_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_disability_type] 
    ON [participant].[participant_profile] ([disability_type_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_profile_secondary_disability] 
    ON [participant].[participant_profile] ([secondary_disability_type_id]);
GO

-- Composite tenant isolation index for participant_personal_info
CREATE NONCLUSTERED INDEX [CU_participant_personal_info] 
    ON [participant].[participant_personal_info] ([tenant_id], [personal_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_personal_info_perm_state] 
    ON [participant].[participant_personal_info] ([perm_state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_personal_info_res_state] 
    ON [participant].[participant_personal_info] ([res_state_id]);
GO

-- Composite tenant isolation index for participant_contact_info
CREATE NONCLUSTERED INDEX [CU_participant_contact_info] 
    ON [participant].[participant_contact_info] ([tenant_id], [contact_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_contact_info_country] 
    ON [participant].[participant_contact_info] ([country_id]);
GO

-- Composite tenant isolation index for participant_emergency_contact
CREATE NONCLUSTERED INDEX [CU_participant_emergency_contact] 
    ON [participant].[participant_emergency_contact] ([tenant_id], [emergency_contact_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_emergency_contact_ndis_primary] 
    ON [participant].[participant_emergency_contact] ([tenant_id], [ndis_no], [is_primary]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_emergency_contact_relationship] 
    ON [participant].[participant_emergency_contact] ([relationship_type_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_emergency_contact_state] 
    ON [participant].[participant_emergency_contact] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_emergency_contact_country] 
    ON [participant].[participant_emergency_contact] ([country_id]);
GO

-- Composite tenant isolation index for participant_preferences
CREATE NONCLUSTERED INDEX [CU_participant_preferences] 
    ON [participant].[participant_preferences] ([tenant_id], [preference_id]);
GO

-- Composite tenant isolation index for participant_plan
CREATE NONCLUSTERED INDEX [CU_participant_plan] 
    ON [participant].[participant_plan] ([tenant_id], [plan_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_status_current] 
    ON [participant].[participant_plan] ([tenant_id], [ndis_no], [plan_status], [is_current]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_expiry_alerts] 
    ON [participant].[participant_plan] ([tenant_id], [plan_end_date], [plan_status]);
GO

-- Composite tenant isolation index for participant_plan_funding
CREATE NONCLUSTERED INDEX [CU_participant_plan_funding] 
    ON [participant].[participant_plan_funding] ([tenant_id], [funding_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_funding_ndis_category] 
    ON [participant].[participant_plan_funding] ([tenant_id], [ndis_no], [support_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_funding_plan] 
    ON [participant].[participant_plan_funding] ([plan_id]);
GO

-- Composite tenant isolation index for participant_plan_support_item
CREATE NONCLUSTERED INDEX [CU_participant_plan_support_item] 
    ON [participant].[participant_plan_support_item] ([tenant_id], [support_item_mapping_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_support_item_funding] 
    ON [participant].[participant_plan_support_item] ([funding_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_plan_support_item_support_item] 
    ON [participant].[participant_plan_support_item] ([support_item_id]);
GO

-- Composite tenant isolation index for participant_document
CREATE NONCLUSTERED INDEX [CU_participant_document] 
    ON [participant].[participant_document] ([tenant_id], [document_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_document_ndis_category] 
    ON [participant].[participant_document] ([tenant_id], [ndis_no], [document_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_document_expiry] 
    ON [participant].[participant_document] ([tenant_id], [expiry_date]) 
    WHERE [expiry_date] IS NOT NULL;
GO

-- Composite tenant isolation index for participant_goal
CREATE NONCLUSTERED INDEX [CU_participant_goal] 
    ON [participant].[participant_goal] ([tenant_id], [goal_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_ndis_status] 
    ON [participant].[participant_goal] ([tenant_id], [ndis_no], [goal_status]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_plan] 
    ON [participant].[participant_goal] ([plan_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_support_category] 
    ON [participant].[participant_goal] ([support_category_id]);
GO

-- Composite tenant isolation index for participant_goal_review
CREATE NONCLUSTERED INDEX [CU_participant_goal_review] 
    ON [participant].[participant_goal_review] ([tenant_id], [review_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_review_goal_date] 
    ON [participant].[participant_goal_review] ([tenant_id], [goal_id], [review_date] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_review_reviewed_by] 
    ON [participant].[participant_goal_review] ([reviewed_by]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_goal_review_participant] 
    ON [participant].[participant_goal_review] ([ndis_no]);
GO

-- Composite tenant isolation index for participant_care_note
CREATE NONCLUSTERED INDEX [CU_participant_care_note] 
    ON [participant].[participant_care_note] ([tenant_id], [care_note_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_care_note_ndis_date] 
    ON [participant].[participant_care_note] ([tenant_id], [ndis_no], [note_date] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_participant_care_note_ndis_status] 
    ON [participant].[participant_care_note] ([tenant_id], [ndis_no], [note_status]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_care_note_goal] 
    ON [participant].[participant_care_note] ([related_goal_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_care_note_support_item] 
    ON [participant].[participant_care_note] ([related_support_item_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_care_note_support_worker] 
    ON [participant].[participant_care_note] ([support_worker_id]);
GO

-- Composite tenant isolation index for participant_interaction
CREATE NONCLUSTERED INDEX [CU_participant_interaction] 
    ON [participant].[participant_interaction] ([tenant_id], [interaction_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_interaction_ndis_date] 
    ON [participant].[participant_interaction] ([tenant_id], [ndis_no], [interaction_date] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_participant_interaction_interacted_by] 
    ON [participant].[participant_interaction] ([interacted_by]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_interaction_follow_up] 
    ON [participant].[participant_interaction] ([tenant_id], [follow_up_required], [follow_up_due_date])
    WHERE [follow_up_required] = 1;
GO

-- Composite tenant isolation index for participant_risk_flag
CREATE NONCLUSTERED INDEX [CU_participant_risk_flag] 
    ON [participant].[participant_risk_flag] ([tenant_id], [risk_flag_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_risk_flag_status_severity] 
    ON [participant].[participant_risk_flag] ([tenant_id], [ndis_no], [risk_status], [severity]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_risk_flag_severity_status] 
    ON [participant].[participant_risk_flag] ([tenant_id], [severity], [risk_status]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_risk_flag_category] 
    ON [participant].[participant_risk_flag] ([risk_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_risk_flag_identified_by] 
    ON [participant].[participant_risk_flag] ([identified_by]);
GO

-- Composite tenant isolation index for participant_alert
CREATE NONCLUSTERED INDEX [CU_participant_alert] 
    ON [participant].[participant_alert] ([tenant_id], [alert_id]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_alert_dismissed_severity] 
    ON [participant].[participant_alert] ([tenant_id], [ndis_no], [is_dismissed], [severity]);
GO

CREATE NONCLUSTERED INDEX [IX_participant_alert_due_date] 
    ON [participant].[participant_alert] ([tenant_id], [due_date])
    WHERE [is_dismissed] = 0;
GO

-- ----------------------------------------------------------------------------
-- STAFF SCHEMA INDEXES
-- ----------------------------------------------------------------------------
-- Composite tenant isolation index for staff_profile
CREATE NONCLUSTERED INDEX [CU_staff_profile] 
    ON [staff].[staff_profile] ([tenant_id], [staff_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_profile_branch_status_deleted] 
    ON [staff].[staff_profile] ([tenant_id], [branch_id], [staff_status], [is_deleted]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_profile_user_id] 
    ON [staff].[staff_profile] ([tenant_id], [user_id]) 
    WHERE [user_id] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_staff_profile_reporting_manager] 
    ON [staff].[staff_profile] ([reporting_manager_id]);
GO

-- Composite tenant isolation index for staff_contact
CREATE NONCLUSTERED INDEX [CU_staff_contact] 
    ON [staff].[staff_contact] ([tenant_id], [contact_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_contact_state] 
    ON [staff].[staff_contact] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_contact_country] 
    ON [staff].[staff_contact] ([country_id]);
GO

-- Composite tenant isolation index for staff_identification
CREATE NONCLUSTERED INDEX [CU_staff_identification] 
    ON [staff].[staff_identification] ([tenant_id], [identification_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_identification_staff] 
    ON [staff].[staff_identification] ([tenant_id], [staff_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_identification_expiry] 
    ON [staff].[staff_identification] ([tenant_id], [expiry_date])
    WHERE [expiry_date] IS NOT NULL;
GO

-- Composite tenant isolation index for staff_qualification
CREATE NONCLUSTERED INDEX [CU_staff_qualification] 
    ON [staff].[staff_qualification] ([tenant_id], [qualification_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_qualification_staff_status] 
    ON [staff].[staff_qualification] ([tenant_id], [staff_id], [qualification_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_qualification_expiry_status] 
    ON [staff].[staff_qualification] ([tenant_id], [expiry_date], [qualification_status]) 
    WHERE [expiry_date] IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX [IX_staff_qualification_type] 
    ON [staff].[staff_qualification] ([qualification_type_id]);
GO

-- Composite tenant isolation index for staff_compliance
CREATE NONCLUSTERED INDEX [CU_staff_compliance] 
    ON [staff].[staff_compliance] ([tenant_id], [compliance_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_compliance_staff_status] 
    ON [staff].[staff_compliance] ([tenant_id], [staff_id], [compliance_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_compliance_expiry_status] 
    ON [staff].[staff_compliance] ([tenant_id], [expiry_date], [compliance_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_compliance_type] 
    ON [staff].[staff_compliance] ([compliance_type_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_compliance_state] 
    ON [staff].[staff_compliance] ([state_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_program_tenant_program] 
    ON [staff].[staff_program] ([tenant_id], [program_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_program_staff] 
    ON [staff].[staff_program] ([staff_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_branch_assignment_branch] 
    ON [staff].[staff_branch_assignment] ([tenant_id], [branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_branch_assignment_staff] 
    ON [staff].[staff_branch_assignment] ([staff_id]);
GO

-- Composite tenant isolation index for staff_availability
CREATE NONCLUSTERED INDEX [CU_staff_availability] 
    ON [staff].[staff_availability] ([tenant_id], [availability_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_availability_staff_day] 
    ON [staff].[staff_availability] ([tenant_id], [staff_id], [day_of_week]);
GO

-- Composite tenant isolation index for timesheet
CREATE NONCLUSTERED INDEX [CU_timesheet] 
    ON [staff].[timesheet] ([tenant_id], [timesheet_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_staff_status] 
    ON [staff].[timesheet] ([tenant_id], [staff_id], [timesheet_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_branch] 
    ON [staff].[timesheet] ([tenant_id], [branch_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_approved_by] 
    ON [staff].[timesheet] ([approved_by]);
GO

-- Composite tenant isolation index for timesheet_entry
CREATE NONCLUSTERED INDEX [CU_timesheet_entry] 
    ON [staff].[timesheet_entry] ([tenant_id], [entry_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_entry_timesheet] 
    ON [staff].[timesheet_entry] ([timesheet_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_entry_staff_date] 
    ON [staff].[timesheet_entry] ([tenant_id], [staff_id], [work_date]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_entry_participant] 
    ON [staff].[timesheet_entry] ([tenant_id], [ndis_no]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_timesheet_entry_support_item] 
    ON [staff].[timesheet_entry] ([support_item_id]);
GO

-- Composite tenant isolation index for leave_request
CREATE NONCLUSTERED INDEX [CU_leave_request] 
    ON [staff].[leave_request] ([tenant_id], [leave_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_leave_request_staff_status] 
    ON [staff].[leave_request] ([tenant_id], [staff_id], [leave_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_leave_request_start_status] 
    ON [staff].[leave_request] ([tenant_id], [start_date], [leave_status]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_leave_request_leave_type] 
    ON [staff].[leave_request] ([leave_type_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_leave_request_approved_by] 
    ON [staff].[leave_request] ([approved_by]);
GO

-- Composite tenant isolation index for staff_document
CREATE NONCLUSTERED INDEX [CU_staff_document] 
    ON [staff].[staff_document] ([tenant_id], [document_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_document_staff_category] 
    ON [staff].[staff_document] ([tenant_id], [staff_id], [document_category_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_document_expiry] 
    ON [staff].[staff_document] ([tenant_id], [expiry_date]) 
    WHERE [expiry_date] IS NOT NULL;
GO

-- Composite tenant isolation index for staff_performance_review
CREATE NONCLUSTERED INDEX [CU_staff_performance_review] 
    ON [staff].[staff_performance_review] ([tenant_id], [review_id]);
GO

CREATE NONCLUSTERED INDEX [IX_staff_performance_review_staff_date] 
    ON [staff].[staff_performance_review] ([tenant_id], [staff_id], [review_date] DESC);
GO

CREATE NONCLUSTERED INDEX [IX_staff_performance_review_reviewer] 
    ON [staff].[staff_performance_review] ([reviewer_id]);
GO

-- ============================================================================
-- SUMMARY OF CREATED OBJECTS
-- ============================================================================
/*
SCHEMAS CREATED (4):
  1. master       - Central reference lookups (Countries, States, NDIS Price Guide, Compliances)
  2. tenant       - Multi-tenant organisation hierarchy, branches, programs, RBAC, users, and audits
  3. participant  - Participant master, demographics, contacts, NDIS plans, budgets, goals, care notes
  4. staff        - Staff HR profiles, qualifications, WWCC compliance clearances, availability, timesheets

TABLES CREATED BY SCHEMA (61 total):

  [master] (12 tables):
    1.  master.country
    2.  master.state
    3.  master.disability_type
    4.  master.document_category
    5.  master.ndis_support_category
    6.  master.ndis_support_item
    7.  master.registration_group
    8.  master.qualification_type
    9.  master.compliance_type
    10. master.relationship_type
    11. master.leave_type
    12. master.risk_category

  [tenant] (21 tables):
    1.  tenant.subscription_plan
    2.  tenant.tenant
    3.  tenant.tenant_subscription
    4.  tenant.tenant_contact
    5.  tenant.tenant_address
    6.  tenant.tenant_service_state
    7.  tenant.tenant_registration_group
    8.  tenant.tenant_document
    9.  tenant.tenant_change_history
    10. tenant.branch
    11. tenant.program
    12. tenant.program_branch
    13. tenant.role
    14. tenant.permission
    15. tenant.role_permission
    16. tenant.app_user
    17. tenant.user_role
    18. tenant.cross_branch_access
    19. tenant.tenant_config
    20. tenant.audit_log
    21. tenant.rbac_change_log

  [participant] (15 tables):
    1.  participant.participant_profile
    2.  participant.participant_personal_info
    3.  participant.participant_contact_info
    4.  participant.participant_emergency_contact
    5.  participant.participant_preferences
    6.  participant.participant_plan
    7.  participant.participant_plan_funding
    8.  participant.participant_plan_support_item
    9.  participant.participant_document
    10. participant.participant_goal
    11. participant.participant_goal_review
    12. participant.participant_care_note
    13. participant.participant_interaction
    14. participant.participant_risk_flag
    15. participant.participant_alert

  [staff] (13 tables):
    1.  staff.staff_profile
    2.  staff.staff_contact
    3.  staff.staff_identification
    4.  staff.staff_qualification
    5.  staff.staff_compliance
    6.  staff.staff_program
    7.  staff.staff_branch_assignment
    8.  staff.staff_availability
    9.  staff.timesheet
    10. staff.timesheet_entry
    11. staff.leave_request
    12. staff.staff_document
    13. staff.staff_performance_review

COMPLIANCE & ARCHITECTURAL PATTERNS ENFORCED:
  - Strict MSSQL 2019+ T-SQL batch-separated syntax with GO statements
  - Unicode NVARCHAR string types across all character columns
  - DATETIMEOFFSET with DEFAULT SYSDATETIMEOFFSET() for accurate Australian timezone handling
  - Exact DECIMAL(12,2) for financial budgets and DECIMAL(10,4) for NDIS catalogue rates
  - PERSISTED computed column on participant_plan_funding.remaining_balance_aud
  - Multi-tenant data isolation via tenant_id foreign keys and CU_ composite indexes
  - Soft delete support across all operational tables with is_deleted and deleted_at
  - Comprehensive auditing via created_by, created_at, updated_by, updated_at
  - Immutable audit trail in tenant.audit_log and tenant.rbac_change_log
  - Standardized named constraint nomenclature: PK_*, FK_*, UQ_*, CK_*, CU_*, IX_*
*/
"""

with open(r"c:\new\ndis_mssql_schema.sql", "w", encoding="utf-8") as f:
    f.write(sql_content.strip() + "\n")

print("Schema generated successfully at c:\\new\\ndis_mssql_schema.sql")
