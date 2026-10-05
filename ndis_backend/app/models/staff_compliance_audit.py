"""Staff Compliance Audit Trail model — 3.6 Compliance History / Audit Trail."""
from sqlalchemy import Column, String, Text, DateTime, func
from app.core.database import Base


class StaffComplianceAudit(Base):
    __tablename__ = "staff_compliance_audit"
    __table_args__ = {"schema": "tenant_schema"}

    audit_id            = Column(String(36), primary_key=True)
    tenant_id           = Column(String(36), nullable=False, index=True)
    staff_id            = Column(String(36), nullable=False, index=True)
    compliance_item_id  = Column(String(36), nullable=False, index=True)

    action_type         = Column(String(100))   # created / updated / document_uploaded / reminder_sent / status_changed
    action_description  = Column(String(500))
    previous_status     = Column(String(50))
    new_status          = Column(String(50))
    changed_by_user_id  = Column(String(36))
    changed_by_name     = Column(String(200))
    notes               = Column(Text)
    created_at          = Column(DateTime, server_default=func.now())
