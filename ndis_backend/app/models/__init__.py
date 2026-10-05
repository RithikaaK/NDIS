"""Models package — imports all ORM classes so SQLAlchemy mapper registry is complete."""
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant_model import Tenant
from app.models.tenant_subscription import TenantSubscription
from app.models.tenant_contact import TenantContact
from app.models.tenant_address import TenantAddress
from app.models.tenant_service_state import TenantServiceState
from app.models.tenant_registration_group import TenantRegistrationGroup
from app.models.tenant_document import TenantDocument
from app.models.branch import Branch
from app.models.program import Program
from app.models.program_branch import ProgramBranch
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.app_user import AppUser
from app.models.user_role import UserRole
from app.models.cross_branch_access import CrossBranchAccess
from app.models.tenant_config import TenantConfig
from app.models.audit_log import AuditLog

# ── Staff Management models ────────────────────────────────────────────────────
from app.models.staff_profile import StaffProfile
from app.models.staff_personal_info import StaffPersonalInfo
from app.models.staff_contact_info import StaffContactInfo
from app.models.staff_identification import StaffIdentification
from app.models.staff_preferences import StaffPreferences
from app.models.staff_emergency_contact import StaffEmergencyContact
from app.models.employment_information import EmploymentInformation
from app.models.staff_probation import StaffProbation
from app.models.staff_contract import StaffContract
from app.models.staff_roles import StaffRoles
from app.models.staff_exit_process import StaffExitProcess
from app.models.qualification import Qualification
from app.models.staff_qualification import StaffQualification
from app.models.certification import Certification
from app.models.staff_certification import StaffCertification
from app.models.staff_availability import StaffAvailability
from app.models.staff_timesheet_header import StaffTimesheetHeader
from app.models.staff_timesheet_line import StaffTimesheetLine
from app.models.leave_type import LeaveType
from app.models.staff_leave_request import StaffLeaveRequest
from app.models.staff_leave_request_date import StaffLeaveRequestDate
from app.models.staff_leave_balance import StaffLeaveBalance
from app.models.staff_document_repository import StaffDocumentRepository

__all__ = [
    "SubscriptionPlan",
    "Tenant",
    "TenantSubscription",
    "TenantContact",
    "TenantAddress",
    "TenantServiceState",
    "TenantRegistrationGroup",
    "TenantDocument",
    "Branch",
    "Program",
    "ProgramBranch",
    "Role",
    "Permission",
    "RolePermission",
    "AppUser",
    "UserRole",
    "CrossBranchAccess",
    "TenantConfig",
    "AuditLog",
    # Staff Management
    "StaffProfile",
    "StaffPersonalInfo",
    "StaffContactInfo",
    "StaffIdentification",
    "StaffPreferences",
    "StaffEmergencyContact",
    "EmploymentInformation",
    "StaffProbation",
    "StaffContract",
    "StaffRoles",
    "StaffExitProcess",
    "Qualification",
    "StaffQualification",
    "Certification",
    "StaffCertification",
    "StaffAvailability",
    "StaffTimesheetHeader",
    "StaffTimesheetLine",
    "LeaveType",
    "StaffLeaveRequest",
    "StaffLeaveRequestDate",
    "StaffLeaveBalance",
    "StaffDocumentRepository",
]
