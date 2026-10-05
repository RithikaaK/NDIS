import api from './axios'

// ─── Field-name transformers ──────────────────────────────────────────────────
// Backend uses: role_code (required), role_id, permission_id, module, permission_code
// Frontend uses: id, resource, permission_name

const toBackend = (data) => ({
  role_name: data.role_name,
  role_code: data.role_code
    || data.role_name.toUpperCase().replace(/[^A-Z0-9]/g, '_').slice(0, 20),
  description: data.description || undefined,
  is_active: data.is_active !== false,
})

const fromBackend = (r) => r ? ({
  ...r,
  id: r.role_id,   // frontend key (integer)
}) : r

const permFromBackend = (p) => p ? ({
  ...p,
  id: p.permission_id,
  resource: p.module,
  permission_name: p.permission_code,
}) : p

// ─── Response helpers ─────────────────────────────────────────────────────────
const wrapList = async (promise) => {
  const res = await promise
  return { ...res, data: (res.data || []).map(fromBackend) }
}
const wrapOne = async (promise) => {
  const res = await promise
  return { ...res, data: fromBackend(res.data) }
}
const wrapPermList = async (promise) => {
  const res = await promise
  return { ...res, data: (res.data || []).map(permFromBackend) }
}

// ─── Exports ──────────────────────────────────────────────────────────────────
export const getRoles            = (tid)              => wrapList(api.get(`/tenant/${tid}/roles`))
export const getRole             = (tid, rid)         => wrapOne(api.get(`/tenant/${tid}/roles/${rid}`))
export const createRole          = (tid, data)        => wrapOne(api.post(`/tenant/${tid}/roles`, toBackend(data)))
export const updateRole          = (tid, rid, data)   => wrapOne(api.put(`/tenant/${tid}/roles/${rid}`, toBackend(data)))
export const deleteRole          = (tid, rid)         => api.delete(`/tenant/${tid}/roles/${rid}`)
export const activateRole        = (tid, rid)         => wrapOne(api.patch(`/tenant/${tid}/roles/${rid}/activate`))
export const deactivateRole      = (tid, rid)         => wrapOne(api.patch(`/tenant/${tid}/roles/${rid}/deactivate`))
export const getRoleUsers        = (tid, rid)         => api.get(`/tenant/${tid}/roles/${rid}/users`)
export const getPermissions      = (tid)              => wrapPermList(api.get(`/tenant/${tid}/permissions`))
export const getRolePermissions  = (tid, rid)         => wrapPermList(api.get(`/tenant/${tid}/roles/${rid}/permissions`))
export const assignPermission    = (tid, rid, pid)    => api.post(`/tenant/${tid}/roles/${rid}/permissions/${pid}`)
export const revokePermission    = (tid, rid, pid)    => api.delete(`/tenant/${tid}/roles/${rid}/permissions/${pid}`)
export const assignPermissions   = async (tid, rid, permIds) => {
  return Promise.all(permIds.map(pid => api.post(`/tenant/${tid}/roles/${rid}/permissions/${pid}`)))
}
