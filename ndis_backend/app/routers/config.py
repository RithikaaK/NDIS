"""Tenant Configuration router — covers 8.1–8.7 (tenant-schema scoped)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session, get_db
from app.models import TenantConfig
from app.models.tenant_model import Tenant
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import TenantConfigResponse, TenantConfigUpdate

router = APIRouter(tags=["Tenant Configuration"])

TTL_CONFIG = 300

_DEFAULTS = dict(
    country="Australia", state=None,
    date_format="DD/MM/YYYY", time_format="24h", week_starts_on="Monday",
    timezone="Australia/Sydney",
    currency_code="AUD", enable_gst=True, gst_rate=10, enable_schads_award=True,
    invoice_prefix="INV", invoice_due_days=14, billing_frequency="Monthly",
    payment_terms=None, auto_invoice_enabled=False,
    default_funding_type="Agency Managed",
    notify_email_enabled=True, notify_sms_enabled=False, notify_inapp_enabled=True,
    notify_appointment_reminders=True, notify_plan_expiry_alerts=True,
    notify_overdue_payment_alerts=True, notify_budget_alerts=True,
    notify_reminder_hours_before=24,
    session_timeout_minutes=60, password_min_length=8,
    password_require_uppercase=True, password_require_numbers=True,
    password_require_symbols=False, max_login_attempts=5, mfa_enabled=False,
    enable_pace_integration=False, enable_proda_integration=False,
    integration_myob_enabled=False, integration_xero_enabled=False,
    integration_communication_provider=None, integration_payment_provider=None,
)


@router.get("/tenant/{tenant_id}/config", response_model=TenantConfigResponse)
async def get_tenant_config(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantConfigResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:config"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    config = await db.scalar(select(TenantConfig))
    if not config:
        config = TenantConfig(**_DEFAULTS)
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
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
) -> TenantConfigResponse:
    verify_tenant_access(tenant_id, current_user)

    config = await db.scalar(select(TenantConfig))
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant configuration not found")

    old_values = {c.name: getattr(config, c.name) for c in config.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        setattr(config, field, val)

    # If timezone changed, mirror it to ndis_common.tenant as well
    if "timezone" in update_data:
        tenant = await common_db.scalar(select(Tenant).where(Tenant.tenant_id == tenant_id))
        if tenant:
            tenant.timezone = update_data["timezone"]
            await common_db.commit()

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="UPDATE_CONFIG",
        table_name="tenant_config",
        record_id=str(config.config_id),
        old_values=old_values,
        new_values=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(config)
    await cache_delete(f"tenant:{tenant_id}:config")
    return TenantConfigResponse.model_validate(config)
