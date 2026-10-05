"""Users router.

AppUser lives in ndis_common (get_db).
Branch, UserRole, and AuditLog live in the per-tenant schema (get_tenant_session).
Both dependencies are injected per-request.
"""
import logging
import secrets
import smtplib
import string
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import resend
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import (
    get_current_user,
    get_password_hash, get_password_hash_async,
    verify_password, verify_password_async,
)
from app.database import get_db, get_tenant_session
from app.models import AppUser, AuditLog, Branch, Role, RolePermission, UserRole
from app.models.staff_profile import StaffProfile
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas import AppUserCreate, AppUserResponse, AppUserUpdate, MessageResponse
from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleResponse

router = APIRouter(tags=["Users"])

TTL_USER = 300

# ── Temp-password generation ───────────────────────────────────────────────────

def _generate_temp_password() -> str:
    """Return a 12-character cryptographically random temporary password.

    Guarantees at least one uppercase, one lowercase, one digit, and one symbol.
    Uses secrets.choice (backed by os.urandom) — never logs or returns plain text
    after the caller has hashed it.
    """
    upper  = secrets.choice(string.ascii_uppercase)
    lower  = secrets.choice(string.ascii_lowercase)
    digit  = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%^&*")
    rest   = [secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(8)]
    pool   = list(upper + lower + digit + symbol) + rest
    secrets.SystemRandom().shuffle(pool)
    return "".join(pool)


# ── Credentials email ─────────────────────────────────────────────────────────

def _credentials_email_html(first_name: str, email: str, temp_password: str, login_url: str) -> str:
    """Welcome email with login credentials. Never called after temp_password has been discarded."""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:32px 24px">
      <div style="margin-bottom:24px">
        <span style="font-size:18px;font-weight:700;color:#1e3a5f">NDIS Manager</span>
      </div>
      <h2 style="font-size:22px;color:#1e293b;margin-bottom:8px">Welcome, {first_name}!</h2>
      <p style="color:#64748b;font-size:14px;margin-bottom:24px">
        An account has been created for you on NDIS Manager. Use the credentials below to log in.
        You will be prompted to set a new password on your first login.
      </p>
      <div style="background:#f8fafc;border-radius:12px;padding:20px 24px;margin-bottom:24px;border:1px solid #e2e8f0">
        <div style="margin-bottom:12px">
          <span style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em">Email</span><br>
          <span style="font-size:15px;color:#1e293b;font-family:monospace">{email}</span>
        </div>
        <div>
          <span style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em">Temporary Password</span><br>
          <span style="font-size:15px;color:#1e40af;font-family:monospace;font-weight:700;letter-spacing:2px">{temp_password}</span>
        </div>
      </div>
      <a href="{login_url}" style="display:inline-block;background:#4a2080;color:#fff;font-size:14px;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;margin-bottom:24px">
        Log in to NDIS Manager →
      </a>
      <p style="color:#94a3b8;font-size:12px">
        For security, change your password immediately after logging in.
        If you did not expect this email, please contact your administrator.
      </p>
    </div>
    """


def _send_credentials_email(to_email: str, first_name: str, temp_password: str, login_url: str) -> None:
    """Send welcome credentials email. Runs in a background task.

    Tries Resend → SMTP → falls back to logging (dev mode).
    The temp_password is only used here to build the email; it is never stored or logged.
    """
    from app.core.config import settings  # local import avoids circular at module load

    resend_key = settings.RESEND_API_KEY
    smtp_user  = settings.SMTP_USER
    smtp_pass  = settings.SMTP_PASS
    smtp_host  = settings.SMTP_HOST
    smtp_port  = settings.SMTP_PORT
    from_name  = settings.EMAIL_FROM_NAME
    dev_target = settings.DEV_REDIRECT_EMAIL

    target   = dev_target if dev_target else to_email
    subject  = "Your NDIS Manager account credentials"
    html_body = _credentials_email_html(first_name, to_email, temp_password, login_url)

    # ── Try Resend ────────────────────────────────────────────────────────────
    if resend_key:
        try:
            resend.api_key = resend_key
            resend.Emails.send({
                "from": f"{from_name} <onboarding@resend.dev>",
                "to": [target],
                "subject": subject,
                "html": html_body,
            })
            logger.info("Credentials email sent via Resend to %s", to_email)
            return
        except Exception as exc:
            logger.warning("Resend failed for credentials email to %s: %s", to_email, exc)

    # ── Try SMTP ──────────────────────────────────────────────────────────────
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{from_name} <{smtp_user}>"
            msg["To"]      = target
            msg.attach(MIMEText(html_body, "html"))
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, target, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.ehlo(); server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, target, msg.as_string())
            logger.info("Credentials email sent via SMTP to %s", to_email)
            return
        except Exception as exc:
            logger.warning("SMTP failed for credentials email to %s: %s", to_email, exc)

    # ── Dev fallback — log that email was NOT sent (never log password) ───────
    logger.warning(
        "Could not deliver credentials email to %s — no email service configured. "
        "Admin must share credentials manually.",
        to_email,
    )


@router.get("/tenant/{tenant_id}/users", response_model=List[AppUserResponse])
async def list_users(
    tenant_id: int,
    branch_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> List[AppUserResponse]:
    verify_tenant_access(tenant_id, current_user)

    stmt = select(AppUser).where(
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    )
    if branch_id is not None:
        stmt = stmt.where(AppUser.branch_id == branch_id)
    if is_active is not None:
        stmt = stmt.where(AppUser.is_active == is_active)
    stmt = stmt.order_by(AppUser.first_name, AppUser.last_name)
    users = (await db.scalars(stmt)).all()

    # Batch-fetch all role assignments for these users in one query
    user_ids = [u.user_id for u in users]
    role_rows = (await tenant_db.scalars(
        select(UserRole)
        .where(UserRole.user_id.in_(user_ids), UserRole.is_active == True)  # noqa: E712
        .options(selectinload(UserRole.role))
    )).all() if user_ids else []

    from collections import defaultdict
    roles_by_user: Dict[str, List] = defaultdict(list)
    for ur in role_rows:
        if ur.role and not ur.role.is_deleted:
            roles_by_user[str(ur.user_id)].append(ur.role)

    # Fetch all tenant roles for job_title fallback matching
    all_tenant_roles = (await tenant_db.scalars(
        select(Role).where(Role.is_active == True, Role.is_deleted == False)  # noqa: E712
    )).all()
    role_by_name: Dict[str, Any] = {r.role_name.strip().lower(): r for r in all_tenant_roles}

    # Backfill user_role records for users whose job_title matches a role
    # but have no formal user_role record yet (e.g. created before role seeding)
    backfilled = False
    for u in users:
        if roles_by_user.get(str(u.user_id)):
            continue  # already has formal assignments
        if not u.job_title:
            continue
        matched = role_by_name.get(u.job_title.strip().lower())
        if matched:
            tenant_db.add(UserRole(
                user_id=u.user_id,
                role_id=matched.role_id,
                assigned_by=current_user["user_id"],
                is_active=True,
            ))
            roles_by_user[str(u.user_id)].append(matched)
            backfilled = True
    if backfilled:
        try:
            await tenant_db.commit()
        except Exception:
            await tenant_db.rollback()

    result = []
    for u in users:
        resp = AppUserResponse.model_validate(u)
        assigned = roles_by_user.get(str(u.user_id), [])
        resp.role_ids   = [r.role_id   for r in assigned]
        resp.role_names = [r.role_name for r in assigned]
        result.append(resp)
    return result


@router.post("/tenant/{tenant_id}/users", response_model=AppUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    tenant_id: int,
    payload: AppUserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> AppUserResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(tenant_db, current_user, "users:create")

    # Uniqueness check — DB constraint covers ALL rows (including soft-deleted),
    # so we must check without the is_deleted filter to return a clean 409
    # instead of letting the DB raise an IntegrityError.
    existing = await db.scalar(select(AppUser).where(
        AppUser.tenant_id == tenant_id,
        AppUser.email == payload.email.lower().strip(),
    ))
    if existing:
        msg = (
            f"A user with email '{payload.email}' already exists in this organisation."
            if not existing.is_deleted
            else f"Email '{payload.email}' belongs to a previously deleted account and cannot be reused."
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)

    # Validate branch in tenant schema (optional — users can exist without a branch)
    if payload.branch_id is not None:
        branch = await tenant_db.scalar(select(Branch).where(
            Branch.branch_id == payload.branch_id,
            Branch.is_deleted == False,  # noqa: E712
        ))
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected branch not found in this tenant's schema",
            )

    # Generate or use provided password — always hash immediately, never store plain text
    temp_password = payload.password or _generate_temp_password()

    # Create AppUser in ndis_common
    user_id = str(uuid.uuid4())
    user = AppUser(
        user_id=user_id,
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        email=payload.email.lower().strip(),
        password_hash=await get_password_hash_async(temp_password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        mobile=payload.mobile,
        job_title=payload.job_title,
        is_tenant_admin=payload.is_tenant_admin,
        is_active=payload.is_active,
        is_deleted=False,
        must_change_password=True,
        created_by=current_user["user_id"],
    )
    db.add(user)
    await db.flush()

    # Assign roles in tenant schema
    if payload.role_ids:
        for r_id in payload.role_ids:
            tenant_db.add(UserRole(
                user_id=user_id, role_id=r_id,
                assigned_by=current_user["user_id"],
                is_active=True,
            ))

    # Audit log in tenant schema
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="CREATE",
        table_name="app_user",
        record_id=user_id,
        new_values={
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "branch_id": user.branch_id,
            "is_tenant_admin": user.is_tenant_admin,
        },
        request=request,
    )

    await db.commit()
    await tenant_db.commit()
    await db.refresh(user)

    # Auto-create a linked StaffProfile in the tenant schema so the new user
    # immediately appears in Staff Management without any extra step.
    try:
        staff = StaffProfile(
            staff_id=user_id,          # use same ID as user for easy lookup
            tenant_id=tenant_id,
            user_id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            work_email=user.email,
            status="Active",
            created_by=current_user["user_id"],
        )
        tenant_db.add(staff)
        await tenant_db.commit()
    except Exception as _exc:
        logger.warning("Could not auto-create StaffProfile for user %s: %s", user_id, _exc)
        await tenant_db.rollback()

    # Send credentials email in background — temp_password passed directly, never stored
    import urllib.parse as _urlparse
    from app.core.config import settings as _settings
    # Link goes to the standalone set-password page (served by FastAPI) so users
    # land on a clean password-change form without having to log in first.
    login_url = (
        _settings.BACKEND_URL.rstrip("/") + "/api/v1/auth/set-password?email="
        + _urlparse.quote(user.email, safe="")
    )
    background_tasks.add_task(
        _send_credentials_email,
        user.email,
        user.first_name,
        temp_password,
        login_url,
    )
    # temp_password goes out of scope here — only lives long enough to be hashed + emailed

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
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
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
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> AppUserResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(tenant_db, current_user, "users:edit")

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Validate new branch if being changed
    if payload.branch_id is not None:
        branch = await tenant_db.scalar(select(Branch).where(
            Branch.branch_id == payload.branch_id,
            Branch.is_deleted == False,  # noqa: E712
        ))
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected branch not found in this tenant's schema",
            )

    old_values = {
        "first_name": user.first_name, "last_name": user.last_name,
        "branch_id": user.branch_id, "mobile": user.mobile,
        "job_title": user.job_title, "is_active": user.is_active,
    }
    # Use model_fields_set to distinguish "not sent" (skip) from "sent as null" (clear)
    fs = payload.model_fields_set
    if "email" in fs and payload.email:
        new_email = str(payload.email).lower().strip()
        if new_email != user.email:
            conflict = await db.scalar(select(AppUser).where(
                AppUser.tenant_id == tenant_id,
                AppUser.email == new_email,
                AppUser.is_deleted == False,  # noqa: E712
                AppUser.user_id != user_id,
            ))
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{new_email}' is already in use by another user.",
                )
            user.email = new_email
    if "branch_id" in fs and payload.branch_id is not None:
        user.branch_id = payload.branch_id
    if "first_name" in fs and payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if "last_name" in fs and payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if "mobile" in fs:
        user.mobile = payload.mobile  # None clears it; a string sets it
    if "job_title" in fs:
        user.job_title = payload.job_title  # None clears it; a string sets it
    if "is_active" in fs and payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = await get_password_hash_async(payload.password)
        user.password_changed_at = datetime.now(timezone.utc)
    user.updated_by = current_user["user_id"]

    # Update role assignments if role_ids was explicitly sent
    if "role_ids" in fs and payload.role_ids is not None:
        # Delete existing role assignments for this user
        existing_roles = await tenant_db.scalars(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        for ur in existing_roles:
            await tenant_db.delete(ur)
        await tenant_db.flush()
        # Insert new role assignments
        for r_id in payload.role_ids:
            tenant_db.add(UserRole(
                user_id=user_id, role_id=r_id,
                assigned_by=current_user["user_id"],
                is_active=True,
            ))

    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="UPDATE",
        table_name="app_user",
        record_id=user_id,
        old_values=old_values,
        new_values=payload.model_dump(exclude={"password"}, exclude_unset=True),
        request=request,
    )
    # Sync name/email changes to the linked StaffProfile
    staff = await tenant_db.scalar(
        select(StaffProfile).where(StaffProfile.user_id == user_id, StaffProfile.is_deleted == False)  # noqa: E712
    )
    if staff:
        fs = payload.model_fields_set
        if "first_name" in fs and payload.first_name:
            staff.first_name = payload.first_name.strip()
        if "last_name" in fs and payload.last_name:
            staff.last_name = payload.last_name.strip()
        if "email" in fs and payload.email:
            staff.work_email = str(payload.email).lower().strip()
        if "is_active" in fs and payload.is_active is not None:
            staff.status = "Active" if payload.is_active else "Inactive"
        staff.updated_by = current_user["user_id"]

    await db.commit()
    await tenant_db.commit()
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
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(tenant_db, current_user, "users:delete")

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the primary tenant administrator",
        )

    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False

    # Soft-delete linked StaffProfile so it disappears from Staff Management
    staff = await tenant_db.scalar(
        select(StaffProfile).where(StaffProfile.user_id == user_id, StaffProfile.is_deleted == False)  # noqa: E712
    )
    if staff:
        staff.is_deleted = True
        staff.deleted_at = datetime.now(timezone.utc)
        staff.updated_by = current_user["user_id"]

    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="SOFT_DELETE",
        table_name="app_user",
        record_id=user_id,
        request=request,
    )
    await db.commit()
    await tenant_db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return MessageResponse(message=f"User {user.email} has been deactivated and deleted")


@router.post(
    "/tenant/{tenant_id}/users/{user_id}/roles/{role_id}",
    response_model=MessageResponse,
)
async def assign_role_to_user(
    tenant_id: int,
    user_id: str,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    # Verify user exists in ndis_common
    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify role exists in tenant schema
    role = await tenant_db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    existing = await tenant_db.scalar(select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    ))
    if existing:
        return MessageResponse(message=f"User already has role {role.role_name}")

    tenant_db.add(UserRole(
        user_id=user_id, role_id=role_id,
        assigned_by=current_user["user_id"],
        is_active=True,
    ))
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="ASSIGN_ROLE",
        table_name="user_role",
        record_id=f"{user_id}:{role_id}",
        request=request,
    )
    await tenant_db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return MessageResponse(message=f"Role {role.role_name} assigned to user {user.email}")



# ── Activate / Deactivate ──────────────────────────────────────────────────────

@router.patch("/tenant/{tenant_id}/users/{user_id}/activate", response_model=AppUserResponse)
async def activate_user(
    tenant_id: int,
    user_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> AppUserResponse:
    """Re-activate a deactivated user."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(tenant_db, current_user, "users:edit")
    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = True
    user.updated_by = current_user["user_id"]
    user.updated_at = datetime.now(timezone.utc)
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="ACTIVATE_USER",
        table_name="app_user",
        record_id=user_id,
        new_values={"is_active": True},
        request=request,
    )
    await db.commit()
    await tenant_db.commit()
    await db.refresh(user)
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")

    roles = (await tenant_db.scalars(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.is_active == True)  # noqa
        .options(selectinload(UserRole.role))
    )).all()
    resp = AppUserResponse.model_validate(user)
    resp.role_ids = [r.role_id for r in roles if r.role and not r.role.is_deleted]
    resp.role_names = [r.role.role_name for r in roles if r.role and not r.role.is_deleted]
    return resp


@router.patch("/tenant/{tenant_id}/users/{user_id}/deactivate", response_model=AppUserResponse)
async def deactivate_user(
    tenant_id: int,
    user_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> AppUserResponse:
    """Deactivate a user (keeps record, blocks login)."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(tenant_db, current_user, "users:edit")
    if current_user["user_id"] == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate yourself")

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    user.updated_by = current_user["user_id"]
    user.updated_at = datetime.now(timezone.utc)
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="DEACTIVATE_USER",
        table_name="app_user",
        record_id=user_id,
        new_values={"is_active": False},
        request=request,
    )
    await db.commit()
    await tenant_db.commit()
    await db.refresh(user)
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")

    roles = (await tenant_db.scalars(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.is_active == True)  # noqa
        .options(selectinload(UserRole.role))
    )).all()
    resp = AppUserResponse.model_validate(user)
    resp.role_ids = [r.role_id for r in roles if r.role and not r.role.is_deleted]
    resp.role_names = [r.role.role_name for r in roles if r.role and not r.role.is_deleted]
    return resp


# ── Resend Invitation ──────────────────────────────────────────────────────────

@router.post("/tenant/{tenant_id}/users/{user_id}/resend-invitation", response_model=MessageResponse)
async def resend_invitation(
    tenant_id: int,
    user_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Generate a new temporary password and resend login credentials to the user."""
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from app.core.config import settings
    temp_password = _generate_temp_password()
    user.password_hash = await get_password_hash_async(temp_password)
    user.must_change_password = True
    user.updated_by = current_user["user_id"]
    user.updated_at = datetime.now(timezone.utc)

    login_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173") + "/login"
    background_tasks.add_task(
        _send_credentials_email,
        to_email=user.email,
        first_name=user.first_name,
        temp_password=temp_password,
        login_url=login_url,
    )
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="RESEND_INVITATION",
        table_name="app_user",
        record_id=user_id,
        new_values={"resent_by": current_user["user_id"]},
        request=request,
    )
    await db.commit()
    await tenant_db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    return MessageResponse(message=f"Invitation resent to {user.email}")


# ── User Activity ──────────────────────────────────────────────────────────────

@router.get("/tenant/{tenant_id}/users/{user_id}/activity")
async def get_user_activity(
    tenant_id: int,
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> List[Dict]:
    """Return the most recent audit log entries for a specific user."""
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = (await tenant_db.scalars(
        select(AuditLog)
        .where(AuditLog.record_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )).all()

    return [
        {
            "audit_id": r.audit_id,
            "user_id": r.user_id,
            "action": r.action,
            "table_name": r.table_name,
            "record_id": r.record_id,
            "old_values": r.old_values,
            "new_values": r.new_values,
            "ip_address": r.ip_address,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# ── User Effective Permissions ─────────────────────────────────────────────────

@router.get(
    "/tenant/{tenant_id}/users/{user_id}/permissions",
    response_model=List[PermissionResponse],
)
async def get_user_effective_permissions(
    tenant_id: int,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> List[PermissionResponse]:
    """Return the union of all permissions from all active roles assigned to a user."""
    verify_tenant_access(tenant_id, current_user)

    # Validate user exists in ndis_common
    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    key = f"tenant:{tenant_id}:user:{user_id}:permissions"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    # Fetch all active user-role mappings, eagerly loading role → role_permissions → permission
    user_roles = (await tenant_db.scalars(
        select(UserRole)
        .where(UserRole.user_id == user_id, UserRole.is_active == True)  # noqa: E712
        .options(
            selectinload(UserRole.role).selectinload(Role.role_permissions).selectinload(
                RolePermission.permission
            )
        )
    )).all()

    # Aggregate unique, granted, active permissions across all roles
    seen: set[int] = set()
    perms: list[PermissionResponse] = []
    for ur in user_roles:
        if ur.role is None:
            continue
        for rp in ur.role.role_permissions:
            if not rp.granted:
                continue
            if rp.permission is None:
                continue
            if not rp.permission.is_active:
                continue
            if rp.permission.permission_id in seen:
                continue
            seen.add(rp.permission.permission_id)
            perms.append(PermissionResponse.model_validate(rp.permission))

    result = [p.model_dump(mode="json") for p in perms]
    await cache_set(key, result, ttl=300)
    return result


# ── User Roles Management ──────────────────────────────────────────────────────

@router.get(
    "/tenant/{tenant_id}/users/{user_id}/roles",
    response_model=List[RoleResponse],
)
async def list_user_roles(
    tenant_id: int,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> List[RoleResponse]:
    """List all active roles assigned to a user."""
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_roles = (await tenant_db.scalars(
        select(UserRole)
        .where(UserRole.user_id == user_id, UserRole.is_active == True)  # noqa: E712
        .options(selectinload(UserRole.role))
    )).all()

    return [
        RoleResponse.model_validate(ur.role)
        for ur in user_roles
        if ur.role is not None and not ur.role.is_deleted
    ]


@router.delete(
    "/tenant/{tenant_id}/users/{user_id}/roles/{role_id}",
    response_model=MessageResponse,
)
async def remove_role_from_user(
    tenant_id: int,
    user_id: str,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Remove a role from a user."""
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = await tenant_db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user_role = await tenant_db.scalar(select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    ))
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have this role assigned",
        )

    await tenant_db.delete(user_role)
    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="REMOVE_ROLE",
        table_name="user_role",
        record_id=f"{user_id}:{role_id}",
        old_values={"user_id": user_id, "role_id": role_id},
        request=request,
    )
    await tenant_db.commit()
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}")
    await cache_delete(f"tenant:{tenant_id}:user:{user_id}:permissions")
    return MessageResponse(message=f"Role '{role.role_name}' removed from user {user.email}")


# ── User Self-Service ──────────────────────────────────────────────────────────

@router.post(
    "/tenant/{tenant_id}/users/{user_id}/change-password",
    response_model=MessageResponse,
)
async def change_user_password(
    tenant_id: int,
    user_id: str,
    payload: dict,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Change a user's password. Requires current_password for self-service; admins can omit it."""
    verify_tenant_access(tenant_id, current_user)

    user = await db.scalar(select(AppUser).where(
        AppUser.user_id == user_id,
        AppUser.tenant_id == tenant_id,
        AppUser.is_deleted == False,  # noqa: E712
    ))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Non-admins must provide their current password
    is_self = current_user["user_id"] == user_id
    is_admin = current_user.get("is_tenant_admin", False)

    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="new_password must be at least 8 characters",
        )

    if is_self and not is_admin:
        if not current_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="current_password is required for self-service password change",
            )
        if not await verify_password_async(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

    user.password_hash = await get_password_hash_async(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.updated_by = current_user["user_id"]

    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="CHANGE_PASSWORD",
        table_name="app_user",
        record_id=user_id,
        new_values={"changed_by": current_user["user_id"]},
        request=request,
    )
    await db.commit()
    await tenant_db.commit()
    return MessageResponse(message="Password changed successfully")
