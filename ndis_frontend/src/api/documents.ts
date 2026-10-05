import api from './axios'

// ─── Tenant Documents ─────────────────────────────────────────────────────────
// Backend routes:
//   GET    /tenant/{tid}/documents
//   POST   /tenant/{tid}/documents   { document_category, document_name, file_path, file_size_kb, mime_type, linked_to, expiry_date }
//   PUT    /tenant/{tid}/documents/{id}  { document_category?, document_name?, linked_to?, expiry_date? }
//   DELETE /tenant/{tid}/documents/{id}   (soft-delete)

export const getDocuments    = (tid: number, params?: any)              => api.get(`/tenant/${tid}/documents`, { params })
export const getDocument     = (tid: number, id: number)               => api.get(`/tenant/${tid}/documents/${id}`)
export const createDocument  = (tid: number, data: any)                => api.post(`/tenant/${tid}/documents`, data)
export const updateDocument  = (tid: number, id: number, data: any)   => api.put(`/tenant/${tid}/documents/${id}`, data)
export const deleteDocument  = (tid: number, id: number)               => api.delete(`/tenant/${tid}/documents/${id}`)
// params for getDocuments: { category?, search?, skip?, limit? }
