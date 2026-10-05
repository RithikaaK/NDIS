import api from './axios'

export const signupRegistered    = (data)            => api.post('/tenant/signup/registered', data)
export const signupNonRegistered = (data)            => api.post('/tenant/signup/non-registered', data)
export const checkEmailDomain   = (email)            => api.get('/tenant/check-domain', { params: { email } })
export const getPlans            = ()                => api.get('/plans')
export const getTenant           = (id)              => api.get(`/tenant/${id}`)
export const updateTenant        = (id, data)        => api.put(`/tenant/${id}`, data)

// Contacts
export const getContacts         = (id)              => api.get(`/tenant/${id}/contacts`)
export const createContact       = (id, data)        => api.post(`/tenant/${id}/contacts`, data)
export const updateContact       = (id, cid, data)   => api.put(`/tenant/${id}/contacts/${cid}`, data)
export const deleteContact       = (id, cid)         => api.delete(`/tenant/${id}/contacts/${cid}`)

// Addresses
export const getAddresses        = (id)              => api.get(`/tenant/${id}/addresses`)
export const createAddress       = (id, data)        => api.post(`/tenant/${id}/addresses`, data)
export const updateAddress       = (id, aid, data)   => api.put(`/tenant/${id}/addresses/${aid}`, data)
export const deleteAddress       = (id, aid)         => api.delete(`/tenant/${id}/addresses/${aid}`)

// Config
export const getConfig           = (id)              => api.get(`/tenant/${id}/config`)
export const updateConfig        = (id, data)        => api.put(`/tenant/${id}/config`, data)

// Audit logs — params: { user_id, action, table_name, record_id, from, to, skip, limit }
export const getAuditLogs        = (id, params)      => api.get(`/tenant/${id}/audit-logs`, { params })

// Subscription
export const getSubscription     = (id)              => api.get(`/tenant/${id}/subscription`)
export const getSubscriptionPlans = (id)             => api.get(`/tenant/${id}/subscription/plans`)
export const changeSubscription  = (id, data)        => api.put(`/tenant/${id}/subscription`, data)
// data shape: { plan_code: 'BASIC' | 'PROFESSIONAL' | 'ENTERPRISE', billing_cycle: 'Monthly' | 'Annual' }
