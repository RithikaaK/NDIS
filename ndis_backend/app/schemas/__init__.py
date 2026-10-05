"""Schemas package — re-exports all Pydantic schema classes."""
from app.schemas.common import MessageResponse
from app.schemas.subscription_plan import SubscriptionPlanResponse
from app.schemas.tenant_schema import (
    TenantSignupBase,
    TenantSignupRegistered,
    TenantSignupNonRegistered,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    DomainCheckResponse,
)
from app.schemas.tenant_contact import TenantContactCreate, TenantContactUpdate, TenantContactResponse
from app.schemas.tenant_address import TenantAddressCreate, TenantAddressUpdate, TenantAddressResponse
from app.schemas.tenant_config import TenantConfigUpdate, TenantConfigResponse
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse, BranchStaffResponse, BranchProgramResponse
from app.schemas.program import ProgramCreate, ProgramUpdate, ProgramResponse
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.permission import PermissionResponse
from app.schemas.app_user import AppUserCreate, AppUserUpdate, AppUserResponse
from app.schemas.auth import (
    LoginRequest, TokenResponse,
    SendOtpRequest, VerifyOtpRequest,
    ResetPasswordRequest, MeResponse, MeUpdate, ChangePasswordRequest,
    ForcedChangePasswordRequest,
)
from app.schemas.staff_profile import (
    StaffProfileCreate, StaffProfileUpdate, StaffProfileResponse,
    StaffPersonalInfoCreate, StaffPersonalInfoResponse,
    StaffContactInfoCreate, StaffContactInfoResponse,
    StaffIdentificationCreate, StaffIdentificationResponse,
    StaffPreferencesCreate, StaffPreferencesResponse,
    StaffEmergencyContactCreate, StaffEmergencyContactResponse,
)
from app.schemas.staff_employment import (
    EmploymentInformationCreate, EmploymentInformationResponse,
    StaffProbationCreate, StaffProbationResponse,
    StaffContractCreate, StaffContractResponse,
    StaffRolesCreate, StaffRolesResponse,
    StaffExitProcessCreate, StaffExitProcessResponse,
)
from app.schemas.staff_compliance import (
    QualificationCreate, QualificationResponse,
    StaffQualificationCreate, StaffQualificationResponse,
    CertificationCreate, CertificationResponse,
    StaffCertificationCreate, StaffCertificationResponse,
)
from app.schemas.staff_availability import StaffAvailabilityCreate, StaffAvailabilityResponse
from app.schemas.staff_timesheets import (
    StaffTimesheetHeaderCreate, StaffTimesheetHeaderUpdate, StaffTimesheetHeaderResponse,
    StaffTimesheetLineCreate, StaffTimesheetLineResponse,
)
from app.schemas.staff_leave import (
    LeaveTypeCreate, LeaveTypeResponse,
    StaffLeaveRequestDateCreate, StaffLeaveRequestDateResponse,
    StaffLeaveRequestCreate, StaffLeaveRequestUpdate, StaffLeaveRequestResponse,
    StaffLeaveBalanceResponse,
)
from app.schemas.staff_documents import StaffDocumentResponse
from app.schemas.staff_detail import StaffDetailResponse
from app.schemas.staff_performance import (
    StaffPerformanceReviewCreate, StaffPerformanceReviewUpdate, StaffPerformanceReviewResponse,
    StaffKpiCreate, StaffKpiUpdate, StaffKpiResponse,
    StaffGoalCreate, StaffGoalUpdate, StaffGoalResponse,
)
from app.schemas.staff_compliance_tracking import (
    ComplianceItemCreate, ComplianceItemUpdate, ComplianceItemResponse,
    ComplianceAuditResponse,
)

__all__ = [
    "MessageResponse",
    "SubscriptionPlanResponse",
    "TenantSignupBase",
    "TenantSignupRegistered",
    "TenantSignupNonRegistered",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    "DomainCheckResponse",
    "TenantContactCreate",
    "TenantContactUpdate",
    "TenantContactResponse",
    "TenantAddressCreate",
    "TenantAddressUpdate",
    "TenantAddressResponse",
    "TenantConfigUpdate",
    "TenantConfigResponse",
    "BranchCreate",
    "BranchUpdate",
    "BranchResponse",
    "ProgramCreate",
    "ProgramUpdate",
    "ProgramResponse",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "PermissionResponse",
    "AppUserCreate",
    "AppUserUpdate",
    "AppUserResponse",
    "LoginRequest",
    "TokenResponse",
    "SendOtpRequest",
    "VerifyOtpRequest",
    "ResetPasswordRequest",
    "MeResponse",
    "MeUpdate",
    "ChangePasswordRequest",
    "ForcedChangePasswordRequest",
    # Staff — Profile
    "StaffProfileCreate", "StaffProfileUpdate", "StaffProfileResponse",
    "StaffPersonalInfoCreate", "StaffPersonalInfoResponse",
    "StaffContactInfoCreate", "StaffContactInfoResponse",
    "StaffIdentificationCreate", "StaffIdentificationResponse",
    "StaffPreferencesCreate", "StaffPreferencesResponse",
    "StaffEmergencyContactCreate", "StaffEmergencyContactResponse",
    # Staff — Employment
    "EmploymentInformationCreate", "EmploymentInformationResponse",
    "StaffProbationCreate", "StaffProbationResponse",
    "StaffContractCreate", "StaffContractResponse",
    "StaffRolesCreate", "StaffRolesResponse",
    "StaffExitProcessCreate", "StaffExitProcessResponse",
    # Staff — Compliance
    "QualificationCreate", "QualificationResponse",
    "StaffQualificationCreate", "StaffQualificationResponse",
    "CertificationCreate", "CertificationResponse",
    "StaffCertificationCreate", "StaffCertificationResponse",
    # Staff — Availability
    "StaffAvailabilityCreate", "StaffAvailabilityResponse",
    # Staff — Timesheets
    "StaffTimesheetHeaderCreate", "StaffTimesheetHeaderUpdate", "StaffTimesheetHeaderResponse",
    "StaffTimesheetLineCreate", "StaffTimesheetLineResponse",
    # Staff — Leave
    "LeaveTypeCreate", "LeaveTypeResponse",
    "StaffLeaveRequestDateCreate", "StaffLeaveRequestDateResponse",
    "StaffLeaveRequestCreate", "StaffLeaveRequestUpdate", "StaffLeaveRequestResponse",
    "StaffLeaveBalanceResponse",
    # Staff — Documents
    "StaffDocumentResponse",
    # Staff — Detail
    "StaffDetailResponse",
    # Staff — Performance
    "StaffPerformanceReviewCreate", "StaffPerformanceReviewUpdate", "StaffPerformanceReviewResponse",
    "StaffKpiCreate", "StaffKpiUpdate", "StaffKpiResponse",
    "StaffGoalCreate", "StaffGoalUpdate", "StaffGoalResponse",
]
