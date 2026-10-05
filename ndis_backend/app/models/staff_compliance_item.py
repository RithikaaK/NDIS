"""Staff Compliance Item model — tracks per-staff mandatory requirements."""
from sqlalchemy import Column, String, Text, Date, Boolean, DateTime, func
from app.core.database import Base


class StaffComplianceItem(Base):
    __tablename__ = "staff_compliance_item"
    __table_args__ = {"schema": "tenant_schema"}

    compliance_item_id  = Column(String(36), primary_key=True)
    tenant_id           = Column(String(36), nullable=False, index=True)
    staff_id            = Column(String(36), nullable=False, index=True)

    # 3.1 Requirement management
    requirement_name    = Column(String(200), nullable=False)
    reference_no        = Column(String(100))
    category            = Column(String(100))          # e.g. NDIS mandatory, State mandatory, Organisation policy
    requirement_type    = Column(String(100))          # e.g. Check, Training, Vaccination, Certificate

    # 3.2 / 3.3  Status + expiry tracking
    completed_date      = Column(Date)
    expiry_date         = Column(Date)
    status              = Column(String(50), default="Pending")  # Current / Due soon / Expired / Pending
    is_mandatory        = Column(Boolean, default=True)

    # 3.4 Document management
    document_filename   = Column(String(300))
    document_url        = Column(String(500))
    document_uploaded_at = Column(DateTime)

    # 3.5 Alerts / reminders
    reminder_days_before = Column(String(10), default="30")  # days before expiry to send reminder
    reminder_sent_at    = Column(DateTime)

    notes               = Column(Text)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())
