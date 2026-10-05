"""Tenant Signup router — public endpoints for onboarding new providers."""
import time
from fastapi import APIRouter, Depends, Query, Request, status

from app.core.cache import cache_delete
from app.database import get_db
from app.routers.helpers import create_tenant_hierarchy, _PUBLIC_DOMAINS
from app.schemas import TenantResponse, TenantSignupNonRegistered, TenantSignupRegistered, DomainCheckResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Tenant

router = APIRouter(tags=["Tenant Signup"])

# ── Simple TTL cache for domain availability (avoids repeated DB hits) ────────
_domain_cache: dict[str, tuple[bool, str, float]] = {}  # domain -> (available, message, ts)
_DOMAIN_CACHE_TTL = 120  # seconds


@router.get("/tenant/check-domain", response_model=DomainCheckResponse)
async def check_email_domain(
    email: str = Query(..., description="Full email address to check"),
    db: AsyncSession = Depends(get_db),
) -> DomainCheckResponse:
    """
    Domain availability check for signup.
    Results are cached for 2 minutes to avoid repeated DB hits.
    """
    email_clean = email.strip().lower()
    if "@" not in email_clean:
        return DomainCheckResponse(available=False, domain="", message="Invalid email address.")

    domain = email_clean.split("@", 1)[1]

    # Public domains — no DB needed
    if domain in _PUBLIC_DOMAINS:
        return DomainCheckResponse(
            available=False,
            domain=domain,
            message=f"Public email providers ({domain}) are not accepted. Please use your organisation's work email address.",
        )

    # Return cached result if fresh
    cached = _domain_cache.get(domain)
    if cached and time.monotonic() - cached[2] < _DOMAIN_CACHE_TTL:
        return DomainCheckResponse(available=cached[0], domain=domain, message=cached[1])

    # DB check
    existing = await db.scalar(
        select(Tenant.tenant_id).where(
            Tenant.email_domain == domain,
            Tenant.is_deleted == False,  # noqa: E712
        )
    )
    if existing:
        msg = f"An organisation is already registered with @{domain}. Please contact your organisation admin to get access."
        _domain_cache[domain] = (False, msg, time.monotonic())
        return DomainCheckResponse(available=False, domain=domain, message=msg)

    _domain_cache[domain] = (True, "", time.monotonic())
    return DomainCheckResponse(available=True, domain=domain, message="")


@router.post("/tenant/signup/registered", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def signup_registered_provider(
    request: Request,
    payload: TenantSignupRegistered,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Onboards a Registered NDIS Provider."""
    tenant = await create_tenant_hierarchy(db, payload, is_registered=True, request=request)
    await cache_delete("plans:all")
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
