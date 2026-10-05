"""Authentication Router for NDIS Tenant Module."""
import json
import logging
import os
import random
import smtplib
import string
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token, get_current_user,
    get_password_hash, get_password_hash_async,
    verify_password, verify_password_async,
)
from app.core.tenant_schema import generate_schema_name
from app.database import get_db, get_tenant_db
from app.models import AppUser, AuditLog, Tenant
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas import (
    LoginRequest, TokenResponse,
    SendOtpRequest, VerifyOtpRequest,
    ResetPasswordRequest, MeResponse, MeUpdate, ChangePasswordRequest,
    ForcedChangePasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# ── In-memory OTP store: { email -> (otp_code, expires_at) } ─────────────────
# Dev-only: no persistence between restarts, no rate limiting.
# Replace with Redis + email service in production.
_otp_store: dict[str, tuple[str, datetime]] = {}
_OTP_TTL_MINUTES = 10

# ── Email config from settings (loaded from .env via pydantic-settings) ───────
_RESEND_API_KEY   = settings.RESEND_API_KEY
_SMTP_HOST        = settings.SMTP_HOST
_SMTP_PORT        = settings.SMTP_PORT
_SMTP_USER        = settings.SMTP_USER
_SMTP_PASS        = settings.SMTP_PASS
_EMAIL_FROM_NAME  = settings.EMAIL_FROM_NAME
_DEV_REDIRECT     = settings.DEV_REDIRECT_EMAIL  # all OTPs go here when set


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _otp_html(otp: str) -> str:
    """Shared HTML template for OTP emails."""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <div style="margin-bottom:24px">
        <span style="font-size:18px;font-weight:700;color:#1e3a5f">NDIS Manager</span>
      </div>
      <h2 style="font-size:22px;color:#1e293b;margin-bottom:8px">Your verification code</h2>
      <p style="color:#64748b;font-size:14px;margin-bottom:24px">
        Use the code below to verify your email address.
        It expires in {_OTP_TTL_MINUTES} minutes.
      </p>
      <div style="background:#f1f5f9;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
        <span style="font-size:36px;font-weight:700;letter-spacing:12px;color:#1e40af;font-family:monospace">{otp}</span>
      </div>
      <p style="color:#94a3b8;font-size:12px">
        If you did not request this code, you can safely ignore this email.
      </p>
    </div>
    """


def _send_via_resend(to_email: str, otp: str) -> bool:
    """Send OTP via Resend API. Returns True on success, False if not configured."""
    if not _RESEND_API_KEY:
        return False
    try:
        resend.api_key = _RESEND_API_KEY
        resend.Emails.send({
            "from": f"{_EMAIL_FROM_NAME} <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Your NDIS Manager verification code",
            "html": _otp_html(otp),
        })
        logger.info("OTP email sent via Resend to %s", to_email)
        return True
    except Exception as exc:
        logger.warning("Resend failed for %s: %s", to_email, exc)
        return False


def _send_via_smtp(to_email: str, otp: str) -> bool:
    """Send OTP via SMTP. Returns True on success, False if not configured."""
    print(f"[SMTP] user={_SMTP_USER!r} pass={'set' if _SMTP_PASS else 'EMPTY'} host={_SMTP_HOST}:{_SMTP_PORT}", flush=True)
    if not _SMTP_USER or not _SMTP_PASS:
        print("[SMTP] No credentials — skipping", flush=True)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your NDIS Manager verification code"
        msg["From"]    = f"{_EMAIL_FROM_NAME} <{_SMTP_USER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(_otp_html(otp), "html"))
        if _SMTP_PORT == 465:
            with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
                server.login(_SMTP_USER, _SMTP_PASS)
                server.sendmail(_SMTP_USER, to_email, msg.as_string())
        else:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(_SMTP_USER, _SMTP_PASS)
                server.sendmail(_SMTP_USER, to_email, msg.as_string())
        print(f"[SMTP] SUCCESS — sent to {to_email}", flush=True)
        logger.info("OTP email sent via SMTP to %s", to_email)
        return True
    except Exception as exc:
        print(f"[SMTP] FAILED: {exc}", flush=True)
        logger.warning("SMTP failed for %s: %s", to_email, exc)
        return False


def _send_direct(to_email: str, otp: str) -> bool:
    """Send OTP directly to the recipient's mail server via MX lookup.
    No relay, no API key, no credentials — pure SMTP.
    Requires port 25 outbound (open on most home/office networks).
    """
    try:
        import dns.resolver  # dnspython

        domain = to_email.split("@")[1]
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = sorted(mx_records, key=lambda r: r.preference)[0].exchange.to_text().rstrip(".")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your NDIS Manager verification code"
        msg["From"]    = f"{_EMAIL_FROM_NAME} <noreply@ndis-manager.com.au>"
        msg["To"]      = to_email
        msg.attach(MIMEText(_otp_html(otp), "html"))

        with smtplib.SMTP(mx_host, 25, timeout=15) as server:
            server.ehlo("ndis-manager.com.au")
            server.sendmail("noreply@ndis-manager.com.au", [to_email], msg.as_string())

        logger.info("OTP sent via direct MX delivery to %s (via %s)", to_email, mx_host)
        return True
    except Exception as exc:
        logger.warning("Direct MX delivery failed for %s: %s", to_email, exc)
        return False


def _send_otp_email(to_email: str, otp: str) -> bool:
    """Try Resend → SMTP → direct MX delivery. Falls back to dev_otp if all fail."""
    target = _DEV_REDIRECT if _DEV_REDIRECT else to_email
    if _DEV_REDIRECT and _DEV_REDIRECT != to_email:
        logger.info("DEV redirect: OTP for %s sent to %s instead", to_email, _DEV_REDIRECT)
    return _send_via_resend(target, otp) or _send_via_smtp(target, otp) or _send_direct(target, otp)


# ─── OTP: Send ────────────────────────────────────────────────────────────────

def _background_send_otp(email: str, otp: str) -> None:
    """Run in a background thread: attempt email delivery, log result."""
    sent = _send_otp_email(email, otp)
    if not sent:
        logger.info("[DEV OTP]  email=%s  otp=%s", email, otp)


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(payload: SendOtpRequest, background_tasks: BackgroundTasks):
    """Generate a 6-digit OTP, store it, and return immediately.

    Email delivery is dispatched as a background task so the API responds
    without blocking on SMTP — the user reaches the OTP screen in milliseconds
    while the email is sent concurrently.
    OTP is valid for 10 minutes.
    """
    email = payload.email.lower().strip()
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_OTP_TTL_MINUTES)
    _otp_store[email] = (otp, expires_at)

    # Dispatch email in the background — never blocks this response
    background_tasks.add_task(_background_send_otp, email, otp)

    response: dict = {
        "message": f"Verification code sent to {email}",
        "expires_in_minutes": _OTP_TTL_MINUTES,
        "dev_otp": otp,   # always returned — shown in the yellow dev-mode banner on the frontend
    }
    return response


# ─── OTP: Verify ──────────────────────────────────────────────────────────────

@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(payload: VerifyOtpRequest):
    """Validate a 6-digit OTP.  Consumes it on success (single-use)."""
    email = payload.email.lower().strip()
    record = _otp_store.get(email)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found for this email. Please request a new one.",
        )

    otp_code, expires_at = record

    if datetime.now(timezone.utc) > expires_at:
        del _otp_store[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one.",
        )

    if payload.otp != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again.",
        )

    # Consume OTP — single use
    del _otp_store[email]
    return {"message": "Email verified successfully", "verified": True}


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticates an application user.

    Supports two flows:
      A) Email-only (new default): look up user by email, then get their tenant.
      B) Legacy (tenant_code + email): look up tenant first, then user within it.

    In both cases the tenant schema_name is resolved from the DB (system-generated,
    never from the client) and embedded in the JWT — preventing cross-tenant access.
    """
    email = credentials.email.lower().strip()

    if credentials.tenant_code:
        # ── Flow B: legacy tenant_code flow ───────────────────────────────────
        tenant: Tenant | None = await db.scalar(
            select(Tenant).where(
                Tenant.tenant_code == credentials.tenant_code.strip(),
                Tenant.is_deleted == False,  # noqa: E712
            )
        )
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid organisation code or organisation not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user: AppUser | None = await db.scalar(
            select(AppUser).where(
                AppUser.tenant_id == tenant.tenant_id,
                AppUser.email == email,
                AppUser.is_deleted == False,  # noqa: E712
            )
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # ── Flow A: email-only — look up user, then get their tenant ──────────
        user = await db.scalar(
            select(AppUser).where(
                AppUser.email == email,
                AppUser.is_deleted == False,  # noqa: E712
            )
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not registered. Please sign up first.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        tenant = await db.scalar(
            select(Tenant).where(
                Tenant.tenant_id == user.tenant_id,
                Tenant.is_deleted == False,  # noqa: E712
            )
        )
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organisation not found or has been deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ── Shared: tenant active check ───────────────────────────────────────────
    if tenant.status.lower() in ("suspended", "inactive", "deactivated"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organisation account is currently {tenant.status}. Please contact support.",
        )

    # ── User active check ─────────────────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact your administrator.",
        )

    # ── Password verify ───────────────────────────────────────────────────────
    if not await verify_password_async(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Resolve schema_name from DB — never from the client ───────────────────
    schema_name: str = tenant.schema_name or generate_schema_name(
        tenant.tenant_code or str(tenant.tenant_id)
    )

    # ── Update last_login_at ──────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    await db.commit()
    await db.refresh(user)

    # ── Write audit log + auto-assign ADMIN role for tenant admins ───────────
    client_ip = request.client.host if request.client else None
    user_agent_str = request.headers.get("user-agent")
    try:
        async for tenant_db in get_tenant_db(schema_name):
            audit_entry = AuditLog(
                user_id=user.user_id,
                action="LOGIN_SUCCESS",
                table_name="app_user",
                record_id=user.user_id,
                old_values=None,
                new_values=json.dumps({"last_login_at": now.isoformat()}),
                ip_address=client_ip,
                user_agent=user_agent_str[:500] if user_agent_str else None,
            )
            tenant_db.add(audit_entry)

            # Auto-assign ADMIN role to is_tenant_admin users (idempotent)
            if user.is_tenant_admin:
                admin_role = await tenant_db.scalar(
                    select(Role).where(Role.role_code == "ADMIN")
                )
                if admin_role:
                    existing = await tenant_db.scalar(
                        select(UserRole).where(
                            UserRole.user_id == user.user_id,
                            UserRole.role_id == admin_role.role_id,
                        )
                    )
                    if not existing:
                        tenant_db.add(UserRole(
                            user_id=user.user_id,
                            role_id=admin_role.role_id,
                            assigned_by="SYSTEM",
                            is_active=True,
                        ))

            await tenant_db.commit()
    except Exception:
        logger.warning(
            "Failed to write audit log for user %s to schema %s", user.user_id, schema_name
        )

    # ── Issue JWT — schema_name embedded, resolved from DB ───────────────────
    token_payload = {
        "sub": user.user_id,
        "tenant_id": tenant.tenant_id,
        "schema_name": schema_name,
        "email": user.email,
        "is_tenant_admin": user.is_tenant_admin,
        "must_change_password": user.must_change_password,
    }
    access_token = create_access_token(data=token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        tenant_id=tenant.tenant_id,
        schema_name=schema_name,
        full_name=f"{user.first_name} {user.last_name}".strip(),
        is_tenant_admin=user.is_tenant_admin,
        must_change_password=user.must_change_password,
    )


# ─── Forgot Password: Reset ───────────────────────────────────────────────────

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and set a new password in one atomic call.

    The OTP must have been issued by /send-otp for the same email within the last 10 minutes.
    Consumes the OTP on success (single-use).
    """
    email = payload.email.lower().strip()

    # Verify OTP
    record = _otp_store.get(email)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found for this email. Please request a new one.",
        )
    otp_code, expires_at = record
    if datetime.now(timezone.utc) > expires_at:
        del _otp_store[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one.",
        )
    if payload.otp != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )
    del _otp_store[email]  # consume

    # Find user
    user: AppUser | None = await db.scalar(
        select(AppUser).where(AppUser.email == email, AppUser.is_deleted == False)  # noqa: E712
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this email.")

    # Update password
    now = datetime.now(timezone.utc)
    user.password_hash = await get_password_hash_async(payload.new_password)
    user.password_changed_at = now
    await db.commit()
    logger.info("Password reset for user %s", user.user_id)
    return {"message": "Password reset successfully. Please sign in with your new password."}


# ─── Current User: Profile ────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Return the currently authenticated user's profile."""
    user: AppUser | None = await db.scalar(
        select(AppUser).where(
            AppUser.user_id == current_user["user_id"],
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=f"{user.first_name} {user.last_name}".strip(),
        mobile=user.mobile,
        job_title=user.job_title,
        is_tenant_admin=user.is_tenant_admin,
        last_login_at=user.last_login_at,
    )


@router.put("/me", response_model=MeResponse)
async def update_me(
    payload: MeUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Update the currently authenticated user's profile (name, mobile, job title)."""
    user: AppUser | None = await db.scalar(
        select(AppUser).where(
            AppUser.user_id == current_user["user_id"],
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.mobile is not None:
        user.mobile = payload.mobile.strip() or None
    if payload.job_title is not None:
        user.job_title = payload.job_title.strip() or None

    user.updated_by = current_user["user_id"]
    await db.commit()
    await db.refresh(user)

    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=f"{user.first_name} {user.last_name}".strip(),
        mobile=user.mobile,
        job_title=user.job_title,
        is_tenant_admin=user.is_tenant_admin,
        last_login_at=user.last_login_at,
    )


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user — requires current password."""
    user: AppUser | None = await db.scalar(
        select(AppUser).where(
            AppUser.user_id == current_user["user_id"],
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not await verify_password_async(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from your current password.",
        )

    user.password_hash = await get_password_hash_async(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.updated_by = current_user["user_id"]
    await db.commit()
    return {"message": "Password changed successfully."}


# ─── First-Login: Forced Password Change ─────────────────────────────────────

@router.post("/forced-change-password", status_code=status.HTTP_200_OK)
async def forced_change_password(
    payload: ForcedChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Used when must_change_password=True after first login with temp credentials.

    Does NOT require the old/temp password — the user is already authenticated
    via their JWT, which is sufficient proof of identity.
    Sets must_change_password=False on success.
    """
    user: AppUser | None = await db.scalar(
        select(AppUser).where(
            AppUser.user_id == current_user["user_id"],
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No forced password change is required for this account.",
        )

    now = datetime.now(timezone.utc)
    user.password_hash = await get_password_hash_async(payload.new_password)
    user.password_changed_at = now
    user.must_change_password = False
    user.updated_by = current_user["user_id"]
    await db.commit()
    logger.info("Forced password change completed for user %s", user.user_id)
    return {"message": "Password changed successfully. Please log in again with your new password."}


# ─── Standalone Set-Password Page (served from email link) ───────────────────

def _set_password_html(email: str, error: str = "", success: bool = False) -> str:
    """Return a fully self-contained HTML page for first-login password setup."""
    from app.core.config import settings as _settings
    frontend_url = _settings.FRONTEND_URL.rstrip("/")
    encoded_email = urllib.parse.quote(email)

    error_block = (
        f'<div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;'
        f'padding:12px 16px;margin-bottom:16px;color:#dc2626;font-size:13px">{error}</div>'
        if error else ""
    )
    success_block = (
        f'<div style="background:#dcfce7;border:1px solid #86efac;border-radius:8px;'
        f'padding:12px 16px;margin-bottom:16px;color:#16a34a;font-size:13px">'
        f'Password set successfully! Redirecting to login…</div>'
        f'<script>setTimeout(()=>{{window.location.href="{frontend_url}/login";}},2000);</script>'
        if success else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Set New Password — NDIS Manager</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
        background:#f1f5f9;min-height:100vh;display:flex;align-items:center;
        justify-content:center;padding:1rem}}
  .card{{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);
         padding:2rem;width:100%;max-width:420px}}
  .logo{{display:flex;align-items:center;gap:8px;margin-bottom:1.5rem}}
  .logo-icon{{width:32px;height:32px;background:#4a2080;border-radius:8px;
              display:flex;align-items:center;justify-content:center}}
  .logo-icon svg{{width:18px;height:18px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
  .logo-name{{font-size:15px;font-weight:600;color:#1e293b}}
  h1{{font-size:20px;font-weight:600;color:#1e293b;margin-bottom:6px}}
  .subtitle{{font-size:13px;color:#64748b;margin-bottom:1.5rem}}
  .divider{{height:1px;background:#e2e8f0;margin:1.25rem 0}}
  label{{display:block;font-size:12px;font-weight:500;color:#475569;margin-bottom:5px}}
  .field{{margin-bottom:1rem}}
  .input-wrap{{position:relative}}
  .input-wrap > svg{{position:absolute;left:10px;top:50%;transform:translateY(-50%);
                    width:16px;height:16px;stroke:#94a3b8;fill:none;stroke-width:2;
                    stroke-linecap:round;stroke-linejoin:round;pointer-events:none}}
  .toggle-eye{{position:absolute;right:10px;top:50%;transform:translateY(-50%);
               background:none;border:none;cursor:pointer;padding:4px;z-index:2;
               line-height:0;border-radius:4px;display:flex;align-items:center;justify-content:center}}
  .toggle-eye:hover{{background:#f1f5f9}}
  .toggle-eye svg{{position:static;width:16px;height:16px;stroke:#94a3b8;fill:none;
                   stroke-width:2;stroke-linecap:round;stroke-linejoin:round;
                   pointer-events:none;transform:none}}
  input[type=email],input[type=password],input[type=text]{{
    width:100%;padding:9px 36px 9px 34px;font-size:13px;
    border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc;
    color:#1e293b;outline:none;transition:border .15s}}
  input:focus{{border-color:#4a2080;background:#fff}}
  input[readonly]{{color:#94a3b8;cursor:not-allowed}}
  .hint{{font-size:11px;color:#94a3b8;margin-top:4px}}
  .btn{{width:100%;padding:11px;background:#4a2080;color:#fff;font-size:14px;
        font-weight:600;border:none;border-radius:8px;cursor:pointer;
        margin-top:4px;transition:background .15s}}
  .btn:hover{{background:#3a1870}}
  .btn:disabled{{background:#94a3b8;cursor:not-allowed}}
  .footer{{text-align:center;font-size:12px;color:#94a3b8;margin-top:1.25rem}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">
      <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    </div>
    <span class="logo-name">NDIS Manager</span>
  </div>

  <h1>Set your new password</h1>
  <p class="subtitle">Enter the temporary password from your welcome email, then choose a new password to secure your account.</p>

  {error_block}{success_block}

  <form method="POST" action="/api/v1/auth/set-password" id="spf">
    <div class="field">
      <label for="email">Email</label>
      <div class="input-wrap">
        <svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 7 10-7"/></svg>
        <input type="email" id="email" name="email" value="{email}" readonly tabindex="-1">
      </div>
    </div>

    <div class="field">
      <label for="temp_password">Temporary password <span style="color:#dc2626">*</span></label>
      <div class="input-wrap">
        <svg viewBox="0 0 24 24"><circle cx="8" cy="15" r="3"/><path d="m11 12 9-9m-3 0 3 3m-6 0 3 3"/></svg>
        <input type="password" id="temp_password" name="temp_password" placeholder="From your welcome email" required>
      </div>
    </div>

    <div class="divider"></div>

    <div class="field">
      <label for="new_password">New password <span style="color:#dc2626">*</span></label>
      <div class="input-wrap">
        <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        <input type="password" id="new_password" name="new_password" placeholder="Min. 8 characters" required minlength="8">
        <button type="button" class="toggle-eye" onclick="togglePw('new_password','eye_new')" tabindex="-1" aria-label="Show/hide password">
          <svg id="eye_new" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </div>
      <div class="hint">At least 8 characters, mix of letters, numbers and symbols.</div>
    </div>

    <div class="field">
      <label for="confirm_password">Confirm new password <span style="color:#dc2626">*</span></label>
      <div class="input-wrap">
        <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        <input type="password" id="confirm_password" name="confirm_password" placeholder="Re-enter your new password" required>
        <button type="button" class="toggle-eye" onclick="togglePw('confirm_password','eye_confirm')" tabindex="-1" aria-label="Show/hide password">
          <svg id="eye_confirm" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </div>
    </div>

    <button type="submit" class="btn" id="submit_btn">Set new password</button>
  </form>

  <p class="footer">After setting your password you'll be taken to the login screen.</p>
</div>
<script>
var EYE_OPEN = '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>';
var EYE_SHUT = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
function togglePw(inputId, svgId) {{
  var inp = document.getElementById(inputId);
  var svg = document.getElementById(svgId);
  if (inp.type === 'password') {{
    inp.type = 'text';
    svg.innerHTML = EYE_SHUT;
    svg.style.stroke = '#4a2080';
  }} else {{
    inp.type = 'password';
    svg.innerHTML = EYE_OPEN;
    svg.style.stroke = '#94a3b8';
  }}
}}
document.getElementById('spf').addEventListener('submit', function(e) {{
  var np = document.getElementById('new_password').value;
  var cp = document.getElementById('confirm_password').value;
  if (np !== cp) {{
    e.preventDefault();
    alert('New password and confirm password do not match.');
    return;
  }}
  document.getElementById('submit_btn').disabled = true;
  document.getElementById('submit_btn').textContent = 'Setting password…';
}});
</script>
</body>
</html>"""


@router.get("/set-password", response_class=HTMLResponse, include_in_schema=False)
async def set_password_page(email: str = ""):
    """Serve the standalone Set New Password page.

    Linked from the welcome email: /api/v1/auth/set-password?email=user@example.com
    No auth required — user proves identity by knowing the temp password.
    """
    return HTMLResponse(_set_password_html(urllib.parse.unquote(email)))


@router.post("/set-password", response_class=HTMLResponse, include_in_schema=False)
async def set_password_submit(
    email: str = Form(...),
    temp_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Set New Password form submission.

    Verifies the temp password against the stored hash, then sets the new password
    and clears must_change_password. Redirects to frontend login on success.
    """
    from app.core.config import settings as _settings

    frontend_url = _settings.FRONTEND_URL.rstrip("/")
    email_clean = email.lower().strip()

    # Basic validation
    if new_password != confirm_password:
        return HTMLResponse(_set_password_html(email_clean, error="New password and confirm password do not match."))

    if len(new_password) < 8:
        return HTMLResponse(_set_password_html(email_clean, error="New password must be at least 8 characters."))

    # Look up user
    user: AppUser | None = await db.scalar(
        select(AppUser).where(
            AppUser.email == email_clean,
            AppUser.is_deleted == False,  # noqa: E712
        )
    )
    if not user:
        return HTMLResponse(_set_password_html(email_clean, error="No account found for this email address."))

    if not user.must_change_password:
        # Already changed — just redirect to login
        return RedirectResponse(url=f"{frontend_url}/login", status_code=302)

    # Verify the temporary password
    if not await verify_password_async(temp_password, user.password_hash):
        return HTMLResponse(_set_password_html(email_clean, error="Temporary password is incorrect. Please check your welcome email."))

    # Set new password and clear the flag
    now = datetime.now(timezone.utc)
    user.password_hash = await get_password_hash_async(new_password)
    user.password_changed_at = now
    user.must_change_password = False
    await db.commit()
    logger.info("Set-password page: password updated for user %s", user.user_id)

    # Show success with redirect script
    return HTMLResponse(_set_password_html(email_clean, success=True))
