/**
 * Staff Management API layer
 * All calls go through the shared axios instance which already attaches
 * the Bearer token and base URL.
 */
import api from './axios'

const BASE = (tid: number | string) => `/tenant/${tid}/staff`

// ─── Staff Profile ────────────────────────────────────────────────────────────

export const getStaffList = (tid: number, status?: string) =>
  api.get(BASE(tid), { params: status ? { status } : undefined })

export const getStaff = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}`)

export const createStaff = (tid: number, data: Record<string, any>) =>
  api.post(BASE(tid), data)

export const updateStaff = (tid: number, staffId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}`, data)

export const deleteStaff = (tid: number, staffId: string) =>
  api.delete(`${BASE(tid)}/${staffId}`)

// ─── Personal Info ────────────────────────────────────────────────────────────

export const getPersonalInfo = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/personal-info`)

export const upsertPersonalInfo = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/personal-info`, data)

// ─── Contact Info ─────────────────────────────────────────────────────────────

export const getContactInfo = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/contact-info`)

export const upsertContactInfo = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/contact-info`, data)

// ─── Employment ───────────────────────────────────────────────────────────────

export const getEmployment = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/employment`)

export const upsertEmployment = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/employment`, data)

// ─── Probation ────────────────────────────────────────────────────────────────

export const getProbation = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/probation`)

export const upsertProbation = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/probation`, data)

// ─── Contracts ────────────────────────────────────────────────────────────────

export const getContracts = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/contracts`)

export const createContract = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/contracts`, data)

export const updateContract = (tid: number, staffId: string, contractId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/contracts/${contractId}`, data)

export const deleteContract = (tid: number, staffId: string, contractId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/contracts/${contractId}`)

// ─── Staff Job Roles ──────────────────────────────────────────────────────────

export const getStaffRoles = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/roles`)

export const addStaffRole = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/roles`, data)

export const updateStaffRole = (tid: number, staffId: string, roleId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/roles/${roleId}`, data)

export const deleteStaffRole = (tid: number, staffId: string, roleId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/roles/${roleId}`)

// ─── Identification ───────────────────────────────────────────────────────────

export const getIdentifications = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/identifications`)

export const addIdentification = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/identifications`, data)

export const updateIdentification = (tid: number, staffId: string, idenId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/identifications/${idenId}`, data)

export const deleteIdentification = (tid: number, staffId: string, idenId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/identifications/${idenId}`)

// ─── Emergency Contacts ───────────────────────────────────────────────────────

export const getEmergencyContacts = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/emergency-contacts`)

export const addEmergencyContact = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/emergency-contacts`, data)

export const updateEmergencyContact = (tid: number, staffId: string, contactId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/emergency-contacts/${contactId}`, data)

export const deleteEmergencyContact = (tid: number, staffId: string, contactId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/emergency-contacts/${contactId}`)

// ─── Preferences ─────────────────────────────────────────────────────────────

export const getPreferences = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/preferences`)

export const upsertPreferences = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/preferences`, data)

// ─── Exit Process ─────────────────────────────────────────────────────────────

export const getExitProcess = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/exit-process`)

export const upsertExitProcess = (tid: number, staffId: string, data: Record<string, any>) =>
  api.put(`${BASE(tid)}/${staffId}/exit-process`, data)

// ─── Qualifications (master catalogue) ───────────────────────────────────────

export const getQualificationCatalogue = () =>
  api.get('/qualifications')

export const createQualificationCatalogue = (data: Record<string, any>) =>
  api.post('/qualifications', data)

// ─── Staff Qualifications ─────────────────────────────────────────────────────

export const getStaffQualifications = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/qualifications`)

export const addStaffQualification = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/qualifications`, data)

export const updateStaffQualification = (tid: number, staffId: string, qualId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/qualifications/${qualId}`, data)

export const deleteStaffQualification = (tid: number, staffId: string, qualId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/qualifications/${qualId}`)

// ─── Certifications (master catalogue) ───────────────────────────────────────

export const getCertificationCatalogue = () =>
  api.get('/certifications')

export const createCertificationCatalogue = (data: Record<string, any>) =>
  api.post('/certifications', data)

// ─── Staff Certifications ─────────────────────────────────────────────────────

export const getStaffCertifications = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/certifications`)

export const addStaffCertification = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/certifications`, data)

export const updateStaffCertification = (tid: number, staffId: string, certId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/certifications/${certId}`, data)

export const deleteStaffCertification = (tid: number, staffId: string, certId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/certifications/${certId}`)

// ─── Compliance Document Upload ───────────────────────────────────────────────

export const uploadComplianceDocument = (tid: number, staffId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`${BASE(tid)}/${staffId}/upload-document`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ─── Availability ─────────────────────────────────────────────────────────────

export const getAvailability = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/availability`)

export const createAvailability = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/availability`, data)

export const updateAvailability = (tid: number, staffId: string, availId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/availability/${availId}`, data)

export const deleteAvailability = (tid: number, staffId: string, availId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/availability/${availId}`)

// ─── Shifts & Roster (4.3–4.5) ─────────────────────────────────────────────────

export const getShifts = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/shifts`)

export const createShift = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/shifts`, data)

export const updateShift = (tid: number, staffId: string, shiftId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/shifts/${shiftId}`, data)

export const deleteShift = (tid: number, staffId: string, shiftId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/shifts/${shiftId}`)

// ─── Timesheets ───────────────────────────────────────────────────────────────

export const getTimesheets = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/timesheets`)

export const createTimesheet = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/timesheets`, data)

export const updateTimesheet = (tid: number, staffId: string, timesheetId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/timesheets/${timesheetId}`, data)

export const deleteTimesheet = (tid: number, staffId: string, timesheetId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/timesheets/${timesheetId}`)

export const getTimesheetLines = (tid: number, staffId: string, timesheetId: string) =>
  api.get(`${BASE(tid)}/${staffId}/timesheets/${timesheetId}/lines`)

export const addTimesheetLine = (tid: number, staffId: string, timesheetId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/timesheets/${timesheetId}/lines`, data)

// ─── Leave Types (master catalogue) ──────────────────────────────────────────

export const getLeaveTypes = () =>
  api.get('/leave-types')

export const createLeaveType = (data: Record<string, any>) =>
  api.post('/leave-types', data)

// ─── Leave Requests ───────────────────────────────────────────────────────────

export const getLeaveRequests = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/leave-requests`)

export const createLeaveRequest = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/leave-requests`, data)

export const updateLeaveRequest = (
  tid: number,
  staffId: string,
  leaveRequestId: string,
  data: Record<string, any>,
) => api.patch(`${BASE(tid)}/${staffId}/leave-requests/${leaveRequestId}`, data)

// ─── Leave Balances ───────────────────────────────────────────────────────────

export const getLeaveBalances = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/leave-balances`)

// ─── Documents ────────────────────────────────────────────────────────────────

export const getStaffDocuments = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/documents`)

export const uploadStaffDocument = (
  tid: number,
  staffId: string,
  data: {
    file: File
    document_type: string
    document_name: string
    document_status?: string
    document_description?: string
    expiry_date?: string
  },
) => {
  const form = new FormData()
  form.append('file', data.file)
  form.append('document_type', data.document_type)
  form.append('document_name', data.document_name)
  form.append('document_status', data.document_status ?? 'Active')
  if (data.document_description) form.append('document_description', data.document_description)
  if (data.expiry_date) form.append('expiry_date', data.expiry_date)
  return api.post(`${BASE(tid)}/${staffId}/documents`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteStaffDocument = (tid: number, staffId: string, documentId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/documents/${documentId}`)

export const updateStaffDocument = (
  tid: number,
  staffId: string,
  documentId: string,
  data: {
    file?: File
    document_type?: string
    document_name?: string
    document_status?: string
    document_description?: string
    expiry_date?: string | null
  },
) => {
  const form = new FormData()
  if (data.file) form.append('file', data.file)
  if (data.document_type !== undefined) form.append('document_type', data.document_type)
  if (data.document_name !== undefined) form.append('document_name', data.document_name)
  if (data.document_status !== undefined) form.append('document_status', data.document_status)
  if (data.document_description !== undefined) form.append('document_description', data.document_description)
  if (data.expiry_date !== undefined) form.append('expiry_date', data.expiry_date === null ? "null" : data.expiry_date)

  return api.patch(`${BASE(tid)}/${staffId}/documents/${documentId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ─── Performance Reviews ──────────────────────────────────────────────────────

export const getPerformanceReviews = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/performance-reviews`)

export const createPerformanceReview = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/performance-reviews`, data)

export const updatePerformanceReview = (tid: number, staffId: string, reviewId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/performance-reviews/${reviewId}`, data)

export const deletePerformanceReview = (tid: number, staffId: string, reviewId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/performance-reviews/${reviewId}`)

// ─── KPIs ─────────────────────────────────────────────────────────────────────

export const getKpis = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/kpis`)

export const createKpi = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/kpis`, data)

export const updateKpi = (tid: number, staffId: string, kpiId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/kpis/${kpiId}`, data)

export const deleteKpi = (tid: number, staffId: string, kpiId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/kpis/${kpiId}`)

// ─── Goals ────────────────────────────────────────────────────────────────────

export const getGoals = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/goals`)

export const createGoal = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/goals`, data)

export const updateGoal = (tid: number, staffId: string, goalId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/goals/${goalId}`, data)

export const deleteGoal = (tid: number, staffId: string, goalId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/goals/${goalId}`)

// ─── Compliance Tracking (3.1–3.6) ───────────────────────────────────────────

export const getComplianceItems = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/compliance-items`)

export const createComplianceItem = (tid: number, staffId: string, data: Record<string, any>) =>
  api.post(`${BASE(tid)}/${staffId}/compliance-items`, data)

export const updateComplianceItem = (tid: number, staffId: string, itemId: string, data: Record<string, any>) =>
  api.patch(`${BASE(tid)}/${staffId}/compliance-items/${itemId}`, data)

export const deleteComplianceItem = (tid: number, staffId: string, itemId: string) =>
  api.delete(`${BASE(tid)}/${staffId}/compliance-items/${itemId}`)

export const sendComplianceReminder = (tid: number, staffId: string, itemId: string) =>
  api.post(`${BASE(tid)}/${staffId}/compliance-items/${itemId}/remind`, {})

export const getComplianceAudit = (tid: number, staffId: string) =>
  api.get(`${BASE(tid)}/${staffId}/compliance-audit`)
