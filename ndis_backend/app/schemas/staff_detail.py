"""Staff Detail schema — composite response aggregating all staff sub-entities."""
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.staff_profile import (
    StaffProfileResponse,
    StaffPersonalInfoResponse,
    StaffContactInfoResponse,
    StaffIdentificationResponse,
    StaffPreferencesResponse,
    StaffEmergencyContactResponse,
)
from app.schemas.staff_employment import (
    EmploymentInformationResponse,
    StaffProbationResponse,
    StaffContractResponse,
    StaffRolesResponse,
    StaffExitProcessResponse,
)
from app.schemas.staff_compliance import (
    StaffQualificationResponse,
    StaffCertificationResponse,
)
from app.schemas.staff_availability import StaffAvailabilityResponse
from app.schemas.staff_documents import StaffDocumentResponse


class StaffDetailResponse(BaseModel):
    """Full staff record with all sub-entities."""
    profile: StaffProfileResponse
    personal_info: Optional[StaffPersonalInfoResponse] = None
    contact_info: Optional[StaffContactInfoResponse] = None
    employment: Optional[EmploymentInformationResponse] = None
    probation: Optional[StaffProbationResponse] = None
    contract: Optional[StaffContractResponse] = None
    roles: List[StaffRolesResponse] = []
    identifications: List[StaffIdentificationResponse] = []
    emergency_contacts: List[StaffEmergencyContactResponse] = []
    preferences: Optional[StaffPreferencesResponse] = None
    exit_process: Optional[StaffExitProcessResponse] = None
    qualifications: List[StaffQualificationResponse] = []
    certifications: List[StaffCertificationResponse] = []
    availability: List[StaffAvailabilityResponse] = []
    documents: List[StaffDocumentResponse] = []
