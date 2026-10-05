"""TenantConfig ORM model — covers 8.1–8.7 Tenant-Level Configuration."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantConfig(Base):
    """Tenant-specific configuration: regional, financial, security, notifications, integrations.
    Lives in per-tenant schema. One config row per tenant schema.
    """
    __tablename__ = "tenant_config"
    __table_args__ = {"schema": "tenant_schema"}

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── 8.2 Regional & Timezone ───────────────────────────────────────────────
    country: Mapped[str]          = mapped_column(String(100), default="Australia", nullable=False)
    state: Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    date_format: Mapped[str]      = mapped_column(String(20), default="DD/MM/YYYY", nullable=False)
    time_format: Mapped[str]      = mapped_column(String(10), default="24h", nullable=False)
    week_starts_on: Mapped[str]   = mapped_column(String(10), default="Monday", nullable=False)
    # timezone lives on Tenant model (ndis_common) — mirrored here for convenience
    timezone: Mapped[str]         = mapped_column(String(100), default="Australia/Sydney", nullable=False)

    # ── 8.3 Currency & Tax ────────────────────────────────────────────────────
    currency_code: Mapped[str]    = mapped_column(String(3), default="AUD", nullable=False)
    enable_gst: Mapped[bool]      = mapped_column(Boolean, default=True, nullable=False)
    gst_rate: Mapped[int]         = mapped_column(Integer, default=10, nullable=False)  # percent
    enable_schads_award: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── 8.4 Billing & Invoice ─────────────────────────────────────────────────
    invoice_prefix: Mapped[str]          = mapped_column(String(20), default="INV", nullable=False)
    invoice_due_days: Mapped[int]        = mapped_column(Integer, default=14, nullable=False)
    billing_frequency: Mapped[str]       = mapped_column(String(50), default="Monthly", nullable=False)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    auto_invoice_enabled: Mapped[bool]   = mapped_column(Boolean, default=False, nullable=False)
    default_funding_type: Mapped[str]    = mapped_column(String(50), default="Agency Managed", nullable=False)

    # ── 8.5 Notification Configuration ───────────────────────────────────────
    notify_email_enabled: Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    notify_sms_enabled: Mapped[bool]            = mapped_column(Boolean, default=False, nullable=False)
    notify_inapp_enabled: Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    notify_appointment_reminders: Mapped[bool]  = mapped_column(Boolean, default=True, nullable=False)
    notify_plan_expiry_alerts: Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    notify_overdue_payment_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_budget_alerts: Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    notify_reminder_hours_before: Mapped[int]   = mapped_column(Integer, default=24, nullable=False)

    # ── 8.6 Security & Access ─────────────────────────────────────────────────
    session_timeout_minutes: Mapped[int]         = mapped_column(Integer, default=60, nullable=False)
    password_min_length: Mapped[int]             = mapped_column(Integer, default=8, nullable=False)
    password_require_uppercase: Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    password_require_numbers: Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)
    password_require_symbols: Mapped[bool]       = mapped_column(Boolean, default=False, nullable=False)
    max_login_attempts: Mapped[int]              = mapped_column(Integer, default=5, nullable=False)
    mfa_enabled: Mapped[bool]                    = mapped_column(Boolean, default=False, nullable=False)

    # ── 8.7 Integration Configuration ─────────────────────────────────────────
    enable_pace_integration: Mapped[bool]             = mapped_column(Boolean, default=False, nullable=False)
    enable_proda_integration: Mapped[bool]            = mapped_column(Boolean, default=False, nullable=False)
    integration_myob_enabled: Mapped[bool]            = mapped_column(Boolean, default=False, nullable=False)
    integration_xero_enabled: Mapped[bool]            = mapped_column(Boolean, default=False, nullable=False)
    integration_communication_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    integration_payment_provider: Mapped[Optional[str]]       = mapped_column(String(50), nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────────
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
