"""Shared helpers used across all tenant routers."""
import json
import logging
import re
import traceback
import uuid
from datetime import date
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import FieldValidationError
from app.core.security import get_password_hash
from app.core.tenant_schema import generate_schema_name, provision_tenant_schema
from app.database import engine
from app.models import (
    AppUser,
    AuditLog,
    Branch,
    Permission,
    RolePermission,
    SubscriptionPlan,
    Tenant,
    TenantConfig,
    TenantContact,
    TenantSubscription,
    UserRole,
)

logger = logging.getLogger(__name__)

# Public/personal email domains that cannot be used for org signup
_PUBLIC_DOMAINS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.com.au", "ymail.com",
    "outlook.com", "hotmail.com", "hotmail.com.au", "live.com", "live.com.au",
    "icloud.com", "me.com", "mac.com",
    "aol.com",
    "protonmail.com", "proton.me",
    "zoho.com",
    "mail.com",
    "bigpond.com", "bigpond.net.au",
    "optusnet.com.au",
    "internode.on.net",
}


# ─── Tenant access guard ───────────────────────────────────────────────────────

def verify_tenant_access(tenant_id: int, current_user: Dict[str, Any]) -> None:
    """Enforces multi-tenant isolation — compares JWT tenant_id against URL parameter."""
    if current_user.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot access or modify resources of another organization",
        )


async def require_permission(
    db: AsyncSession,
    current_user: Dict[str, Any],
    permission_code: str,
) -> None:
    """Checks that the current user holds a specific permission code.

    Tenant admins (is_tenant_admin=True) bypass all permission checks.
    Everyone else must have the code via at least one active role.

    Raises HTTP 403 if the permission is not held.
    """
    if current_user.get("is_tenant_admin"):
        return  # superuser — no check needed

    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")

    # Get the user's active role IDs
    role_id_rows = await db.scalars(
        select(UserRole.role_id).where(
            UserRole.user_id == user_id,
            UserRole.is_active == True,  # noqa: E712
        )
    )
    role_ids = list(role_id_rows)
    if not role_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: '{permission_code}' required",
        )

    # Check if any of those roles has the permission granted
    perm = await db.scalar(
        select(Permission.permission_id)
        .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
        .where(
            RolePermission.role_id.in_(role_ids),
            RolePermission.granted == True,  # noqa: E712
            Permission.permission_code == permission_code,
        )
    )
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: '{permission_code}' required",
        )


# ─── Audit log helper ─────────────────────────────────────────────────────────

async def log_audit(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    table_name: str,
    record_id: Optional[str],
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Appends an immutable audit log entry via a tenant-schema scoped session.

    IMPORTANT: `db` must be a tenant-scoped session (from get_tenant_db or an
    engine connection with schema_translate_map applied).  Never pass get_db().
    """
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    entry = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=str(record_id) if record_id is not None else None,
        old_values=json.dumps(old_values, default=str) if old_values else None,
        new_values=json.dumps(new_values, default=str) if new_values else None,
        ip_address=client_ip,
        user_agent=user_agent[:500] if user_agent else None,
    )
    db.add(entry)


# ─── Tenant code generation ────────────────────────────────────────────────────

async def generate_unique_tenant_code(db: AsyncSession, organisation_name: str) -> str:
    """Auto-generates a unique tenant slug code (e.g. SUNSHI-001)."""
    cleaned = re.sub(r"[^A-Z0-9]", "", organisation_name.upper())
    base = cleaned[:6] if len(cleaned) >= 3 else "NDIS"
    counter = 1
    candidate = f"{base}-001"
    while await db.scalar(select(Tenant.tenant_id).where(Tenant.tenant_code == candidate)):
        counter += 1
        candidate = f"{base}-{counter:03d}"
    return candidate


# ─── Main signup helper ───────────────────────────────────────────────────────

async def create_tenant_hierarchy(
    db: AsyncSession,
    signup_data: Any,
    is_registered: bool,
    request: Optional[Request] = None,
) -> Tenant:
    """Provisions a complete new tenant (schema-per-tenant architecture).

    Phase A — ndis_common (passed `db` session):
      1. ABN uniqueness check
      2. Get/create SubscriptionPlan
      3. Create Tenant row (flush → tenant_id)
      4. Create TenantSubscription + TenantContact
      5. Commit Phase A

    Phase B — DDL (raw engine connection):
      6. provision_tenant_schema() → CREATE SCHEMA + 10 tables

    Phase C — tenant_schema (new engine connection):
      7. Create Branch (flush → branch_id)
      8. Create TenantConfig
      9. Commit Phase C

    Phase D — ndis_common (passed `db` session):
      10. Create AppUser (branch_id from Phase C, logical ref)
      11. Commit Phase D

    Phase E — tenant_schema (audit):
      12. Write AuditLog entry → commit
    """
    # ── Phase A ───────────────────────────────────────────────────────────────
    admin_email_lower = signup_data.admin_email.lower()

    # 1. Exact email already registered
    existing_user = await db.scalar(
        select(AppUser).where(
            AppUser.email == admin_email_lower,
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if existing_user:
        raise FieldValidationError(
            field="admin_email",
            message="An account with this email already exists. Please log in instead.",
            status_code=status.HTTP_409_CONFLICT,
        )

    # 2. Block public/personal email providers
    email_domain = admin_email_lower.split("@", 1)[1]
    if email_domain in _PUBLIC_DOMAINS:
        raise FieldValidationError(
            field="admin_email",
            message=(
                f"Public email providers ({email_domain}) are not accepted. "
                "Please use your organisation's work email address."
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 3. Check if this email domain is already registered as an organisation
    existing_domain_tenant = await db.scalar(
        select(Tenant).where(
            Tenant.email_domain == email_domain,
            Tenant.is_deleted == False,  # noqa: E712
        )
    )
    if existing_domain_tenant:
        raise FieldValidationError(
            field="admin_email",
            message=(
                f"An organisation is already registered with the email domain @{email_domain}. "
                "Please contact your organisation admin to get access."
            ),
            status_code=status.HTTP_409_CONFLICT,
        )

    if getattr(signup_data, "abn", None):
        existing_abn = await db.scalar(
            select(Tenant).where(
                Tenant.abn == signup_data.abn,
                Tenant.is_deleted == False,  # noqa: E712
            )
        )
        if existing_abn:
            raise FieldValidationError(
                field="abn",
                message=f"An organization with ABN {signup_data.abn} is already registered",
                status_code=status.HTTP_409_CONFLICT,
            )

    plan_id = getattr(signup_data, "plan_id", None)
    if not plan_id:
        default_plan = await db.scalar(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active == True)  # noqa: E712
            .order_by(SubscriptionPlan.plan_id)
        )
        if default_plan:
            plan_id = default_plan.plan_id
        else:
            starter = SubscriptionPlan(
                plan_code="STARTER", plan_name="Starter Tier",
                max_branches=1, max_users=5, max_participants=50,
                monthly_price=149.00, monthly_fee_aud=149.00, annual_fee_aud=1490.00,
                is_active=True,
            )
            db.add(starter)
            await db.flush()
            plan_id = starter.plan_id

    tenant_code = await generate_unique_tenant_code(db, signup_data.organisation_name)
    schema_name = generate_schema_name(tenant_code)

    today = date.today()
    new_tenant = Tenant(
        tenant_code=tenant_code,
        schema_name=schema_name,
        organisation_name=signup_data.organisation_name,
        trading_name=getattr(signup_data, "trading_name", None),
        abn=getattr(signup_data, "abn", None),
        acn=getattr(signup_data, "acn", None),
        is_registered_provider=is_registered,
        ndis_registration_number=getattr(signup_data, "ndis_registration_number", None),
        registration_expiry_date=getattr(signup_data, "registration_expiry_date", None),
        provider_type=getattr(signup_data, "provider_type", None),
        organisation_type=getattr(signup_data, "organisation_type", None),
        primary_email=signup_data.primary_email.lower(),
        email_domain=email_domain,
        primary_phone=getattr(signup_data, "primary_phone", None),
        website_url=getattr(signup_data, "website_url", None),
        timezone=getattr(signup_data, "timezone", "Australia/Sydney"),
        status="Active",
        is_deleted=False,
    )
    db.add(new_tenant)
    try:
        await db.flush()  # gets tenant_id
    except IntegrityError as exc:
        await db.rollback()
        logger.error("Phase A flush FAILED (IntegrityError): %s", exc)
        # Most common cause: abn UNIQUE violation when multiple tenants have no ABN.
        # The startup migration replaces the inline UNIQUE with a filtered index,
        # but catch here as a safety net.
        if "abn" in str(exc).lower() or "UQ__tenant" in str(exc):
            raise FieldValidationError(
                field="abn",
                message="An organisation record with this ABN already exists. Please contact support or log in.",
                status_code=status.HTTP_409_CONFLICT,
            )
        raise HTTPException(status_code=500, detail=f"Registration conflict: {exc}")

    db.add(TenantSubscription(
        tenant_id=new_tenant.tenant_id, plan_id=plan_id,
        billing_cycle="Monthly", start_date=today, status="Active",
    ))
    await db.commit()
    await db.refresh(new_tenant)
    logger.info("Phase A complete: tenant %s (id=%d) in ndis_common", tenant_code, new_tenant.tenant_id)

    # ── Phase B: DDL ──────────────────────────────────────────────────────────
    try:
        async with engine.connect() as ddl_conn:
            await provision_tenant_schema(ddl_conn, schema_name)
        logger.info("Phase B complete: schema [%s] provisioned", schema_name)
    except Exception as exc:
        logger.error("Phase B FAILED for schema [%s]: %s\n%s", schema_name, exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Schema provisioning failed: {exc}")

    # ── Phase C: tenant_schema — Config + Contact (no auto branch) ────────────
    try:
        async with engine.connect() as t_conn:
            t_conn = await t_conn.execution_options(schema_translate_map={"tenant_schema": schema_name})
            async with AsyncSession(bind=t_conn, expire_on_commit=False) as t_db:
                t_db.add(TenantContact(
                    tenant_id=new_tenant.tenant_id, contact_type="Primary",
                    first_name=signup_data.admin_first_name,
                    last_name=signup_data.admin_last_name,
                    position_title=getattr(signup_data, "admin_job_title", None) or "Primary Administrator",
                    email=signup_data.admin_email.lower(),
                    phone=getattr(signup_data, "primary_phone", None),
                    mobile=getattr(signup_data, "admin_mobile", None),
                    is_active=True,
                ))
                t_db.add(TenantConfig(
                    date_format="DD/MM/YYYY", currency_code="AUD",
                    enable_gst=True, enable_schads_award=True,
                    enable_pace_integration=False, enable_proda_integration=False,
                    default_funding_type="Agency Managed" if is_registered else "Plan Managed",
                    invoice_prefix="INV", invoice_due_days=14,
                ))
                await t_db.commit()
        logger.info("Phase C complete: config provisioned in [%s]", schema_name)
    except Exception as exc:
        logger.error("Phase C FAILED in schema [%s]: %s\n%s", schema_name, exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Config setup failed: {exc}")

    # ── Phase D: ndis_common — AppUser ────────────────────────────────────────
    admin_user_id = str(uuid.uuid4())
    try:
        db.add(AppUser(
            user_id=admin_user_id,
            tenant_id=new_tenant.tenant_id,
            branch_id=None,  # no branch assigned at signup — admin creates branches themselves
            email=signup_data.admin_email.lower(),
            password_hash=get_password_hash(signup_data.admin_password),
            first_name=signup_data.admin_first_name,
            last_name=signup_data.admin_last_name,
            mobile=getattr(signup_data, "admin_mobile", None),
            job_title=getattr(signup_data, "admin_job_title", None) or "Administrator",
            is_tenant_admin=True, is_active=True, is_deleted=False,
            created_by="SIGNUP",
        ))
        await db.commit()
        logger.info("Phase D complete: admin user %s in ndis_common", admin_user_id)
    except Exception as exc:
        logger.error("Phase D FAILED: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"User account creation failed: {exc}")

    # ── Phase E: tenant_schema — AuditLog ─────────────────────────────────────
    try:
        async with engine.connect() as t_conn:
            t_conn = await t_conn.execution_options(schema_translate_map={"tenant_schema": schema_name})
            async with AsyncSession(bind=t_conn, expire_on_commit=False) as t_db:
                await log_audit(
                    db=t_db,
                    user_id=admin_user_id,
                    action="TENANT_REGISTERED",
                    table_name="tenant",
                    record_id=str(new_tenant.tenant_id),
                    new_values={
                        "organisation_name": new_tenant.organisation_name,
                        "abn": new_tenant.abn,
                        "tenant_code": new_tenant.tenant_code,
                        "schema_name": schema_name,
                    },
                    request=request,
                )
                await t_db.commit()
    except Exception as exc:
        logger.warning("Phase E: audit log write to [%s] failed (non-fatal): %s", schema_name, exc)

    await db.refresh(new_tenant)
    return new_tenant
