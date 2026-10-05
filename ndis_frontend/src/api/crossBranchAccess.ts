import api from './axios'

const BASE = (tid: number) => `/tenant/${tid}/cross-branch-access`

export const listCrossbranchAccess   = (tid: number, params?: { status?: string; branch_id?: number }) =>
  api.get(BASE(tid), { params })

export const getCrossbranchAccess    = (tid: number, id: number) =>
  api.get(`${BASE(tid)}/${id}`)

export const createAccessRequest     = (tid: number, data: any) =>
  api.post(BASE(tid), data)

export const createEmergencyAccess   = (tid: number, data: any) =>
  api.post(`${BASE(tid)}/emergency`, data)

export const approveAccess           = (tid: number, id: number, data?: any) =>
  api.patch(`${BASE(tid)}/${id}/approve`, data ?? {})

export const rejectAccess            = (tid: number, id: number, data?: any) =>
  api.patch(`${BASE(tid)}/${id}/reject`, data ?? {})

export const revokeAccess            = (tid: number, id: number, data?: any) =>
  api.patch(`${BASE(tid)}/${id}/revoke`, data ?? {})

export const reviewEmergencyAccess   = (tid: number, id: number, data?: any) =>
  api.patch(`${BASE(tid)}/${id}/review`, data ?? {})

export const getCrossbranchAudit     = (tid: number, limit = 100) =>
  api.get(`/tenant/${tid}/cross-branch-access-audit`, { params: { limit } })
