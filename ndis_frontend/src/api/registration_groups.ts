import api from './axios'

// ─── Registration Groups ──────────────────────────────────────────────────────
// Backend routes:
//   GET    /tenant/{tid}/registration-groups
//   POST   /tenant/{tid}/registration-groups   { registration_group_code, registration_group_name, is_active }
//   PUT    /tenant/{tid}/registration-groups/{id}
//   DELETE /tenant/{tid}/registration-groups/{id}

export const getRegistrationGroups    = (tid)           => api.get(`/tenant/${tid}/registration-groups`)
export const createRegistrationGroup  = (tid, data)     => api.post(`/tenant/${tid}/registration-groups`, data)
export const updateRegistrationGroup  = (tid, id, data) => api.put(`/tenant/${tid}/registration-groups/${id}`, data)
export const deleteRegistrationGroup  = (tid, id)       => api.delete(`/tenant/${tid}/registration-groups/${id}`)
