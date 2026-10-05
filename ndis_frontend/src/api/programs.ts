import api from './axios'

// ─── Field-name transformers ──────────────────────────────────────────────────
// Backend uses: funding_type, program_id
// Frontend uses: program_type, id

const toBackend = (data) => ({
  program_name: data.program_name,
  program_code: data.program_code
    || data.program_name.toUpperCase().replace(/[^A-Z0-9]/g, '-').slice(0, 8) + '-01',
  description: data.description || undefined,
  funding_type: data.program_type || data.funding_type || 'NDIS',
  is_active: data.is_active !== false,
  branch_ids: data.branch_ids || [],
})

const fromBackend = (p) => p ? ({
  ...p,
  id: p.program_id,           // frontend key
  program_type: p.funding_type,
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

// ─── Exports ──────────────────────────────────────────────────────────────────
export const getPrograms   = (tid)            => wrapList(api.get(`/tenant/${tid}/programs`))
export const createProgram = (tid, data)      => wrapOne(api.post(`/tenant/${tid}/programs`, toBackend(data)))
export const updateProgram = (tid, pid, data) => wrapOne(api.put(`/tenant/${tid}/programs/${pid}`, toBackend(data)))
export const deleteProgram = (tid, pid)       => api.delete(`/tenant/${tid}/programs/${pid}`)
