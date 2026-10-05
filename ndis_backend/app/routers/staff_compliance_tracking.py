"""Staff Compliance Tracking router — features 3.1–3.6."""
from __future__ import annotations
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_tenant_session, get_db
from app.core.security import get_current_user
from app.models import AppUser
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_compliance_tracking import (
    ComplianceItemCreate,
    ComplianceItemUpdate,
    ComplianceItemResponse,
    ComplianceAuditResponse,
)

router = APIRouter(tags=["Staff — Compliance Tracking"])
BASE   = "/tenant/{tenant_id}/staff"


# ── helpers ──────────────────────────────────────────────────────────────────

def _auto_status(expiry_date: date | None) -> str:
    """Derive status from expiry date."""
    if expiry_date is None:
        return "Current"
    today = date.today()
    if expiry_date < today:
        return "Expired"
    if (expiry_date - today).days <= 90:
        return "Due soon"
    return "Current"


async def _audit(db: AsyncSession, schema: str, tenant_id: str, staff_id: str,
                 item_id: str, action_type: str, description: str,
                 prev_status: str | None, new_status: str | None,
                 user_name: str, user_id: str | None = None) -> None:
    await db.execute(
        text(f"""
            INSERT INTO [{schema}].[staff_compliance_audit]
              (audit_id, tenant_id, staff_id, compliance_item_id,
               action_type, action_description, previous_status, new_status,
               changed_by_user_id, changed_by_name)
            VALUES
              (:aid, :tid, :sid, :iid,
               :at, :desc, :ps, :ns, :uid, :name)
        """),
        dict(aid=str(uuid.uuid4()), tid=tenant_id, sid=staff_id, iid=item_id,
             at=action_type, desc=description, ps=prev_status, ns=new_status,
             uid=user_id, name=user_name)
    )


async def _resolve_user_name(common_db: AsyncSession, user_id: str | None) -> str:
    """Best-effort lookup of a human-readable name for the audit trail.

    current_user is a plain dict (user_id/tenant_id/schema_name only — see
    get_current_user), so there's no name to read off it directly; look the
    user up in the shared ndis_common.app_user table instead, same as the
    generic Activity log does.
    """
    if not user_id:
        return "System"
    try:
        from sqlalchemy import select
        row = await common_db.scalar(select(AppUser).where(AppUser.user_id == user_id))
        if row:
            full_name = f"{row.first_name} {row.last_name}".strip()
            return full_name or row.email or user_id
    except Exception:
        pass
    return user_id


# ── 3.1/3.2  List & create compliance items ──────────────────────────────────

@router.get(BASE + "/{staff_id}/compliance-items", response_model=List[ComplianceItemResponse])
async def list_compliance_items(
    tenant_id: str, staff_id: str,
    db: AsyncSession = Depends(get_tenant_session),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:view")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"

    # 1. Manual compliance items
    rows = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE staff_id=:sid AND tenant_id=:tid ORDER BY requirement_name"),
        {"sid": staff_id, "tid": tenant_id}
    )
    manual_items = [ComplianceItemResponse(**dict(r._mapping), source="manual") for r in rows.fetchall()]

    # 2. Auto-sync: certifications with expiry dates
    # LEFT JOIN so certs work even if certification_id isn't in the master catalogue.
    # Falls back to using the certification_id code as the display name.
    cert_rows = await db.execute(
        text(f"""
            SELECT
                sc.staff_certification_id                       AS compliance_item_id,
                CAST(:tid AS NVARCHAR(50))                      AS tenant_id,
                sc.staff_id,
                COALESCE(c.certification_name, sc.certification_id) AS requirement_name,
                'Certification'                                 AS category,
                'Auto'                                          AS requirement_type,
                sc.expiry_date,
                sc.created_at,
                sc.updated_at,
                'certification'                                 AS source
            FROM [{schema}].[staff_certification] sc
            LEFT JOIN [ndis_common].[certification] c
              ON sc.certification_id = c.certification_id
            WHERE sc.staff_id = :sid
              AND sc.is_deleted = 0
              AND sc.expiry_date IS NOT NULL
        """),
        {"sid": staff_id, "tid": tenant_id}
    )
    cert_items = []
    for r in cert_rows.fetchall():
        d = dict(r._mapping)
        exp = d.get("expiry_date")
        d["status"] = _auto_status(exp) if exp else "Current"
        d["is_mandatory"] = True
        cert_items.append(ComplianceItemResponse(**d))

    # 3. Auto-sync: qualifications with expiry dates
    # LEFT JOIN + correct column name (qualification_type, not qualification_name).
    # Skipped if expiry_date column hasn't been added by migration yet.
    qual_col_check = await db.execute(
        text("""
            SELECT COUNT(1) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'staff_qualification'
            AND COLUMN_NAME = 'expiry_date'
        """),
        {"schema": schema}
    )
    qual_has_expiry = (qual_col_check.scalar() or 0) > 0
    qual_items = []
    if qual_has_expiry:
        qual_rows = await db.execute(
            text(f"""
                SELECT
                    sq.staff_qualification_id                           AS compliance_item_id,
                    CAST(:tid AS NVARCHAR(50))                          AS tenant_id,
                    sq.staff_id,
                    COALESCE(q.qualification_type, sq.qualification_id) AS requirement_name,
                    'Qualification'                                     AS category,
                    'Auto'                                              AS requirement_type,
                    sq.expiry_date,
                    sq.created_at,
                    sq.updated_at,
                    'qualification'                                     AS source
                FROM [{schema}].[staff_qualification] sq
                LEFT JOIN [ndis_common].[qualification] q
                  ON sq.qualification_id = q.qualification_id
                WHERE sq.staff_id = :sid
                  AND sq.is_deleted = 0
                  AND sq.expiry_date IS NOT NULL
            """),
            {"sid": staff_id, "tid": tenant_id}
        )
        for r in qual_rows.fetchall():
            d = dict(r._mapping)
            exp = d.get("expiry_date")
            d["status"] = _auto_status(exp) if exp else "Current"
            d["is_mandatory"] = True
            qual_items.append(ComplianceItemResponse(**d))

    # Merge: manual first, then auto-synced (sorted by name)
    auto_items = sorted(qual_items + cert_items, key=lambda x: x.requirement_name)
    return manual_items + auto_items


@router.post(BASE + "/{staff_id}/compliance-items", response_model=ComplianceItemResponse, status_code=201)
async def create_compliance_item(
    tenant_id: str, staff_id: str, body: ComplianceItemCreate,
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:edit")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"
    iid    = str(uuid.uuid4())
    auto_s = _auto_status(body.expiry_date)
    effective_status = body.status if body.status and body.status != "Pending" else auto_s

    await db.execute(
        text(f"""
            INSERT INTO [{schema}].[staff_compliance_item]
              (compliance_item_id, tenant_id, staff_id, requirement_name,
               reference_no, category, requirement_type,
               completed_date, expiry_date, status, is_mandatory,
               reminder_days_before, notes)
            VALUES
              (:iid,:tid,:sid,:name,:ref,:cat,:rtype,
               :cd,:ed,:st,:mand,:rdb,:notes)
        """),
        dict(iid=iid, tid=tenant_id, sid=staff_id,
             name=body.requirement_name, ref=body.reference_no,
             cat=body.category, rtype=body.requirement_type,
             cd=body.completed_date, ed=body.expiry_date,
             st=effective_status, mand=body.is_mandatory,
             rdb=body.reminder_days_before, notes=body.notes)
    )
    user_name = await _resolve_user_name(common_db, current_user.get("user_id"))
    await _audit(db, schema, tenant_id, staff_id, iid,
                 "created", f"Compliance requirement '{body.requirement_name}' added",
                 None, effective_status, user_name, current_user.get("user_id"))
    await log_audit(
        db, current_user.get("user_id"), "CREATE", "staff_compliance_item", iid,
        new_values={"requirement_name": body.requirement_name},
    )
    await db.commit()
    row = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id"), {"id": iid}
    )
    return ComplianceItemResponse(**dict(row.fetchone()._mapping))


# ── 3.2/3.3  Get / Update (status + expiry) ──────────────────────────────────

@router.get(BASE + "/{staff_id}/compliance-items/{item_id}", response_model=ComplianceItemResponse)
async def get_compliance_item(
    tenant_id: str, staff_id: str, item_id: str,
    db: AsyncSession = Depends(get_tenant_session),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:view")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"
    row = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id AND staff_id=:sid"),
        {"id": item_id, "sid": staff_id}
    )
    r = row.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    return ComplianceItemResponse(**dict(r._mapping))


@router.patch(BASE + "/{staff_id}/compliance-items/{item_id}", response_model=ComplianceItemResponse)
async def update_compliance_item(
    tenant_id: str, staff_id: str, item_id: str, body: ComplianceItemUpdate,
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:edit")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"
    existing = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id AND staff_id=:sid"),
        {"id": item_id, "sid": staff_id}
    )
    ex = existing.fetchone()
    if not ex:
        raise HTTPException(status_code=404, detail="Compliance item not found")

    prev_status = ex._mapping.get("status")
    updates = body.model_dump(exclude_none=True)

    # Auto-recalculate status if expiry_date changes and status not explicitly set
    if "expiry_date" in updates and "status" not in updates:
        updates["status"] = _auto_status(updates["expiry_date"])

    # Keep a clean copy of the field changes for the audit log before the
    # SQL-only "id" key gets mixed into `updates` below.
    changed_fields = dict(updates)

    if updates:
        sets = ", ".join(f"{k}=:{k}" for k in updates)
        updates["id"] = item_id
        await db.execute(
            text(f"UPDATE [{schema}].[staff_compliance_item] SET {sets}, updated_at=GETDATE() WHERE compliance_item_id=:id"),
            updates
        )

    new_status = changed_fields.get("status", prev_status)
    user_name = await _resolve_user_name(common_db, current_user.get("user_id"))
    await _audit(db, schema, tenant_id, staff_id, item_id,
                 "updated", f"Compliance requirement updated",
                 prev_status, new_status, user_name, current_user.get("user_id"))
    await log_audit(
        db, current_user.get("user_id"), "UPDATE", "staff_compliance_item", item_id,
        new_values=changed_fields,
    )
    await db.commit()
    row = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id"), {"id": item_id}
    )
    return ComplianceItemResponse(**dict(row.fetchone()._mapping))


@router.delete(BASE + "/{staff_id}/compliance-items/{item_id}", status_code=204)
async def delete_compliance_item(
    tenant_id: str, staff_id: str, item_id: str,
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:edit")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"

    existing = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id AND staff_id=:sid"),
        {"id": item_id, "sid": staff_id}
    )
    ex = existing.fetchone()
    requirement_name = ex._mapping.get("requirement_name") if ex else None
    prev_status = ex._mapping.get("status") if ex else None

    await db.execute(
        text(f"DELETE FROM [{schema}].[staff_compliance_item] WHERE compliance_item_id=:id AND staff_id=:sid"),
        {"id": item_id, "sid": staff_id}
    )

    user_name = await _resolve_user_name(common_db, current_user.get("user_id"))
    await _audit(db, schema, tenant_id, staff_id, item_id,
                 "deleted",
                 f"Compliance requirement '{requirement_name}' removed" if requirement_name else "Compliance requirement removed",
                 prev_status, None, user_name, current_user.get("user_id"))
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_compliance_item", item_id)
    await db.commit()


# ── 3.5  Send reminder ────────────────────────────────────────────────────────

@router.post(BASE + "/{staff_id}/compliance-items/{item_id}/remind", status_code=200)
async def send_compliance_reminder(
    tenant_id: str, staff_id: str, item_id: str,
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a reminder as sent (email integration wired externally)."""
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:edit")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"
    now = datetime.now(timezone.utc)
    await db.execute(
        text(f"UPDATE [{schema}].[staff_compliance_item] SET reminder_sent_at=:now WHERE compliance_item_id=:id"),
        {"now": now, "id": item_id}
    )
    user_name = await _resolve_user_name(common_db, current_user.get("user_id"))
    await _audit(db, schema, tenant_id, staff_id, item_id,
                 "reminder_sent", "Renewal reminder sent to staff member",
                 None, None, user_name, current_user.get("user_id"))
    await db.commit()
    return {"message": "Reminder sent"}


# ── 3.6  Audit trail ─────────────────────────────────────────────────────────

@router.get(BASE + "/{staff_id}/compliance-audit", response_model=List[ComplianceAuditResponse])
async def get_compliance_audit(
    tenant_id: str, staff_id: str,
    db: AsyncSession = Depends(get_tenant_session),
    current_user=Depends(get_current_user),
):
    verify_tenant_access(int(tenant_id), current_user)
    await require_permission(db, current_user, "staff:view")
    schema = current_user.get('schema_name') or f"tenant_{tenant_id.replace('-', '_')}"
    rows = await db.execute(
        text(f"SELECT * FROM [{schema}].[staff_compliance_audit] WHERE staff_id=:sid AND tenant_id=:tid ORDER BY created_at DESC"),
        {"sid": staff_id, "tid": tenant_id}
    )
    return [ComplianceAuditResponse(**dict(r._mapping)) for r in rows.fetchall()]
