"""Audit Log query router — tenant-schema scoped."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session, get_db
from app.models import AuditLog, AppUser
from app.routers.helpers import verify_tenant_access

router = APIRouter(tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: int
    user_id: Optional[str] = None
    username: Optional[str] = None      # resolved full name or email
    action: str
    table_name: str
    record_id: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


@router.get("/tenant/{tenant_id}/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    tenant_id: int,
    # Filters
    user_id: Optional[str] = Query(None, description="Filter by user_id (UUID)"),
    action: Optional[str] = Query(None, description="Filter by action, e.g. CREATE, UPDATE"),
    table_name: Optional[str] = Query(None, description="Filter by table, e.g. app_user"),
    record_id: Optional[str] = Query(None, description="Filter by specific record_id"),
    from_dt: Optional[datetime] = Query(None, alias="from", description="Start datetime (ISO 8601)"),
    to_dt: Optional[datetime] = Query(None, alias="to", description="End datetime (ISO 8601)"),
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
) -> List[AuditLogResponse]:
    """Return audit log entries for this tenant's schema with optional filters and pagination."""
    verify_tenant_access(tenant_id, current_user)

    stmt = select(AuditLog)

    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action.upper())
    if table_name:
        stmt = stmt.where(AuditLog.table_name == table_name)
    if record_id:
        stmt = stmt.where(AuditLog.record_id == record_id)
    if from_dt:
        stmt = stmt.where(AuditLog.created_at >= from_dt)
    if to_dt:
        stmt = stmt.where(AuditLog.created_at <= to_dt)

    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    logs = (await db.scalars(stmt)).all()

    # Resolve user_ids → usernames from ndis_common.app_user
    user_id_list = list({log.user_id for log in logs if log.user_id})
    user_map: Dict[str, str] = {}
    if user_id_list:
        try:
            user_rows = (await common_db.scalars(
                select(AppUser).where(AppUser.user_id.in_(user_id_list))
            )).all()
            for u in user_rows:
                full_name = f"{u.first_name} {u.last_name}".strip()
                user_map[str(u.user_id)] = full_name or u.email
        except Exception:
            pass  # Degrade gracefully — username stays None, frontend falls back to user_id

    result = []
    for log in logs:
        data = AuditLogResponse.model_validate(log)
        data.username = user_map.get(str(log.user_id)) if log.user_id else None
        result.append(data)

    return result
