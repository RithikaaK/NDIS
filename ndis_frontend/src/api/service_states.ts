import api from './axios'

// ─── Service States ───────────────────────────────────────────────────────────
// Backend routes:
//   GET    /tenant/{tid}/service-states
//   POST   /tenant/{tid}/service-states        { state_code, is_active }
//   PUT    /tenant/{tid}/service-states/{id}   { is_active }
//   DELETE /tenant/{tid}/service-states/{id}

export const getServiceStates    = (tid)              => api.get(`/tenant/${tid}/service-states`)
export const createServiceState  = (tid, data)        => api.post(`/tenant/${tid}/service-states`, data)
export const updateServiceState  = (tid, id, data)    => api.put(`/tenant/${tid}/service-states/${id}`, data)
export const deleteServiceState  = (tid, id)          => api.delete(`/tenant/${tid}/service-states/${id}`)
