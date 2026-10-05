import api from './axios'

// ─── Field-name transformers ──────────────────────────────────────────────────
const toBackend = (data: any) => ({
  branch_name:      data.branch_name,
  branch_code:      data.branch_code
    || data.branch_name.toUpperCase().replace(/[^A-Z0-9]/g, '-').slice(0, 10),
  branch_type:      data.branch_type      || null,
  parent_branch_id: data.parent_branch_id || null,
  branch_status:    data.branch_status    || 'Active',
  phone:            data.phone            || null,
  email:            data.email            || null,
  address_line1:    data.address_line1    || null,
  address_line2:    data.address_line2    || null,
  suburb:           data.suburb           || null,
  state_code:       data.state_code       || null,
  postcode:         data.postcode         || null,
  country:          data.country          || null,
  timezone:         data.timezone         || null,
  operating_hours:  data.operating_hours  || null,
  facilities:       data.facilities       || null,
  notes:            data.notes            || null,
  is_head_office:   data.is_head_office   || false,
  is_active:        data.is_active !== false,
  contact_person:   data.contact_person   || null,
  contact_title:    data.contact_title    || null,
  contact_phone:    data.contact_phone    || null,
  contact_mobile:   data.contact_mobile   || null,
  contact_email:    data.contact_email    || null,
})

const fromBackend = (b: any) => b ? ({ ...b, id: b.branch_id }) : b

// ─── Response helpers ─────────────────────────────────────────────────────────
const wrapList = async (promise: Promise<any>) => {
  const res = await promise
  return { ...res, data: (res.data || []).map(fromBackend) }
}
const wrapOne = async (promise: Promise<any>) => {
  const res = await promise
  return { ...res, data: fromBackend(res.data) }
}

// ─── Core CRUD ────────────────────────────────────────────────────────────────
export const getBranches  = (tid: number)                    => wrapList(api.get(`/tenant/${tid}/branches`))
export const getBranch    = (tid: number, bid: any)          => wrapOne(api.get(`/tenant/${tid}/branches/${bid}`))
export const createBranch = (tid: number, data: any)         => wrapOne(api.post(`/tenant/${tid}/branches`, toBackend(data)))
export const updateBranch = (tid: number, bid: any, data: any) => wrapOne(api.put(`/tenant/${tid}/branches/${bid}`, toBackend(data)))
export const deleteBranch = (tid: number, bid: any)          => api.delete(`/tenant/${tid}/branches/${bid}`)

// ─── 3.6 Staff assignments ────────────────────────────────────────────────────
export const getBranchStaff = (tid: number, bid: any) => api.get(`/tenant/${tid}/branches/${bid}/staff`)

// ─── 3.8 Program mappings ─────────────────────────────────────────────────────
export const getBranchPrograms      = (tid: number, bid: any)              => api.get(`/tenant/${tid}/branches/${bid}/programs`)
export const assignProgramToBranch  = (tid: number, bid: any, pid: number) => api.post(`/tenant/${tid}/branches/${bid}/programs/${pid}`)
export const removeProgramFromBranch = (tid: number, bid: any, pid: number) => api.delete(`/tenant/${tid}/branches/${bid}/programs/${pid}`)
