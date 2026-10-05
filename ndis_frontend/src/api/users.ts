import api from './axios'

// ─── Field-name transformers ──────────────────────────────────────────────────
// Backend uses: mobile, user_id (UUID)
// Frontend uses: phone, id

const toBackend = (data: any): any => {
  const payload: any = {
    first_name: data.first_name,
    last_name: data.last_name,
    email: data.email,
    mobile: data.phone || data.mobile || undefined,
    job_title: data.job_title || undefined,
    is_tenant_admin: data.is_tenant_admin || false,
    is_active: data.is_active !== false,
  }
  // password: only send if provided (blank means "keep existing" on update)
  if (data.password) payload.password = data.password
  // branch_id: required on create, optional on update; must be an integer
  const bid = data.branch_id
  if (bid !== '' && bid !== null && bid !== undefined) {
    payload.branch_id = parseInt(bid, 10)
  }
  // role_ids: pass through for both create and update
  if (data.role_ids !== undefined) payload.role_ids = data.role_ids
  return payload
}

const fromBackend = (u) => u ? ({
  ...u,
  id: u.user_id,         // UUID string — used for update/delete/assign-role URLs
  phone: u.mobile,       // display field
  role_ids:   u.role_ids   ?? [],
  role_names: u.role_names ?? [],
}) : u

// ─── Response helpers ─────────────────────────────────────────────────────────
const wrapList = async (promise) => {
  const res = await promise
  return { ...res, data: (res.data || []).map(fromBackend) }
}
const wrapOne = async (promise) => {
  const res = await promise
  return { ...res, data: fromBackend(res.data) }
}

// ─── Exports ──────────────────────────────────────────────────────────────────
export const getUsers            = (tid: any, params?: any) => wrapList(api.get(`/tenant/${tid}/users`, { params }))
export const getUser             = (tid, uid)            => wrapOne(api.get(`/tenant/${tid}/users/${uid}`))
export const createUser          = (tid, data)           => wrapOne(api.post(`/tenant/${tid}/users`, toBackend(data)))
export const updateUser          = (tid, uid, data)      => wrapOne(api.put(`/tenant/${tid}/users/${uid}`, toBackend(data)))
export const deleteUser          = (tid, uid)            => api.delete(`/tenant/${tid}/users/${uid}`)

/** Direct PATCH-style update — sends ONLY the fields AppUserUpdate accepts, nothing extra. */
export const patchUser = (tid: any, uid: string, fields: {
  email?: string; first_name?: string; last_name?: string; mobile?: string | null;
  job_title?: string | null; is_active?: boolean; password?: string; branch_id?: number;
  role_ids?: number[];
}) => wrapOne(api.put(`/tenant/${tid}/users/${uid}`, fields))

// Role management
export const assignRole          = (tid, uid, rid)       => api.post(`/tenant/${tid}/users/${uid}/roles/${rid}`)
export const getUserRoles        = (tid, uid)            => api.get(`/tenant/${tid}/users/${uid}/roles`)
export const removeRole          = (tid, uid, rid)       => api.delete(`/tenant/${tid}/users/${uid}/roles/${rid}`)

// Activate / Deactivate
export const activateUser        = (tid, uid)            => wrapOne(api.patch(`/tenant/${tid}/users/${uid}/activate`))
export const deactivateUser      = (tid, uid)            => wrapOne(api.patch(`/tenant/${tid}/users/${uid}/deactivate`))

// Resend invitation
export const resendInvitation    = (tid, uid)            => api.post(`/tenant/${tid}/users/${uid}/resend-invitation`)

// User activity / audit trail
export const getUserActivity     = (tid, uid, limit = 50) => api.get(`/tenant/${tid}/users/${uid}/activity`, { params: { limit } })

// Effective permissions
export const getUserPermissions  = (tid, uid)            => api.get(`/tenant/${tid}/users/${uid}/permissions`)

// Password management
export const changePassword      = (tid, uid, currentPassword, newPassword) =>
  api.post(`/tenant/${tid}/users/${uid}/change-password`, {
    current_password: currentPassword,
    new_password:     newPassword,
  })
