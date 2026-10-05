"""Per-tenant schema — 15 business tables.

Architecture overview
─────────────────────
  ndis_common  : Platform-level tables — subscription_plan, tenant,
                 tenant_subscription, app_user.  Created by migration 0002.

  tenant_<id>  : One schema per organisation, created at signup by
                 provision_tenant_schema() in app/core/tenant_schema.py.
                 Contains the 15 business tables documented below.

Schema naming convention (system-controlled, never user-provided)
  tenant_code "SUNSHI-001"  →  schema_name "tenant_sunshi_001"

STAMPED NOT RUN
───────────────
This migration is a HISTORICAL RECORD only.  Per-tenant schemas are
created at signup time by provision_tenant_schema(), not by Alembic.
On a brand-new database you would:
    alembic stamp 0001    # mark as applied without running DDL
The actual DDL engine lives in app/core/tenant_schema.py.

Tables (FK dependency order)
─────────────────────────────
  1.  branch
  2.  program
  3.  program_branch
  4.  role
  5.  permission
  6.  role_permission
  7.  user_role
  8.  cross_branch_access
  9.  tenant_config
  10. audit_log
  11. tenant_contact
  12. tenant_address
  13. tenant_service_state
  14. tenant_registration_group
  15. tenant_document

Revision ID: 0001
Revises:
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

# Schema placeholder — at runtime get_tenant_db() rewrites this to the real
# per-tenant schema name via SQLAlchemy's schema_translate_map.
_S = 'tenant_schema'


def upgrade() -> None:
    # This migration is STAMPED (not run).
    # The DDL below is the source of truth for the per-tenant schema structure.
    # It mirrors provision_tenant_schema() in app/core/tenant_schema.py exactly.

    # ── 1. branch ─────────────────────────────────────────────────────────────
    # Physical branch offices and service hubs.
    # No tenant_id column: schema isolation guarantees tenant separation.
    op.create_table(
        'branch',
        sa.Column('branch_id',      sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('branch_code',    sa.String(50),  nullable=False),
        sa.Column('branch_name',    sa.String(255), nullable=False),
        sa.Column('phone',          sa.String(20),  nullable=True),
        sa.Column('email',          sa.String(255), nullable=True),
        sa.Column('address_line1',  sa.String(255), nullable=True),
        sa.Column('suburb',         sa.String(100), nullable=True),
        sa.Column('state_code',     sa.String(10),  nullable=True),
        sa.Column('postcode',       sa.String(10),  nullable=True),
        sa.Column('is_head_office', sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('is_active',      sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('is_deleted',     sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('deleted_at',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by',     sa.Integer(),   nullable=True),
        sa.Column('created_at',     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_by',     sa.Integer(),   nullable=True),
        sa.Column('updated_at',     sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('branch_id'),
        sa.UniqueConstraint('branch_code', name='UQ_branch_code'),
        schema=_S,
    )

    # ── 2. program ────────────────────────────────────────────────────────────
    # Service lines offered by the tenant (In-Home Support, SIL, Therapy…).
    # No tenant_id column.
    op.create_table(
        'program',
        sa.Column('program_id',    sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('program_code',  sa.String(50),  nullable=False),
        sa.Column('program_name',  sa.String(255), nullable=False),
        sa.Column('description',   sa.Text(),      nullable=True),
        sa.Column('funding_type',  sa.String(100), nullable=True),
        sa.Column('is_active',     sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('is_deleted',    sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('deleted_at',    sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by',    sa.Integer(),   nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_by',    sa.Integer(),   nullable=True),
        sa.Column('updated_at',    sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('program_id'),
        sa.UniqueConstraint('program_code', name='UQ_program_code'),
        schema=_S,
    )

    # ── 3. program_branch ─────────────────────────────────────────────────────
    # Maps which programs are active at which branches.
    op.create_table(
        'program_branch',
        sa.Column('program_branch_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('program_id',        sa.Integer(), nullable=False),
        sa.Column('branch_id',         sa.Integer(), nullable=False),
        sa.Column('is_active',         sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at',        sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.ForeignKeyConstraint(['program_id'], [f'{_S}.program.program_id'],
                                name='FK_program_branch_program', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], [f'{_S}.branch.branch_id'],
                                name='FK_program_branch_branch', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('program_branch_id'),
        sa.UniqueConstraint('program_id', 'branch_id', name='UQ_program_branch'),
        schema=_S,
    )

    # ── 4. role ───────────────────────────────────────────────────────────────
    # RBAC roles — no tenant_id (one schema per tenant).
    op.create_table(
        'role',
        sa.Column('role_id',        sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('role_code',      sa.String(50),  nullable=False),
        sa.Column('role_name',      sa.String(150), nullable=False),
        sa.Column('description',    sa.Text(),      nullable=True),
        sa.Column('is_system_role', sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('is_active',      sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('is_deleted',     sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('deleted_at',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by',     sa.Integer(),   nullable=True),
        sa.Column('created_at',     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_by',     sa.Integer(),   nullable=True),
        sa.Column('updated_at',     sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('role_code', name='UQ_role_code'),
        schema=_S,
    )

    # ── 5. permission ─────────────────────────────────────────────────────────
    # Granular system actions across modules.
    op.create_table(
        'permission',
        sa.Column('permission_id',   sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('permission_code', sa.String(100), nullable=False),
        sa.Column('module',          sa.String(100), nullable=False),
        sa.Column('action',          sa.String(50),  nullable=False),
        sa.Column('description',     sa.String(255), nullable=True),
        sa.Column('is_active',       sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('created_at',      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.PrimaryKeyConstraint('permission_id'),
        sa.UniqueConstraint('permission_code', name='UQ_permission_code'),
        schema=_S,
    )

    # ── 6. role_permission ────────────────────────────────────────────────────
    # Permissions granted to a role.
    op.create_table(
        'role_permission',
        sa.Column('role_permission_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_id',            sa.Integer(), nullable=False),
        sa.Column('permission_id',      sa.Integer(), nullable=False),
        sa.Column('granted',            sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('granted_by',         sa.Integer(), nullable=True),
        sa.Column('granted_at',         sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.ForeignKeyConstraint(['role_id'],       [f'{_S}.role.role_id'],
                                name='FK_role_permission_role', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], [f'{_S}.permission.permission_id'],
                                name='FK_role_permission_permission', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_permission_id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='UQ_role_permission'),
        schema=_S,
    )

    # ── 7. user_role ──────────────────────────────────────────────────────────
    # Roles assigned to users.
    # user_id is a logical reference to ndis_common.app_user — no FK constraint
    # (cross-schema FKs not used in this architecture).
    op.create_table(
        'user_role',
        sa.Column('user_role_id', sa.Integer(),  autoincrement=True, nullable=False),
        sa.Column('user_id',      sa.String(50), nullable=False),
        sa.Column('role_id',      sa.Integer(),  nullable=False),
        sa.Column('assigned_by',  sa.String(50), nullable=True),
        sa.Column('assigned_at',  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('is_active',    sa.Boolean(),  nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['role_id'], [f'{_S}.role.role_id'],
                                name='FK_user_role_role', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_role_id'),
        sa.UniqueConstraint('user_id', 'role_id', name='UQ_user_role'),
        schema=_S,
    )

    # ── 8. cross_branch_access ────────────────────────────────────────────────
    # Grants a user access to another branch's data.
    # user_id logical reference — no cross-schema FK.
    op.create_table(
        'cross_branch_access',
        sa.Column('access_id',  sa.Integer(),  autoincrement=True, nullable=False),
        sa.Column('user_id',    sa.String(50), nullable=False),
        sa.Column('branch_id',  sa.Integer(),  nullable=False),
        sa.Column('granted_by', sa.String(50), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('is_active',  sa.Boolean(),  nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['branch_id'], [f'{_S}.branch.branch_id'],
                                name='FK_cross_branch_branch', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('access_id'),
        sa.UniqueConstraint('user_id', 'branch_id', name='UQ_cross_branch_access'),
        schema=_S,
    )

    # ── 9. tenant_config ──────────────────────────────────────────────────────
    # Regional, accounting, and NDIS system settings (one row per tenant schema).
    op.create_table(
        'tenant_config',
        sa.Column('config_id',                sa.Integer(),  autoincrement=True, nullable=False),
        sa.Column('date_format',              sa.String(20), nullable=False,
                  server_default='DD/MM/YYYY'),
        sa.Column('currency_code',            sa.String(10), nullable=False,
                  server_default='AUD'),
        sa.Column('enable_gst',               sa.Boolean(),  nullable=False, server_default='1'),
        sa.Column('enable_schads_award',      sa.Boolean(),  nullable=False, server_default='1'),
        sa.Column('enable_pace_integration',  sa.Boolean(),  nullable=False, server_default='0'),
        sa.Column('enable_proda_integration', sa.Boolean(),  nullable=False, server_default='0'),
        sa.Column('default_funding_type',     sa.String(50), nullable=True),
        sa.Column('invoice_prefix',           sa.String(10), nullable=False,
                  server_default='INV'),
        sa.Column('invoice_due_days',         sa.Integer(),  nullable=False, server_default='14'),
        sa.Column('updated_by',               sa.Integer(),  nullable=True),
        sa.Column('created_at',               sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_at',               sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('config_id'),
        schema=_S,
    )

    # ── 10. audit_log ─────────────────────────────────────────────────────────
    # Immutable audit trail.  BIGINT PK (audit_id) for high volume.
    # No tenant_id: schema isolation guarantees tenant separation.
    # user_id is a logical reference to ndis_common.app_user.
    op.create_table(
        'audit_log',
        sa.Column('audit_id',   sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id',    sa.String(50),   nullable=True),
        sa.Column('action',     sa.String(100),  nullable=False),
        sa.Column('table_name', sa.String(100),  nullable=False),
        sa.Column('record_id',  sa.String(100),  nullable=True),
        sa.Column('old_values', sa.Text(),        nullable=True),
        sa.Column('new_values', sa.Text(),        nullable=True),
        sa.Column('ip_address', sa.String(45),   nullable=True),
        sa.Column('user_agent', sa.String(500),  nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.PrimaryKeyConstraint('audit_id'),
        schema=_S,
    )

    # ── 11. tenant_contact ────────────────────────────────────────────────────
    # Primary / Billing / Support contact persons for the tenant.
    # tenant_id stored for reference; no cross-schema FK constraint.
    op.create_table(
        'tenant_contact',
        sa.Column('contact_id',     sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('tenant_id',      sa.Integer(),   nullable=False),
        sa.Column('contact_type',   sa.String(50),  nullable=False, server_default='Primary'),
        sa.Column('first_name',     sa.String(100), nullable=False),
        sa.Column('last_name',      sa.String(100), nullable=False),
        sa.Column('position_title', sa.String(150), nullable=True),
        sa.Column('email',          sa.String(255), nullable=True),
        sa.Column('phone',          sa.String(20),  nullable=True),
        sa.Column('mobile',         sa.String(20),  nullable=True),
        sa.Column('is_active',      sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('created_at',     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_at',     sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('contact_id'),
        sa.UniqueConstraint('tenant_id', 'contact_type', name='UQ_tenant_contact_tenant_type'),
        schema=_S,
    )

    # ── 12. tenant_address ────────────────────────────────────────────────────
    # Registered, mailing, and physical business addresses.
    # tenant_id stored for reference; no cross-schema FK constraint.
    op.create_table(
        'tenant_address',
        sa.Column('address_id',    sa.Integer(),  autoincrement=True, nullable=False),
        sa.Column('tenant_id',     sa.Integer(),  nullable=False),
        sa.Column('address_type',  sa.String(50),  nullable=False, server_default='Head Office'),
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('suburb',        sa.String(100), nullable=True),
        sa.Column('state_code',    sa.String(10),  nullable=True),
        sa.Column('postcode',      sa.String(10),  nullable=True),
        sa.Column('country_code',  sa.String(3),   nullable=False, server_default='AUS'),
        sa.Column('is_primary',    sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('created_at',    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_at',    sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('address_id'),
        schema=_S,
    )

    # ── 13. tenant_service_state ──────────────────────────────────────────────
    # States / territories where the tenant delivers NDIS services.
    op.create_table(
        'tenant_service_state',
        sa.Column('service_state_id', sa.Integer(),  autoincrement=True, nullable=False),
        sa.Column('tenant_id',        sa.Integer(),  nullable=False),
        sa.Column('state_code',       sa.String(10), nullable=False),
        sa.Column('is_active',        sa.Boolean(),  nullable=False, server_default='1'),
        sa.Column('created_at',       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.PrimaryKeyConstraint('service_state_id'),
        sa.UniqueConstraint('tenant_id', 'state_code', name='UQ_tenant_service_state'),
        schema=_S,
    )

    # ── 14. tenant_registration_group ─────────────────────────────────────────
    # NDIS Registration Groups approved for registered providers.
    op.create_table(
        'tenant_registration_group',
        sa.Column('tenant_reg_group_id',     sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('tenant_id',               sa.Integer(),   nullable=False),
        sa.Column('registration_group_code', sa.String(20),  nullable=False),
        sa.Column('registration_group_name', sa.String(255), nullable=False),
        sa.Column('is_active',               sa.Boolean(),   nullable=False, server_default='1'),
        sa.Column('created_at',              sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.PrimaryKeyConstraint('tenant_reg_group_id'),
        sa.UniqueConstraint('tenant_id', 'registration_group_code', name='UQ_tenant_reg_group'),
        schema=_S,
    )

    # ── 15. tenant_document ───────────────────────────────────────────────────
    # Organisation-level files, certificates, and compliance documents.
    op.create_table(
        'tenant_document',
        sa.Column('document_id',       sa.Integer(),   autoincrement=True, nullable=False),
        sa.Column('tenant_id',         sa.Integer(),   nullable=False),
        sa.Column('document_category', sa.String(100), nullable=False),
        sa.Column('document_name',     sa.String(255), nullable=False),
        sa.Column('file_path',         sa.String(1000), nullable=False),
        sa.Column('file_size_kb',      sa.Integer(),   nullable=True),
        sa.Column('mime_type',         sa.String(100), nullable=True),
        sa.Column('expiry_date',       sa.Date(),      nullable=True),
        sa.Column('uploaded_by',       sa.String(50),  nullable=False),
        sa.Column('uploaded_at',       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('is_deleted',        sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('deleted_at',        sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('document_id'),
        schema=_S,
    )


def downgrade() -> None:
    """Drop all 15 per-tenant tables in reverse FK dependency order."""
    op.drop_table('tenant_document',           schema=_S)
    op.drop_table('tenant_registration_group', schema=_S)
    op.drop_table('tenant_service_state',      schema=_S)
    op.drop_table('tenant_address',            schema=_S)
    op.drop_table('tenant_contact',            schema=_S)
    op.drop_table('audit_log',                 schema=_S)
    op.drop_table('tenant_config',             schema=_S)
    op.drop_table('cross_branch_access',       schema=_S)
    op.drop_table('user_role',                 schema=_S)
    op.drop_table('role_permission',           schema=_S)
    op.drop_table('permission',                schema=_S)
    op.drop_table('role',                      schema=_S)
    op.drop_table('program_branch',            schema=_S)
    op.drop_table('program',                   schema=_S)
    op.drop_table('branch',                    schema=_S)
