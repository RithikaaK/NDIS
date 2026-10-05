"""Tenant config schemas — covers 8.1–8.7."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TenantConfigUpdate(BaseModel):
    # Regional
    country: Optional[str]        = Field(None, max_length=100)
    state: Optional[str]          = Field(None, max_length=100)
    date_format: Optional[str]    = Field(None, max_length=20)
    time_format: Optional[str]    = Field(None, max_length=10)
    week_starts_on: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str]       = Field(None, max_length=100)

    # Currency & Tax
    currency_code: Optional[str]   = Field(None, max_length=3)
    enable_gst: Optional[bool]     = None
    gst_rate: Optional[int]        = None
    enable_schads_award: Optional[bool] = None

    # Billing
    invoice_prefix: Optional[str]       = Field(None, max_length=20)
    invoice_due_days: Optional[int]     = None
    billing_frequency: Optional[str]    = Field(None, max_length=50)
    payment_terms: Optional[str]        = Field(None, max_length=200)
    auto_invoice_enabled: Optional[bool] = None
    default_funding_type: Optional[str] = Field(None, max_length=50)

    # Notifications
    notify_email_enabled: Optional[bool]          = None
    notify_sms_enabled: Optional[bool]            = None
    notify_inapp_enabled: Optional[bool]          = None
    notify_appointment_reminders: Optional[bool]  = None
    notify_plan_expiry_alerts: Optional[bool]     = None
    notify_overdue_payment_alerts: Optional[bool] = None
    notify_budget_alerts: Optional[bool]          = None
    notify_reminder_hours_before: Optional[int]   = None

    # Security
    session_timeout_minutes: Optional[int]     = None
    password_min_length: Optional[int]         = None
    password_require_uppercase: Optional[bool] = None
    password_require_numbers: Optional[bool]   = None
    password_require_symbols: Optional[bool]   = None
    max_login_attempts: Optional[int]          = None
    mfa_enabled: Optional[bool]               = None

    # Integrations
    enable_pace_integration: Optional[bool]             = None
    enable_proda_integration: Optional[bool]            = None
    integration_myob_enabled: Optional[bool]            = None
    integration_xero_enabled: Optional[bool]            = None
    integration_communication_provider: Optional[str]   = Field(None, max_length=50)
    integration_payment_provider: Optional[str]         = Field(None, max_length=50)


class TenantConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    config_id: int

    # Regional
    country: str
    state: Optional[str]
    date_format: str
    time_format: str
    week_starts_on: str
    timezone: str

    # Currency & Tax
    currency_code: str
    enable_gst: bool
    gst_rate: int
    enable_schads_award: bool

    # Billing
    invoice_prefix: str
    invoice_due_days: int
    billing_frequency: str
    payment_terms: Optional[str]
    auto_invoice_enabled: bool
    default_funding_type: str

    # Notifications
    notify_email_enabled: bool
    notify_sms_enabled: bool
    notify_inapp_enabled: bool
    notify_appointment_reminders: bool
    notify_plan_expiry_alerts: bool
    notify_overdue_payment_alerts: bool
    notify_budget_alerts: bool
    notify_reminder_hours_before: int

    # Security
    session_timeout_minutes: int
    password_min_length: int
    password_require_uppercase: bool
    password_require_numbers: bool
    password_require_symbols: bool
    max_login_attempts: int
    mfa_enabled: bool

    # Integrations
    enable_pace_integration: bool
    enable_proda_integration: bool
    integration_myob_enabled: bool
    integration_xero_enabled: bool
    integration_communication_provider: Optional[str]
    integration_payment_provider: Optional[str]

    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
