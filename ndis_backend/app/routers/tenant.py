"""Tenant Module API Router — fully async with Redis caching.
Handles Tenant onboarding, branches, programs, users, roles, config, and audit logging.
"""
import json
import re
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user, get_password_hash
from app.database import get_db, get_tenant_db
from app.models import (
    AppUser,
    AuditLog,
    Branch,
    Permission,
    Program,
    ProgramBranch,
    Role,
    RolePermission,
    SubscriptionPlan,
    Tenant,
    TenantAddress,
    TenantConfig,
    TenantContact,
    TenantSubscription,
    UserRole,
)
from app.schemas import (
    AppUserCreate,
    AppUserResponse,
    AppUserUpdate,
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    MessageResponse,
    PermissionResponse,
    ProgramCreate,
    ProgramResponse,
    ProgramUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    SubscriptionPlanResponse,
    TenantAddressCreate,
    TenantAddressResponse,
    TenantConfigResponse,
    TenantConfigUpdate,
    TenantContactCreate,
    TenantContactResponse,
    TenantContactUpdate,
    TenantListResponse,
    TenantResponse,
    TenantSignupNonRegistered,
    TenantSignupRegistered,
    TenantUpdate,
)

router = APIRouter(tags=["Tenant Management"])

# ---------------------------------------------------------------------------
# Cache TTL constants (seconds)
# ---------------------------------------------------------------------------
TTL_PLANS = 600       # subscription plans rarely change
TTL_TENANT = 300
TTL_CONTACTS = 300
TTL_ADDRESSES = 300
TTL_BRANCHES = 300
TTL_PROGRAMS = 300
TTL_ROLES = 300
TTL_PERMISSIONS = 600  # permissions seeded once, rarely change
TTL_USER = 300
TTL_CONFIG = 300


# ============================================================================
# Helper Functions
# ============================================================================

def verify_tenant_access(tenant_id: int, current_user: Dict[str, Any]) -> None:
    """Enforces multi-tenant isolation: user must belong to the requested tenant."""
    if current_user.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot access or modify resources of another organization",
        )


async def log_audit(
    db: AsyncSession,
    tenant_id: int,
    user_id: Optional[str],
    action: str,
    table_name: str,
    record_id: Optional[str],
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Appends an immutable audit log entry."""
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    entry = AuditLog(
        tenant_id=tenant_id,
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


async def generate_unique_tenant_code(db: AsyncSession, organisation_name: str) -> str:
    """Auto-generates a unique tenant slug code (e.g. CARE-001)."""
    cleaned = re.sub(r"[^A-Z0-9]", "", organisation_name.upper())
    base = cleaned[:6] if len(cleaned) >= 3 else "NDIS"
    counter = 1
    candidate = f"{base}-001"
    while await db.scalar(select(Tenant.tenant_id).where(Tenant.tenant_code == candidate)):
        counter += 1
        candidate = f"{base}-{counter:03d}"
    return candidate


async def create_tenant_hierarchy(
    db: AsyncSession,
    signup_data: Any,
    is_registered: bool,
    request: Optional[Request] = None,
) -> Tenant:
    """Provisions Tenant + Subscription + Branch + Admin User + Config in one transaction."""
    # 1. Check ABN uniqueness
    if signup_data.abn:
        existing_abn = await db.scalar(
            select(Tenant).where(Tenant.abn == signup_data.abn, Tenant.is_deleted == False)  # noqa: E712
        )
        if existing_abn:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An organization with ABN {signup_data.abn} is already registered",
            )

    # 2. Determine Subscription Plan
    plan_id = signup_data.plan_id
    if not plan_id:
        default_plan = await db.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.plan_id)  # noqa: E712
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

    # 3. Create Tenant
    tenant_code = await generate_unique_tenant_code(db, signup_data.organisation_name)
    today = date.today()
    new_tenant = Tenant(
        tenant_code=tenant_code,
        organisation_name=signup_data.organisation_name,
        trading_name=signup_data.trading_name,
        abn=signup_data.abn,
        acn=signup_data.acn,
        is_registered_provider=is_registered,
        ndis_registration_number=getattr(signup_data, "ndis_registration_number", None),
        registration_expiry_date=getattr(signup_data, "registration_expiry_date", None),
        provider_type=signup_data.provider_type,
        organisation_type=signup_data.organisation_type,
        primary_email=signup_data.primary_email.lower(),
        primary_phone=signup_data.primary_phone,
        website_url=signup_data.website_url,
        timezone=signup_data.timezone,
        status="Active",
        is_deleted=False,
    )
    db.add(new_tenant)
    await db.flush()

    # 4. Subscription
    db.add(TenantSubscription(
        tenant_id=new_tenant.tenant_id, plan_id=plan_id,
        billing_cycle="Monthly", start_date=today, status="Active",
    ))

    # 5. Admin AppUser (no auto branch — admin creates branches themselves)
    admin_user_id = str(uuid.uuid4())
    db.add(AppUser(
        user_id=admin_user_id,
        tenant_id=new_tenant.tenant_id,
        branch_id=None,
        email=signup_data.admin_email.lower(),
        password_hash=get_password_hash(signup_data.admin_password),
        first_name=signup_data.admin_first_name,
        last_name=signup_data.admin_last_name,
        mobile=signup_data.admin_mobile,
        job_title=signup_data.admin_job_title or "Administrator",
        is_tenant_admin=True, is_active=True, is_deleted=False,
        created_by="SIGNUP",
    ))

    # 7. Default Config
    db.add(TenantConfig(
        tenant_id=new_tenant.tenant_id,
        date_format="DD/MM/YYYY", currency_code="AUD",
        enable_gst=True, enable_schads_award=True,
        enable_pace_integration=False, enable_proda_integration=False,
        default_funding_type="Agency Managed" if is_registered else "Plan Managed",
        invoice_prefix="INV", invoice_due_days=14,
    ))

    # 8. Primary Contact
    db.add(TenantContact(
        tenant_id=new_tenant.tenant_id, contact_type="Primary",
        first_name=signup_data.admin_first_name,
        last_name=signup_data.admin_last_name,
        position_title=signup_data.admin_job_title or "Primary Administrator",
        email=signup_data.admin_email.lower(),
        phone=signup_data.primary_phone,
        mobile=signup_data.admin_mobile,
        is_active=True,
    ))

    # 9. Audit
    await log_audit(
        db=db, tenant_id=new_tenant.tenant_id, user_id=admin_user_id,
        action="TENANT_REGISTERED", table_name="tenant",
        record_id=str(new_tenant.tenant_id),
        new_values={"organisation_name": new_tenant.organisation_name,
                    "abn": new_tenant.abn, "tenant_code": new_tenant.tenant_code,
                    "provider_type": new_tenant.provider_type},
        request=request,
    )

    await db.commit()
    await db.refresh(new_tenant)
    return new_tenant


# ============================================================================
# Public Routes: Subscription Plans
# ============================================================================

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionPlanResponse]:
    """Public endpoint: returns all active subscription plans."""
    key = "plans:all"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    plans = (await db.scalars(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.plan_id)  # noqa: E712
    )).all()

    result = [SubscriptionPlanResponse.model_validate(p).model_dump(mode="json") for p in plans]
    await cache_set(key, result, ttl=TTL_PLANS)
    return result


# ============================================================================
# Tenant Signup Endpoints (Public)
# ============================================================================

@router.post("/tenant/signup/registered", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def signup_registered_provider(
    request: Request,
    payload: TenantSignupRegistered,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Onboards a Registered NDIS Provider."""
    tenant = await create_tenant_hierarchy(db, payload, is_registered=True, request=request)
    await cache_delete("plans:all")  # plan may have been seeded
    return TenantResponse.model_validate(tenant)


@router.post("/tenant/signup/non-registered", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def signup_non_registered_provider(
    request: Request,
    payload: TenantSignupNonRegistered,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Onboards a Non-Registered NDIS Provider."""
    tenant = await create_tenant_hierarchy(db, payload, is_registered=False, request=request)
    return TenantResponse.model_validate(tenant)


# ============================================================================
# Tenant CRUD Endpoints (Protected)
# ============================================================================

@router.get("/tenant", response_model=TenantListResponse)
async def list_tenants(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantListResponse:
    """Lists tenants with optional search and pagination."""
    stmt = select(Tenant).where(
        Tenant.tenant_id == current_user["tenant_id"],
        Tenant.is_deleted == False,  # noqa: E712
    )
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(
            Tenant.organisation_name.ilike(term),
            Tenant.tenant_code.ilike(term),
            Tenant.abn.ilike(term),
        ))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = (await db.scalars(stmt.offset(skip).limit(limit))).all()
    return TenantListResponse(
        total=total, skip=skip, limit=limit,
        items=[TenantResponse.model_validate(i) for i in items],
    )


@router.get("/tenant/{tenant_id}", response_model=TenantResponse)
async def get_tenant_by_id(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Fetches details of a specific tenant."""
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    result = TenantResponse.model_validate(tenant).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_TENANT)
    return result


@router.put("/tenant/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Updates tenant profile details."""
    verify_tenant_access(tenant_id, current_user)
    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    old_data = {c.name: getattr(tenant, c.name) for c in tenant.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    # Keep is_registered_provider in sync when provider_type is explicitly updated
    if "provider_type" in update_data:
        tenant.is_registered_provider = (update_data["provider_type"] == "Registered")

    # Commit tenant update FIRST — audit log uses a separate tenant-schema session
    # so a failed audit write never rolls back the real save.
    await db.commit()
    await db.refresh(tenant)
    await cache_delete(f"tenant:{tenant_id}")

    # Write audit log to the tenant's own schema (best-effort — never blocks the response)
    try:
        schema_name = tenant.schema_name
        if schema_name:
            async for tenant_db in get_tenant_db(schema_name):
                await log_audit(
                    db=tenant_db,
                    tenant_id=tenant_id,
                    user_id=current_user["user_id"],
                    action="UPDATE",
                    table_name="tenant",
                    record_id=str(tenant_id),
                    old_values=old_data,
                    new_values=update_data,
                    request=request,
                )
                await tenant_db.commit()
    except Exception:
        pass  # Audit log failure never blocks the response

    return TenantResponse.model_validate(tenant)


@router.delete("/tenant/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(
    tenant_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Soft-deletes an organization."""
    verify_tenant_access(tenant_id, current_user)
    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    tenant.is_deleted = True
    tenant.deleted_at = datetime.now(timezone.utc)
    tenant.status = "Inactive"

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="SOFT_DELETE", table_name="tenant", record_id=str(tenant_id),
                    request=request)
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}")
    return MessageResponse(message=f"Tenant {tenant.organisation_name} has been soft-deleted")


# ============================================================================
# Tenant Contacts
# ============================================================================

@router.get("/tenant/{tenant_id}/contacts", response_model=List[TenantContactResponse])
async def list_tenant_contacts(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TenantContactResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:contacts"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    contacts = (await db.scalars(
        select(TenantContact).where(TenantContact.tenant_id == tenant_id).order_by(TenantContact.contact_id)
    )).all()
    result = [TenantContactResponse.model_validate(c).model_dump(mode="json") for c in contacts]
    await cache_set(key, result, ttl=TTL_CONTACTS)
    return result


@router.post("/tenant/{tenant_id}/contacts", response_model=TenantContactResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_contact(
    tenant_id: int,
    payload: TenantContactCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantContactResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(TenantContact).where(
        TenantContact.tenant_id == tenant_id,
        TenantContact.contact_type == payload.contact_type.strip(),
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Contact of type '{payload.contact_type}' already exists")

    contact = TenantContact(
        tenant_id=tenant_id, contact_type=payload.contact_type.strip(),
        first_name=payload.first_name.strip(), last_name=payload.last_name.strip(),
        position_title=payload.position_title, email=payload.email.lower(),
        phone=payload.phone, mobile=payload.mobile, is_active=payload.is_active,
    )
    db.add(contact)
    await db.flush()

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="tenant_contact",
                    record_id=str(contact.contact_id), new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(contact)
    await cache_delete(f"tenant:{tenant_id}:contacts")
    return TenantContactResponse.model_validate(contact)


@router.put("/tenant/{tenant_id}/contacts/{contact_id}", response_model=TenantContactResponse)
async def update_tenant_contact(
    tenant_id: int,
    contact_id: int,
    payload: TenantContactUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantContactResponse:
    verify_tenant_access(tenant_id, current_user)
    contact = await db.scalar(select(TenantContact).where(
        TenantContact.contact_id == contact_id, TenantContact.tenant_id == tenant_id
    ))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    old_values = {c.name: getattr(contact, c.name) for c in contact.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(contact, field, val)

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="tenant_contact", record_id=str(contact_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(contact)
    await cache_delete(f"tenant:{tenant_id}:contacts")
    return TenantContactResponse.model_validate(contact)


# ============================================================================
# Tenant Addresses
# ============================================================================

@router.get("/tenant/{tenant_id}/addresses", response_model=List[TenantAddressResponse])
async def list_tenant_addresses(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TenantAddressResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:addresses"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    addresses = (await db.scalars(
        select(TenantAddress).where(TenantAddress.tenant_id == tenant_id).order_by(TenantAddress.address_id)
    )).all()
    result = [TenantAddressResponse.model_validate(a).model_dump(mode="json") for a in addresses]
    await cache_set(key, result, ttl=TTL_ADDRESSES)
    return result


@router.post("/tenant/{tenant_id}/addresses", response_model=TenantAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_address(
    tenant_id: int,
    payload: TenantAddressCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantAddressResponse:
    verify_tenant_access(tenant_id, current_user)

    if payload.is_primary:
        primaries = (await db.scalars(select(TenantAddress).where(
            TenantAddress.tenant_id == tenant_id, TenantAddress.is_primary == True  # noqa: E712
        ))).all()
        for addr in primaries:
            addr.is_primary = False

    new_address = TenantAddress(
        tenant_id=tenant_id, address_type=payload.address_type,
        address_line1=payload.address_line1, address_line2=payload.address_line2,
        suburb=payload.suburb, state_code=payload.state_code,
        postcode=payload.postcode, country_code=payload.country_code,
        is_primary=payload.is_primary,
    )
    db.add(new_address)
    await db.flush()

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="tenant_address",
                    record_id=str(new_address.address_id), new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(new_address)
    await cache_delete(f"tenant:{tenant_id}:addresses")
    return TenantAddressResponse.model_validate(new_address)


# ============================================================================
# Branches
# ============================================================================

@router.get("/tenant/{tenant_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BranchResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:branches"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    branches = (await db.scalars(
        select(Branch).where(Branch.tenant_id == tenant_id, Branch.is_deleted == False)  # noqa: E712
        .order_by(Branch.is_head_office.desc(), Branch.branch_id)
    )).all()
    result = [BranchResponse.model_validate(b).model_dump(mode="json") for b in branches]
    await cache_set(key, result, ttl=TTL_BRANCHES)
    return result


@router.post("/tenant/{tenant_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    tenant_id: int,
    payload: BranchCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(Branch).where(
        Branch.tenant_id == tenant_id,
        Branch.branch_code == payload.branch_code.strip(),
        Branch.is_deleted == False,  # noqa: E712
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Branch with code '{payload.branch_code}' already exists")

    branch = Branch(
        tenant_id=tenant_id,
        branch_code=payload.branch_code.strip().upper(),
        branch_name=payload.branch_name.strip(),
        phone=payload.phone,
        email=payload.email.lower() if payload.email else None,
        address_line1=payload.address_line1, suburb=payload.suburb,
        state_code=payload.state_code, postcode=payload.postcode,
        is_head_office=payload.is_head_office, is_active=payload.is_active, is_deleted=False,
    )
    db.add(branch)
    await db.flush()

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="branch", record_id=str(branch.branch_id),
                    new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(branch)
    await cache_delete(f"tenant:{tenant_id}:branches")
    return BranchResponse.model_validate(branch)


@router.get("/tenant/{tenant_id}/branches/{branch_id}", response_model=BranchResponse)
async def get_branch_by_id(
    tenant_id: int,
    branch_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:branch:{branch_id}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id, Branch.tenant_id == tenant_id, Branch.is_deleted == False  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    result = BranchResponse.model_validate(branch).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_BRANCHES)
    return result


@router.put("/tenant/{tenant_id}/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    tenant_id: int,
    branch_id: int,
    payload: BranchUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)
    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id, Branch.tenant_id == tenant_id, Branch.is_deleted == False  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    old_values = {c.name: getattr(branch, c.name) for c in branch.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(branch, field, val)

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="branch", record_id=str(branch_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(branch)
    await cache_delete(f"tenant:{tenant_id}:branches", f"tenant:{tenant_id}:branch:{branch_id}")
    return BranchResponse.model_validate(branch)


@router.delete("/tenant/{tenant_id}/branches/{branch_id}", response_model=MessageResponse)
async def delete_branch(
    tenant_id: int,
    branch_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id, Branch.tenant_id == tenant_id, Branch.is_deleted == False  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    if branch.is_head_office:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot delete the Head Office branch")

    branch.is_deleted = True
    branch.deleted_at = datetime.now(timezone.utc)
    branch.is_active = False

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="SOFT_DELETE", table_name="branch", record_id=str(branch_id), request=request)
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:branches", f"tenant:{tenant_id}:branch:{branch_id}")
    return MessageResponse(message=f"Branch {branch.branch_name} has been soft-deleted")


# ============================================================================
# Programs
# ============================================================================

@router.get("/tenant/{tenant_id}/programs", response_model=List[ProgramResponse])
async def list_programs(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ProgramResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:programs"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    programs = (await db.scalars(
        select(Program).where(Program.tenant_id == tenant_id, Program.is_deleted == False)  # noqa: E712
        .order_by(Program.program_id)
    )).all()
    result = [ProgramResponse.model_validate(p).model_dump(mode="json") for p in programs]
    await cache_set(key, result, ttl=TTL_PROGRAMS)
    return result


@router.post("/tenant/{tenant_id}/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    tenant_id: int,
    payload: ProgramCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(Program).where(
        Program.tenant_id == tenant_id,
        Program.program_code == payload.program_code.strip(),
        Program.is_deleted == False,  # noqa: E712
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Program with code '{payload.program_code}' already exists")

    program = Program(
        tenant_id=tenant_id,
        program_code=payload.program_code.strip().upper(),
        program_name=payload.program_name.strip(),
        description=payload.description,
        funding_type=payload.funding_type,
        is_active=payload.is_active, is_deleted=False,
    )
    db.add(program)
    await db.flush()

    if payload.branch_ids:
        for b_id in payload.branch_ids:
            db.add(ProgramBranch(program_id=program.program_id, branch_id=b_id, is_active=True))

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="program", record_id=str(program.program_id),
                    new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(program)
    await cache_delete(f"tenant:{tenant_id}:programs")
    return ProgramResponse.model_validate(program)


@router.put("/tenant/{tenant_id}/programs/{program_id}", response_model=ProgramResponse)
async def update_program(
    tenant_id: int,
    program_id: int,
    payload: ProgramUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    verify_tenant_access(tenant_id, current_user)
    program = await db.scalar(select(Program).where(
        Program.program_id == program_id, Program.tenant_id == tenant_id, Program.is_deleted == False  # noqa: E712
    ))
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    old_values = {c.name: getattr(program, c.name) for c in program.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(program, field, val)

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="program", record_id=str(program_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(program)
    await cache_delete(f"tenant:{tenant_id}:programs")
    return ProgramResponse.model_validate(program)


# ============================================================================
# Roles & Permissions
# ============================================================================

@router.get("/tenant/{tenant_id}/roles", response_model=List[RoleResponse])
async def list_roles(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RoleResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:roles"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    roles = (await db.scalars(
        select(Role).where(
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
            Role.is_active == True,  # noqa: E712
        ).order_by(Role.is_system_role.desc(), Role.role_id)
    )).all()
    result = [RoleResponse.model_validate(r).model_dump(mode="json") for r in roles]
    await cache_set(key, result, ttl=TTL_ROLES)
    return result


@router.post("/tenant/{tenant_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    tenant_id: int,
    payload: RoleCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(Role).where(
        Role.tenant_id == tenant_id,
        Role.role_code == payload.role_code.strip().upper(),
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Role with code '{payload.role_code}' already exists")

    role = Role(
        tenant_id=tenant_id,
        role_code=payload.role_code.strip().upper(),
        role_name=payload.role_name.strip(),
        description=payload.description,
        is_system_role=False, is_active=payload.is_active,
    )
    db.add(role)
    await db.flush()

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="role", record_id=str(role.role_id),
                    new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.put("/tenant/{tenant_id}/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    tenant_id: int,
    role_id: int,
    payload: RoleUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    verify_tenant_access(tenant_id, current_user)
    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="System roles cannot be modified by tenants")
    if role.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Cannot modify another tenant's role")

    old_values = {c.name: getattr(role, c.name) for c in role.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(role, field, val)

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="role", record_id=str(role_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.get("/tenant/{tenant_id}/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PermissionResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:permissions"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    permissions = (await db.scalars(
        select(Permission).order_by(Permission.module, Permission.permission_code)
    )).all()
    result = [PermissionResponse.model_validate(p).model_dump(mode="json") for p in permissions]
    await cache_set(key, result, ttl=TTL_PERMISSIONS)
    return result


@router.post("/tenant/{tenant_id}/roles/{role_id}/permissions/{permission_id}", response_model=MessageResponse)
async def assign_permission_to_role(
    tenant_id: int,
    role_id: int,
    permission_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.tenant_id and role.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another tenant's role")

    perm = await db.scalar(select(Permission).where(Permission.permission_id == permission_id))
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    existing = await db.scalar(select(RolePermission).where(
        RolePermission.role_id == role_id, RolePermission.permission_id == permission_id
    ))
    if existing:
        return MessageResponse(message="Permission is already assigned to this role")

    db.add(RolePermission(role_id=role_id, permission_id=permission_id, granted=True))
    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="GRANT_PERMISSION", table_name="role_permission",
                    record_id=f"{role_id}:{permission_id}", request=request)
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:roles")
    return MessageResponse(message=f"Permission {perm.permission_code} assigned to role {role.role_name}")


# ============================================================================
# Users
# ============================================================================

@router.get("/tenant/{tenant_id}/users", response_model=List[AppUserResponse])
async def list_users(
    tenant_id: int,
    branch_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AppUserResponse]:
    verify_tenant_access(tenant_id, current_user)
    stmt = select(AppUser).where(AppUser.tenant_id == tenant_id, AppUser.is_deleted == False)  # noqa: E712
    if branch_id is not None:
        stmt = stmt.where(AppUser.branch_id == branch_id)
    if is_active is not None:
        stmt = stmt.where(AppUser.is_active == is_active)
    stmt = stmt.order_by(AppUser.first_name, AppUser.last_name)
    users = (await db.scalars(stmt)).all()
    return [AppUserResponse.model_validate(u) for u in users]


@router.post("/tenant/{tenant_id}/users", response_model=AppUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    tenant_id: int,
    payload: AppUserCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppUserResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(AppUser).where(
        AppUser.tenant_id == tenant_id,
        AppUser.email == payload.email.lower().strip(),
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User with email '{payload.email}' already exists")

    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == payload.branch_id, Branch.tenant_id == tenant_id, Branch.is_deleted == False  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Selected branch not found or does not belong to this tenant")

    user_id = str(uuid.uuid4())
    user = AppUser(
        user_id=user_id, tenant_id=tenant_id, branch_id=payload.branch_id,
        email=payload.email.lower().strip(),
        password_hash=get_password_hash(payload.password),
        first_name=payload.first_name.strip(), last_name=payload.last_name.strip(),
        mobile=payload.mobile, job_title=payload.job_title,
        is_tenant_admin=payload.is_tenant_admin, is_active=payload.is_active,
        is_deleted=False, created_by=current_user["user_id"],
    )
    db.add(user)
    await db.flush()

    if payload.role_ids:
        for r_id in payload.role_ids:
            db.add(UserRole(user_id=user_id, role_id=r_id,
                            assigned_by=current_user["user_id"], is_active=True))

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="CREATE", table_name="app_user", record_id=user_id,
                    new_values={"email": user.email, "first_name": user.first_name,
                                "last_name": user.last_name, "branch_id": user.branch_id,
                                "is_tenant_admin": user.is_tenant_admin},
                    request=request)
    await db.commit()
    await db.refresh(user)
    return AppUserResponse.model_validate(user)


@router.get("/tenant/{tenant_id}/users/{user_id}", response_model=AppUserResponse)
async def get_user_by_id(
    tenant_id: int,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppUserResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:user:{user_id}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id, AppUser.tenant_id == tenant_id, AppUser.is_deleted == False  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = AppUserResponse.model_validate(user).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_USER)
    return result


@router.put("/tenant/{tenant_id}/users/{user_id}", response_model=AppUserResponse)
async def update_user(
    tenant_id: int,
    user_id: str,
    payload: AppUserUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppUserResponse:
    verify_tenant_access(tenant_id, current_user)
    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id, AppUser.tenant_id == tenant_id, AppUser.is_deleted == False  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_values = {
        "first_name": user.first_name, "last_name": user.last_name,
        "branch_id": user.branch_id, "mobile": user.mobile,
        "job_title": user.job_title, "is_active": user.is_active,
    }

    if payload.branch_id is not None:
        user.branch_id = payload.branch_id
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.mobile is not None:
        user.mobile = payload.mobile
    if payload.job_title is not None:
        user.job_title = payload.job_title
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
        user.password_changed_at = datetime.now(timezone.utc)

    user.updated_by = current_user["user_id"]

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="app_user", record_id=user_id,
                    old_values=old_values,
                    new_values=payload.model_dump(exclude={"password"}, exclude_unset=True),
                    request=request)
    await db.commit()
    await db.refresh(user)
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return AppUserResponse.model_validate(user)


@router.delete("/tenant/{tenant_id}/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    tenant_id: int,
    user_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id, AppUser.tenant_id == tenant_id, AppUser.is_deleted == False  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_tenant_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot delete the primary tenant administrator")

    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="SOFT_DELETE", table_name="app_user", record_id=user_id, request=request)
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return MessageResponse(message=f"User {user.email} has been deactivated and deleted")


@router.post("/tenant/{tenant_id}/users/{user_id}/roles/{role_id}", response_model=MessageResponse)
async def assign_role_to_user(
    tenant_id: int,
    user_id: str,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id, AppUser.tenant_id == tenant_id, AppUser.is_deleted == False  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.tenant_id and role.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign another tenant's role")

    existing = await db.scalar(select(UserRole).where(
        UserRole.user_id == user_id, UserRole.role_id == role_id
    ))
    if existing:
        return MessageResponse(message=f"User already has role {role.role_name}")

    db.add(UserRole(user_id=user_id, role_id=role_id,
                    assigned_by=current_user["user_id"], is_active=True))
    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="ASSIGN_ROLE", table_name="user_role",
                    record_id=f"{user_id}:{role_id}", request=request)
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return MessageResponse(message=f"Role {role.role_name} assigned to user {user.email}")


# ============================================================================
# Tenant Configuration
# ============================================================================

@router.get("/tenant/{tenant_id}/config", response_model=TenantConfigResponse)
async def get_tenant_config(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantConfigResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:config"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    config = await db.scalar(select(TenantConfig).where(TenantConfig.tenant_id == tenant_id))
    if not config:
        config = TenantConfig(
            tenant_id=tenant_id, date_format="DD/MM/YYYY", currency_code="AUD",
            enable_gst=True, enable_schads_award=True,
            enable_pace_integration=False, enable_proda_integration=False,
            default_funding_type="Agency Managed", invoice_prefix="INV", invoice_due_days=14,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    result = TenantConfigResponse.model_validate(config).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_CONFIG)
    return result


@router.put("/tenant/{tenant_id}/config", response_model=TenantConfigResponse)
async def update_tenant_config(
    tenant_id: int,
    payload: TenantConfigUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantConfigResponse:
    verify_tenant_access(tenant_id, current_user)
    config = await db.scalar(select(TenantConfig).where(TenantConfig.tenant_id == tenant_id))
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant configuration not found")

    old_values = {c.name: getattr(config, c.name) for c in config.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(config, field, val)

    await log_audit(db=db, tenant_id=tenant_id, user_id=current_user["user_id"],
                    action="UPDATE", table_name="tenant_config", record_id=str(config.config_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(config)
    await cache_delete(f"tenant:{tenant_id}:config")
    return TenantConfigResponse.model_validate(config)
