import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { useAuth } from '@/context/AuthContext'
import { getBranch, updateBranch, getBranches, getBranchPrograms, assignProgramToBranch, removeProgramFromBranch } from '@/api/branches'
import { getPrograms } from '@/api/programs'
import { getUsers, createUser, patchUser, deleteUser, getUserRoles } from '@/api/users'
import { getRoles } from '@/api/roles'
import {
  Edit2, MapPin, Users, Layers, GitBranch, Clock, Building2,
  ToggleLeft, ToggleRight, ExternalLink, Plus, Trash2, Network,
  ChevronRight, Info, Settings,
} from 'lucide-react'

const STATES      = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
const COUNTRIES   = ['Australia', 'New Zealand', 'Other']
const BRANCH_TYPES   = ['Head Office', 'Branch Office', 'Service Centre', 'Community Hub', 'Day Programme', 'Respite House', 'Administrative Office', 'Other']
const BRANCH_STATUSES = ['Active', 'Inactive', 'Temporarily Closed', 'Permanently Closed']
const AU_TIMEZONES   = ['Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'Australia/Adelaide', 'Australia/Perth', 'Australia/Darwin', 'Australia/Hobart']

const inputCls  = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls  = "text-xs font-semibold text-slate-600 uppercase tracking-wide"
const textareaCls = "w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all resize-none"

type Tab = 'overview' | 'location' | 'contact' | 'hierarchy' | 'programs' | 'users'
type EditMode = 'overview' | 'contact' | 'address' | 'location' | null

const statusStyle = (st?: string | null) => {
  if (!st || st === 'Active') return { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' }
  if (st === 'Temporarily Closed') return { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-400' }
  if (st === 'Permanently Closed') return { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' }
  return { bg: 'bg-slate-100', text: 'text-slate-500', dot: 'bg-slate-400' }
}

const Field = ({ label, value }: { label: string; value?: string | null }) => (
  <div className="py-3 border-b border-slate-100 last:border-b-0">
    <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-0.5">{label}</p>
    <p className="text-sm text-slate-800 whitespace-pre-line">{value || '—'}</p>
  </div>
)

const SectionHeader = ({ title, onEdit }: { title: string; onEdit: () => void }) => (
  <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
    <h2 className="text-sm font-semibold text-slate-700">{title}</h2>
    <button
      onClick={onEdit}
      className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium border border-slate-200 rounded-lg text-slate-500 hover:bg-slate-50 transition-colors"
    >
      <Edit2 className="h-3 w-3" /> Edit
    </button>
  </div>
)

// ── Working Hours ────────────────────────────────────────────────────────────
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const
type DayKey = typeof DAYS[number]
type DaySchedule = { open: boolean; from: string; to: string }
type WeekSchedule = Record<DayKey, DaySchedule>

const DEFAULT_HOURS: WeekSchedule = {
  Mon: { open: true,  from: '09:00', to: '17:00' },
  Tue: { open: true,  from: '09:00', to: '17:00' },
  Wed: { open: true,  from: '09:00', to: '17:00' },
  Thu: { open: true,  from: '09:00', to: '17:00' },
  Fri: { open: true,  from: '09:00', to: '17:00' },
  Sat: { open: false, from: '09:00', to: '13:00' },
  Sun: { open: false, from: '',      to: ''       },
}

const parseHours = (raw?: string | null): WeekSchedule | null => {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object' && DAYS.every(d => d in parsed)) return parsed as WeekSchedule
  } catch { /* not JSON – legacy free text */ }
  return null
}

const fmt12 = (t: string) => {
  if (!t) return ''
  const [h, m] = t.split(':').map(Number)
  const ampm = h >= 12 ? 'pm' : 'am'
  const h12  = h % 12 || 12
  return m === 0 ? `${h12}${ampm}` : `${h12}:${String(m).padStart(2, '0')}${ampm}`
}

const WorkingHoursDisplay = ({ raw }: { raw?: string | null }) => {
  const schedule = parseHours(raw)
  if (!schedule) return <p className="text-sm text-slate-800 whitespace-pre-line">{raw || '—'}</p>
  return (
    <div className="space-y-1.5 mt-1">
      {DAYS.map(day => {
        const d = schedule[day]
        return (
          <div key={day} className="flex items-center gap-3 text-sm">
            <span className="w-8 text-slate-400 font-medium text-xs shrink-0">{day}</span>
            {d.open
              ? <span className="text-slate-800 text-sm">{fmt12(d.from)} – {fmt12(d.to)}</span>
              : <span className="text-slate-400 text-sm">Closed</span>
            }
          </div>
        )
      })}
    </div>
  )
}

const WorkingHoursEditor = ({ value, onChange }: { value?: string | null; onChange: (v: string) => void }) => {
  const [schedule, setSchedule] = useState<WeekSchedule>(() => parseHours(value) ?? { ...DEFAULT_HOURS })

  const update = (day: DayKey, patch: Partial<DaySchedule>) => {
    const next = { ...schedule, [day]: { ...schedule[day], ...patch } } as WeekSchedule
    setSchedule(next)
    onChange(JSON.stringify(next))
  }

  return (
    <div className="space-y-2">
      {DAYS.map(day => {
        const d = schedule[day]
        return (
          <div key={day} className="flex items-center gap-2.5 min-w-0">
            <span className="w-8 text-xs font-semibold text-slate-500 shrink-0">{day}</span>
            <button
              type="button"
              onClick={() => update(day, { open: !d.open })}
              className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors ${d.open ? 'bg-emerald-500' : 'bg-slate-200'}`}
            >
              <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${d.open ? 'translate-x-4' : 'translate-x-0'}`} />
            </button>
            {d.open ? (
              <>
                <input
                  type="time"
                  value={d.from}
                  onChange={e => update(day, { from: e.target.value })}
                  className="h-7 px-2 rounded border border-slate-200 bg-slate-50 text-xs focus:outline-none focus:ring-1 focus:ring-purple-400 w-24 shrink-0"
                />
                <span className="text-xs text-slate-400 shrink-0">to</span>
                <input
                  type="time"
                  value={d.to}
                  onChange={e => update(day, { to: e.target.value })}
                  className="h-7 px-2 rounded border border-slate-200 bg-slate-50 text-xs focus:outline-none focus:ring-1 focus:ring-purple-400 w-24 shrink-0"
                />
              </>
            ) : (
              <span className="text-xs text-slate-400">Closed</span>
            )}
          </div>
        )
      })}
    </div>
  )
}

const SaveBar = ({ onSave, onCancel, isPending }: any) => (
  <div className="flex gap-3 pt-4 border-t border-slate-100">
    <button
      onClick={onSave}
      disabled={isPending}
      className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
    >
      {isPending && <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
      {isPending ? 'Saving…' : 'Save changes'}
    </button>
    <button onClick={onCancel} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
      Cancel
    </button>
  </div>
)

export default function BranchDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const queryClient = useQueryClient()

  const [tab, setTab]           = useState<Tab>('overview')
  const [editMode, setEditMode] = useState<EditMode>(null)
  const [form, setForm]         = useState<any>({})

  // Programs
  const [addProgramOpen, setAddProgramOpen]     = useState(false)
  const [editProgramOpen, setEditProgramOpen]   = useState(false)
  const [editProgramId, setEditProgramId]       = useState<number | null>(null)
  const [programForm, setProgramForm] = useState({ program_name: '', support_category: '', funding_type: '', is_active: true })
  const [assignProgramId, setAssignProgramId]   = useState<number | null>(null)

  // Users
  const [addUserOpen, setAddUserOpen]       = useState(false)
  const [editUserOpen, setEditUserOpen]     = useState(false)
  const [editingUser, setEditingUser]       = useState<any>(null)
  const [userSearch, setUserSearch]         = useState('')
  const [userRoleFilter, setUserRoleFilter] = useState('')
  const [userStatusFilter, setUserStatusFilter] = useState('')
  const [userForm, setUserForm]       = useState({ first_name: '', last_name: '', email: '', phone: '', selected_role_ids: [] as number[], is_active: true })
  const [editUserForm, setEditUserForm] = useState({ first_name: '', last_name: '', email: '', phone: '', selected_role_ids: [] as number[], password: '', is_active: true })

  const [toast, setToast] = useState('')
  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3000) }
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['branch', tenantId, id] })
    queryClient.invalidateQueries({ queryKey: ['branches', tenantId] })
  }

  // ── Queries ──────────────────────────────────────────────────────────────────
  const { data: branch, isLoading } = useQuery({
    queryKey: ['branch', tenantId, id],
    queryFn: () => getBranch(tenantId, id).then(r => r.data),
    enabled: !!tenantId && !!id,
  })

  // All branches (for hierarchy parent lookup)
  const { data: allBranches = [] } = useQuery({
    queryKey: ['branches', tenantId],
    queryFn: () => getBranches(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  // Programs at branch (via program_branch table)
  const { data: branchPrograms = [], isLoading: bpLoading } = useQuery({
    queryKey: ['branch-programs', tenantId, id],
    queryFn: () => getBranchPrograms(tenantId, id).then(r => r.data || []),
    enabled: !!tenantId && !!id,
  })

  // All programs (for assign dropdown)
  const { data: allPrograms = [] } = useQuery({
    queryKey: ['programs', tenantId],
    queryFn: () => getPrograms(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  // Users at this branch
  const { data: branchUsers = [], isLoading: usersLoading } = useQuery({
    queryKey: ['users', tenantId, id],
    queryFn: () => getUsers(tenantId, { branch_id: id }).then(r => r.data || []),
    enabled: !!tenantId && !!id,
  })

  // Roles
  const { data: roles = [] } = useQuery({
    queryKey: ['roles', tenantId],
    queryFn: () => getRoles(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  // ── Mutations ────────────────────────────────────────────────────────────────
  const saveMut = useMutation({
    mutationFn: (payload: any) => updateBranch(tenantId, id, payload),
    onSuccess: () => { invalidate(); setEditMode(null); flash('Saved successfully.') },
    onError: () => flash('Failed to save.'),
  })

  const assignProgramMut = useMutation({
    mutationFn: (pid: number) => assignProgramToBranch(tenantId, id, pid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-programs', tenantId, id] })
      setAddProgramOpen(false)
      setAssignProgramId(null)
      flash('Program assigned to branch.')
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to assign program.'),
  })

  const removeProgramMut = useMutation({
    mutationFn: (pid: number) => removeProgramFromBranch(tenantId, id, pid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-programs', tenantId, id] })
      flash('Program removed from branch.')
    },
    onError: () => flash('Failed to remove program.'),
  })

  const addUserMut = useMutation({
    mutationFn: (payload: any) => createUser(tenantId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', tenantId, id] })
      setAddUserOpen(false)
      flash('User added to branch.')
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to add user.'),
  })

  const updateUserMut = useMutation({
    mutationFn: ({ uid, payload }: { uid: string; payload: any }) => {
      const fields: any = { is_active: payload.is_active }
      if (payload.email)      fields.email      = payload.email.trim()
      if (payload.first_name) fields.first_name = payload.first_name.trim()
      if (payload.last_name)  fields.last_name  = payload.last_name.trim()
      fields.mobile    = payload.phone ? payload.phone.trim() : null
      fields.job_title = payload.role  ? payload.role.trim()  : null
      fields.role_ids  = payload.role_ids ?? []
      if (payload.password) fields.password = payload.password
      return patchUser(tenantId, uid, fields)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', tenantId, id] })
      setEditUserOpen(false)
      flash('User updated.')
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to update user.'),
  })

  const deleteUserMut = useMutation({
    mutationFn: (uid: string) => deleteUser(tenantId, uid),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['users', tenantId, id] }); flash('User removed.') },
    onError: () => flash('Cannot delete this user.'),
  })

  // ── Helpers ──────────────────────────────────────────────────────────────────
  const openEdit = (mode: EditMode) => { setForm({ ...branch }); setEditMode(mode) }
  const closeEdit = () => setEditMode(null)
  const save = () => saveMut.mutate(form)

  const changeStatus = (newStatus: string) => {
    if (!branch) return
    if (!confirm(`Change status to "${newStatus}"?`)) return
    saveMut.mutate({ ...branch, branch_status: newStatus, is_active: newStatus === 'Active' })
  }

  const openEditUser = async (u: any) => {
    const preselected: number[] = (u.role_ids && u.role_ids.length > 0)
      ? u.role_ids
      : (() => {
          const m = roles.find((r: any) => r.role_name?.trim().toLowerCase() === (u.job_title || '').trim().toLowerCase())
          return m ? [m.role_id] : []
        })()
    setEditingUser(u)
    setEditUserForm({ first_name: u.first_name || '', last_name: u.last_name || '', email: u.email || '', phone: u.mobile || u.phone || '', selected_role_ids: preselected, password: '', is_active: u.is_active !== false })
    setEditUserOpen(true)
    if (!u.role_ids || u.role_ids.length === 0) {
      try {
        const res = await getUserRoles(tenantId, u.id || u.user_id)
        const roleIds = (res.data || []).map((r: any) => r.role_id)
        if (roleIds.length > 0) setEditUserForm(prev => ({ ...prev, selected_role_ids: roleIds }))
      } catch { /* fallback */ }
    }
  }

  const mapsUrl = branch
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
        [branch.address_line1, branch.suburb, branch.state_code, branch.postcode, 'Australia'].filter(Boolean).join(' ')
      )}`
    : '#'

  // Hierarchy
  const parentBranch = allBranches.find((b: any) => b.branch_id === branch?.parent_branch_id)
  const childBranches = allBranches.filter((b: any) => b.parent_branch_id === branch?.branch_id && !b.is_deleted)

  // Available programs to assign (not already linked)
  const linkedProgramIds = new Set(branchPrograms.map((p: any) => p.program_id))
  const availablePrograms = allPrograms.filter((p: any) => !linkedProgramIds.has(p.program_id) && !p.is_deleted)

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'overview',  label: 'Overview',   icon: <Info className="h-3.5 w-3.5" /> },
    { key: 'location',  label: 'Location',   icon: <MapPin className="h-3.5 w-3.5" /> },
    { key: 'contact',   label: 'Contact',    icon: <Building2 className="h-3.5 w-3.5" /> },
    { key: 'hierarchy', label: 'Hierarchy',  icon: <Network className="h-3.5 w-3.5" /> },
    { key: 'programs',  label: 'Programs',   icon: <Layers className="h-3.5 w-3.5" /> },
    { key: 'users',     label: 'Staff',      icon: <Users className="h-3.5 w-3.5" /> },
  ]

  // ── Loading / not found ───────────────────────────────────────────────────────
  if (isLoading) return (
    <Layout title="Branch">
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-slate-100 rounded w-1/4" />
        <div className="h-8 bg-slate-100 rounded w-1/3" />
        <div className="grid grid-cols-4 gap-4 mt-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-slate-100 rounded-xl" />)}
        </div>
      </div>
    </Layout>
  )

  if (!branch) return (
    <Layout title="Branch">
      <div className="text-center py-20 text-slate-400">Branch not found.</div>
    </Layout>
  )

  const st = statusStyle(branch.branch_status)

  return (
    <Layout
      title={branch.branch_name}
      breadcrumbs={[
        { label: 'Branches', path: '/branches' },
        { label: branch.branch_name },
      ]}
    >
      <div className="space-y-5 animate-fade-in">

        {/* Toast */}
        {toast && (
          <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />{toast}
          </div>
        )}

        {/* Page header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-slate-400 mb-1">Branch</p>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-semibold text-slate-900">{branch.branch_name}</h1>
              {branch.is_head_office && (
                <span className="text-xs bg-purple-100 text-purple-700 rounded px-2 py-0.5 font-medium">Head office</span>
              )}
              {branch.branch_type && (
                <span className="text-xs bg-blue-50 text-blue-700 rounded px-2 py-0.5 font-medium">{branch.branch_type}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 mt-1">
            {/* Status change dropdown */}
            <div className="relative group">
              <button className={`flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium border transition-colors ${st.bg} ${st.text} border-current`}>
                <span className={`h-1.5 w-1.5 rounded-full ${st.dot}`} />
                {branch.branch_status || 'Active'}
                <svg className="h-3 w-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </button>
              <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-slate-200 rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-20">
                {BRANCH_STATUSES.map(s => {
                  const ss = statusStyle(s)
                  return (
                    <button
                      key={s}
                      onClick={() => changeStatus(s)}
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-xs hover:bg-slate-50 first:rounded-t-xl last:rounded-b-xl transition-colors"
                    >
                      <span className={`h-2 w-2 rounded-full ${ss.dot}`} />
                      <span className={ss.text}>{s}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: <Users className="h-4 w-4 text-purple-400" />,  label: 'Staff',    value: usersLoading ? '…' : String(branchUsers.length) },
            { icon: <Layers className="h-4 w-4 text-purple-400" />, label: 'Programs', value: bpLoading ? '…' : String(branchPrograms.length) },
            { icon: <MapPin className="h-4 w-4 text-purple-400" />, label: 'State',    value: branch.state_code || '—' },
            { icon: <Network className="h-4 w-4 text-purple-400" />, label: 'Children', value: String(childBranches.length) },
          ].map(({ icon, label, value }) => (
            <div key={label} className="bg-white border border-slate-100 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">{icon}<span className="text-xs text-slate-400">{label}</span></div>
              <p className="text-2xl font-semibold text-slate-900">{value}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm border-b-2 transition-colors whitespace-nowrap ${
                tab === t.key ? 'border-purple-700 text-purple-700 font-medium' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t.icon}{t.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {tab === 'overview' && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5">
            <SectionHeader title="Branch details" onEdit={() => openEdit('overview')} />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
              <Field label="Branch name"    value={branch.branch_name} />
              <Field label="Branch code"    value={branch.branch_code} />
              <Field label="Location type"  value={branch.branch_type} />
              <Field label="Status"         value={branch.branch_status || 'Active'} />
              <Field label="Phone"          value={branch.phone} />
              <Field label="Email"          value={branch.email} />
              <Field label="Timezone"       value={branch.timezone} />
              <div className="py-3 border-b border-slate-100">
                <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-0.5">Head office</p>
                <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${branch.is_head_office ? 'bg-purple-50 text-purple-700' : 'bg-slate-50 text-slate-500'}`}>
                  {branch.is_head_office ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ── LOCATION TAB ── */}
        {tab === 'location' && (
          <div className="space-y-4">
            {/* Address */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5">
              <SectionHeader title="Branch address" onEdit={() => openEdit('address')} />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
                <Field label="Address line 1" value={branch.address_line1} />
                <Field label="Address line 2" value={branch.address_line2} />
                <Field label="Suburb"         value={branch.suburb} />
                <Field label="State"          value={branch.state_code} />
                <Field label="Postcode"       value={branch.postcode} />
                <Field label="Country"        value={branch.country} />
              </div>
              {(branch.address_line1 || branch.suburb) && (
                <>
                  <div className="mt-4 rounded-xl border border-slate-200 h-28 bg-slate-50 flex items-center justify-center">
                    <div className="text-center">
                      <MapPin className="h-7 w-7 text-blue-400 mx-auto mb-1" />
                      <p className="text-xs text-slate-500">{[branch.address_line1, branch.suburb, branch.state_code, branch.postcode].filter(Boolean).join(', ')}</p>
                    </div>
                  </div>
                  <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 mt-3 transition-colors">
                    <ExternalLink className="h-3.5 w-3.5" /> Open in Google Maps
                  </a>
                </>
              )}
            </div>

            {/* Operating hours + Facilities + Notes */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5">
              <SectionHeader title="Location details" onEdit={() => openEdit('location')} />
              <div className="space-y-0">
                <Field label="Timezone" value={branch.timezone} />
                <div className="py-3 border-b border-slate-100 last:border-b-0">
                  <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-0.5">Operating hours</p>
                  <WorkingHoursDisplay raw={branch.operating_hours} />
                </div>
                <Field label="Facilities" value={branch.facilities} />
                <Field label="Notes"      value={branch.notes} />
              </div>
            </div>
          </div>
        )}

        {/* ── CONTACT TAB ── */}
        {tab === 'contact' && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5">
            <SectionHeader title="Branch contact" onEdit={() => openEdit('contact')} />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
              <Field label="Contact person"   value={branch.contact_person} />
              <Field label="Position / title" value={branch.contact_title} />
              <Field label="Phone"            value={branch.contact_phone} />
              <Field label="Mobile"           value={branch.contact_mobile} />
              <div className="sm:col-span-2 py-3">
                <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-0.5">Email</p>
                <p className="text-sm text-slate-800">{branch.contact_email || '—'}</p>
              </div>
            </div>
          </div>
        )}

        {/* ── HIERARCHY TAB ── */}
        {tab === 'hierarchy' && (
          <div className="space-y-4">
            {/* Parent branch */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-700">Parent location</h2>
                <button
                  onClick={() => openEdit('overview')}
                  className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium border border-slate-200 rounded-lg text-slate-500 hover:bg-slate-50 transition-colors"
                >
                  <Edit2 className="h-3 w-3" /> Change
                </button>
              </div>
              {parentBranch ? (
                <button
                  onClick={() => navigate(`/branches/${parentBranch.branch_id}`)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-left"
                >
                  <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                    <GitBranch className="h-5 w-5 text-purple-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800">{parentBranch.branch_name}</p>
                    <p className="text-xs text-slate-400">{parentBranch.branch_type || 'Branch'} · {parentBranch.branch_status || 'Active'}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </button>
              ) : (
                <p className="text-sm text-slate-400 py-2">This is a top-level branch (no parent).</p>
              )}
            </div>

            {/* Child branches */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5">
              <div className="mb-4 pb-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-700">Sub-locations ({childBranches.length})</h2>
              </div>
              {childBranches.length === 0 ? (
                <p className="text-sm text-slate-400 py-2">No sub-locations linked to this branch.</p>
              ) : (
                <div className="space-y-2">
                  {childBranches.map((b: any) => {
                    const css = statusStyle(b.branch_status)
                    return (
                      <button
                        key={b.branch_id}
                        onClick={() => navigate(`/branches/${b.branch_id}`)}
                        className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-left"
                      >
                        <div className="h-9 w-9 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                          <GitBranch className="h-4 w-4 text-purple-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-800">{b.branch_name}</p>
                          <p className="text-xs text-slate-400">{b.branch_type || 'Branch'}</p>
                        </div>
                        <span className={`flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full ${css.bg} ${css.text}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${css.dot}`} />
                          {b.branch_status || 'Active'}
                        </span>
                        <ChevronRight className="h-4 w-4 text-slate-300" />
                      </button>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Hierarchy visual tree */}
            {(parentBranch || childBranches.length > 0) && (
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5">
                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Tree view</h2>
                <div className="space-y-1 text-sm font-mono">
                  {parentBranch && (
                    <div className="text-slate-400 text-xs">└── {parentBranch.branch_name} (parent)</div>
                  )}
                  <div className="flex items-center gap-1.5 text-purple-700 font-semibold text-xs">
                    {parentBranch && <span className="text-slate-300 ml-4">└── </span>}
                    <GitBranch className="h-3 w-3" /> {branch.branch_name} (this)
                  </div>
                  {childBranches.map((b: any) => (
                    <div key={b.branch_id} className="text-slate-400 text-xs ml-8">└── {b.branch_name}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── PROGRAMS TAB ── */}
        {tab === 'programs' && (
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
              <div>
                <h2 className="text-sm font-semibold text-slate-700">Programs at this location</h2>
                <p className="text-xs text-slate-400 mt-0.5">Manage which support programs are available here</p>
              </div>
              <button
                onClick={() => setAddProgramOpen(true)}
                className="flex items-center gap-1.5 h-8 px-3 bg-purple-800 hover:bg-purple-900 text-white text-xs font-medium rounded-lg transition-colors"
              >
                <Plus className="h-3.5 w-3.5" /> Assign program
              </button>
            </div>
            <div className="border border-slate-200 rounded-2xl overflow-hidden">
              <table className="w-full text-sm border-collapse">
                <thead className="bg-slate-50">
                  <tr>{['Program name', 'Funding type', 'Status', ''].map((h, i) => (
                    <th key={i} className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-4 py-3 border-b border-slate-200">{h}</th>
                  ))}</tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {bpLoading ? (
                    <tr><td colSpan={4} className="py-8 text-center text-slate-400 text-sm">Loading…</td></tr>
                  ) : branchPrograms.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-12 text-center">
                        <Layers className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                        <p className="text-sm text-slate-400">No programs linked to this branch yet.</p>
                      </td>
                    </tr>
                  ) : branchPrograms.map((p: any) => (
                    <tr key={p.program_branch_id} className="hover:bg-slate-50 group">
                      <td className="px-4 py-3 text-sm font-medium text-slate-700">{p.program_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-500">{p.funding_type || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2.5 py-0.5 rounded-full ${p.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${p.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                          {p.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => { if (confirm(`Remove "${p.program_name}" from this branch?`)) removeProgramMut.mutate(p.program_id) }}
                            className="h-7 w-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                            title="Remove"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── STAFF TAB ── */}
        {tab === 'users' && (() => {
          const totalUsers    = branchUsers.length
          const activeUsers   = branchUsers.filter((u: any) => u.is_active !== false).length
          const inactiveUsers = totalUsers - activeUsers
          const avatarColors  = [
            { bg: '#ede9fe', text: '#5b21b6' }, { bg: '#e0f2fe', text: '#075985' },
            { bg: '#fef9c3', text: '#854d0e' }, { bg: '#fce7f3', text: '#9d174d' },
            { bg: '#dcfce7', text: '#166534' }, { bg: '#ffedd5', text: '#9a3412' },
            { bg: '#e0e7ff', text: '#3730a3' }, { bg: '#fef3c7', text: '#92400e' },
          ]
          const getColor = (name: string) => avatarColors[name.charCodeAt(0) % avatarColors.length]
          const filteredUsers = branchUsers.filter((u: any) => {
            const name = `${u.first_name} ${u.last_name}`.toLowerCase()
            const matchSearch = !userSearch || name.includes(userSearch.toLowerCase()) || (u.email || '').toLowerCase().includes(userSearch.toLowerCase())
            const matchRole   = !userRoleFilter || (u.job_title || '') === userRoleFilter
            const matchStatus = !userStatusFilter || (userStatusFilter === 'active' ? u.is_active !== false : u.is_active === false)
            return matchSearch && matchRole && matchStatus
          })
          const roleOptions = [...new Set(branchUsers.map((u: any) => u.job_title).filter(Boolean))]
          return (
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-base font-semibold text-slate-800">Staff</h2>
                  <p className="text-xs text-slate-400 mt-0.5">Manage staff assigned to this location</p>
                </div>
                <button
                  onClick={() => { setUserForm({ first_name: '', last_name: '', email: '', phone: '', selected_role_ids: [], is_active: true }); setAddUserOpen(true) }}
                  className="flex items-center gap-1.5 h-8 px-3 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-lg transition-colors"
                >
                  <Plus className="h-3.5 w-3.5" /> Add staff
                </button>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Total', value: totalUsers, sub: 'Assigned', color: 'text-slate-800' },
                  { label: 'Active', value: activeUsers, sub: 'Currently active', color: 'text-emerald-600' },
                  { label: 'Inactive', value: inactiveUsers, sub: 'Deactivated', color: 'text-slate-400' },
                ].map(c => (
                  <div key={c.label} className="border border-slate-200 rounded-xl p-4">
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">{c.label}</p>
                    <p className={`text-2xl font-bold leading-none ${c.color}`}>{c.value}</p>
                    <p className="text-xs text-slate-400 mt-1.5">{c.sub}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 border border-slate-200 rounded-lg px-3 h-9 bg-white">
                  <svg width="13" height="13" fill="none" stroke="#94a3b8" strokeWidth="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                  <input
                    type="text"
                    placeholder="Search staff…"
                    value={userSearch}
                    onChange={e => setUserSearch(e.target.value)}
                    className="border-none outline-none text-xs bg-transparent text-slate-700 w-32 placeholder:text-slate-400"
                  />
                </div>
                <select
                  value={userRoleFilter}
                  onChange={e => setUserRoleFilter(e.target.value)}
                  className="h-9 px-3 pr-7 border border-slate-200 rounded-lg bg-white text-xs text-slate-600 outline-none appearance-none"
                  style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
                >
                  <option value="">All roles</option>
                  {roleOptions.map((r: any) => <option key={r}>{r}</option>)}
                </select>
                <select
                  value={userStatusFilter}
                  onChange={e => setUserStatusFilter(e.target.value)}
                  className="h-9 px-3 pr-7 border border-slate-200 rounded-lg bg-white text-xs text-slate-600 outline-none appearance-none"
                  style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
                >
                  <option value="">All statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm border-collapse" style={{ tableLayout: 'fixed' }}>
                  <colgroup>
                    <col style={{ width: '24%' }} /><col style={{ width: '16%' }} /><col style={{ width: '22%' }} /><col style={{ width: '14%' }} /><col style={{ width: '13%' }} /><col style={{ width: '11%' }} />
                  </colgroup>
                  <thead className="bg-slate-50">
                    <tr>{['Name', 'Role', 'Email', 'Phone', 'Status', 'Actions'].map((h, i) => (
                      <th key={i} className={`text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 py-3 border-b border-slate-200 ${i === 5 ? 'text-center' : ''}`}>{h}</th>
                    ))}</tr>
                  </thead>
                  <tbody>
                    {usersLoading ? (
                      <tr><td colSpan={6} className="py-8 text-center text-slate-400 text-sm">Loading…</td></tr>
                    ) : filteredUsers.length === 0 ? (
                      <tr><td colSpan={6} className="py-12 text-center text-slate-400 text-sm">No staff found.</td></tr>
                    ) : filteredUsers.map((u: any) => {
                      const initials = `${(u.first_name || '')[0] || ''}${(u.last_name || '')[0] || ''}`.toUpperCase()
                      const col = getColor(u.first_name || 'A')
                      const isActive = u.is_active !== false
                      return (
                        <tr key={u.id} className="hover:bg-slate-50 border-t border-slate-100 first:border-t-0">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0" style={{ background: col.bg, color: col.text }}>{initials}</div>
                              <div>
                                <p className="text-sm font-medium text-slate-800 leading-none">{u.first_name} {u.last_name}</p>
                                <p className="text-[11px] text-slate-400 mt-0.5">{(u.role_names && u.role_names.length > 0) ? u.role_names.join(', ') : (u.job_title || '')}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {(u.role_names && u.role_names.length > 0) ? (
                              <div className="flex flex-wrap gap-1">
                                {u.role_names.map((rn: string) => (
                                  <span key={rn} className="inline-block text-[11px] px-2.5 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-500 font-medium">{rn}</span>
                                ))}
                              </div>
                            ) : u.job_title ? (
                              <span className="inline-block text-[11px] px-2.5 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-500 font-medium">{u.job_title}</span>
                            ) : <span className="text-slate-300">—</span>}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-500 truncate">{u.email}</td>
                          <td className="px-4 py-3 text-xs text-slate-500">{u.mobile || u.phone || '—'}</td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${isActive ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isActive ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                              {isActive ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 justify-center">
                              <button onClick={() => openEditUser(u)} className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-purple-700 hover:border-purple-200 hover:bg-purple-50 transition-colors" title="Edit">
                                <Edit2 className="h-3 w-3" />
                              </button>
                              <button onClick={() => { if (confirm(`Delete ${u.first_name} ${u.last_name}?`)) deleteUserMut.mutate(u.id) }} className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors" title="Delete">
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })()}

      </div>

      {/* ── SLIDE-OVERS ───────────────────────────────────────────────────────── */}

      {/* Edit overview */}
      <SlideOver open={editMode === 'overview'} onClose={closeEdit} title="Edit branch details" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Branch Name *</label>
            <input className={inputCls} value={form.branch_name || ''} onChange={e => setForm({ ...form, branch_name: e.target.value })} placeholder="Sydney CBD Office" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Branch Code</label>
              <input className={inputCls} value={form.branch_code || ''} onChange={e => setForm({ ...form, branch_code: e.target.value })} placeholder="SYD-01" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Location type</label>
              <select className={selectCls} value={form.branch_type || ''} onChange={e => setForm({ ...form, branch_type: e.target.value })}>
                <option value="">Select type</option>
                {BRANCH_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Status</label>
              <select className={selectCls} value={form.branch_status || 'Active'} onChange={e => setForm({ ...form, branch_status: e.target.value, is_active: e.target.value === 'Active' })}>
                {BRANCH_STATUSES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Timezone</label>
              <select className={selectCls} value={form.timezone || ''} onChange={e => setForm({ ...form, timezone: e.target.value })}>
                <option value="">Select timezone</option>
                {AU_TIMEZONES.map(tz => <option key={tz}>{tz}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Phone</label>
              <input className={inputCls} value={form.phone || ''} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="02 9000 0000" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Email</label>
              <input className={inputCls} type="email" value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="branch@org.com.au" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Parent branch</label>
              <select className={selectCls} value={form.parent_branch_id || ''} onChange={e => setForm({ ...form, parent_branch_id: e.target.value ? parseInt(e.target.value) : null })}>
                <option value="">None (top-level)</option>
                {allBranches.filter((b: any) => b.branch_id !== branch.branch_id && !b.is_deleted).map((b: any) => (
                  <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2 pt-1">
              <input type="checkbox" id="hq-ov" checked={form.is_head_office || false} onChange={e => setForm({ ...form, is_head_office: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-purple-600" />
              <label htmlFor="hq-ov" className="text-sm font-medium text-slate-700">Head office</label>
            </div>
          </div>
          <SaveBar onSave={save} onCancel={closeEdit} isPending={saveMut.isPending} />
        </div>
      </SlideOver>

      {/* Edit address */}
      <SlideOver open={editMode === 'address'} onClose={closeEdit} title="Edit branch address" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Address line 1</label>
            <input className={inputCls} value={form.address_line1 || ''} onChange={e => setForm({ ...form, address_line1: e.target.value })} placeholder="123 Main Street" />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Address line 2</label>
            <input className={inputCls} value={form.address_line2 || ''} onChange={e => setForm({ ...form, address_line2: e.target.value })} placeholder="Suite 100" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Suburb</label>
              <input className={inputCls} value={form.suburb || ''} onChange={e => setForm({ ...form, suburb: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>State</label>
              <select className={selectCls} value={form.state_code || ''} onChange={e => setForm({ ...form, state_code: e.target.value })}>
                <option value="">Select state</option>
                {STATES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Postcode</label>
              <input className={inputCls} value={form.postcode || ''} onChange={e => setForm({ ...form, postcode: e.target.value })} maxLength={4} />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Country</label>
              <select className={selectCls} value={form.country || ''} onChange={e => setForm({ ...form, country: e.target.value })}>
                <option value="">Select country</option>
                {COUNTRIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <SaveBar onSave={save} onCancel={closeEdit} isPending={saveMut.isPending} />
        </div>
      </SlideOver>

      {/* Edit location details */}
      <SlideOver open={editMode === 'location'} onClose={closeEdit} title="Edit location details" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Timezone</label>
            <select className={selectCls} value={form.timezone || ''} onChange={e => setForm({ ...form, timezone: e.target.value })}>
              <option value="">Select timezone</option>
              {AU_TIMEZONES.map(tz => <option key={tz}>{tz}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className={labelCls}>Operating hours</label>
            <WorkingHoursEditor
              key={editMode === 'location' ? 'open' : 'closed'}
              value={form.operating_hours}
              onChange={v => setForm((f: any) => ({ ...f, operating_hours: v }))}
            />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Facilities available</label>
            <textarea
              className={textareaCls}
              rows={3}
              value={form.facilities || ''}
              onChange={e => setForm({ ...form, facilities: e.target.value })}
              placeholder="Wheelchair access, parking, meeting rooms…"
            />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Notes</label>
            <textarea
              className={textareaCls}
              rows={3}
              value={form.notes || ''}
              onChange={e => setForm({ ...form, notes: e.target.value })}
              placeholder="Any additional notes about this location…"
            />
          </div>
          <SaveBar onSave={save} onCancel={closeEdit} isPending={saveMut.isPending} />
        </div>
      </SlideOver>

      {/* Edit branch contact */}
      <SlideOver open={editMode === 'contact'} onClose={closeEdit} title="Edit branch contact" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Contact person</label>
              <input className={inputCls} value={form.contact_person || ''} onChange={e => setForm({ ...form, contact_person: e.target.value })} placeholder="Full name" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Position / title</label>
              <input className={inputCls} value={form.contact_title || ''} onChange={e => setForm({ ...form, contact_title: e.target.value })} placeholder="Branch Manager" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Phone</label>
              <input className={inputCls} value={form.contact_phone || ''} onChange={e => setForm({ ...form, contact_phone: e.target.value })} placeholder="02 9000 0000" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Mobile</label>
              <input className={inputCls} value={form.contact_mobile || ''} onChange={e => setForm({ ...form, contact_mobile: e.target.value })} placeholder="0400 000 000" />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Email</label>
            <input className={inputCls} type="email" value={form.contact_email || ''} onChange={e => setForm({ ...form, contact_email: e.target.value })} placeholder="contact@branch.com.au" />
          </div>
          <SaveBar onSave={save} onCancel={closeEdit} isPending={saveMut.isPending} />
        </div>
      </SlideOver>

      {/* Assign program slide-over */}
      <SlideOver open={addProgramOpen} onClose={() => setAddProgramOpen(false)} title="Assign program to branch" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Select program</label>
            <select
              className={selectCls}
              value={assignProgramId ?? ''}
              onChange={e => setAssignProgramId(e.target.value ? parseInt(e.target.value) : null)}
            >
              <option value="">Choose a program…</option>
              {availablePrograms.map((p: any) => (
                <option key={p.program_id} value={p.program_id}>{p.program_name}</option>
              ))}
            </select>
            {availablePrograms.length === 0 && (
              <p className="text-xs text-slate-400">All programs are already linked to this branch.</p>
            )}
          </div>
          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => assignProgramId && assignProgramMut.mutate(assignProgramId)}
              disabled={!assignProgramId || assignProgramMut.isPending}
              className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {assignProgramMut.isPending ? 'Assigning…' : 'Assign program'}
            </button>
            <button onClick={() => setAddProgramOpen(false)} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
          </div>
        </div>
      </SlideOver>

      {/* Add staff slide-over */}
      <SlideOver open={addUserOpen} onClose={() => setAddUserOpen(false)} title="Add staff member" subtitle={branch.branch_name}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>First name *</label>
              <input className={inputCls} value={userForm.first_name} onChange={e => setUserForm({ ...userForm, first_name: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Last name *</label>
              <input className={inputCls} value={userForm.last_name} onChange={e => setUserForm({ ...userForm, last_name: e.target.value })} />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Email *</label>
            <input className={inputCls} type="email" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Phone</label>
            <input className={inputCls} value={userForm.phone} onChange={e => setUserForm({ ...userForm, phone: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Roles</label>
            <div className="border border-slate-200 rounded-lg p-3 space-y-2 max-h-36 overflow-y-auto">
              {roles.map((r: any) => (
                <label key={r.role_id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={userForm.selected_role_ids.includes(r.role_id)}
                    onChange={e => setUserForm(prev => ({
                      ...prev,
                      selected_role_ids: e.target.checked
                        ? [...prev.selected_role_ids, r.role_id]
                        : prev.selected_role_ids.filter(id => id !== r.role_id)
                    }))}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-purple-600"
                  />
                  {r.role_name}
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => addUserMut.mutate({ ...userForm, branch_id: parseInt(id!), role_ids: userForm.selected_role_ids })}
              disabled={addUserMut.isPending || !userForm.first_name || !userForm.email}
              className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {addUserMut.isPending ? 'Adding…' : 'Add staff member'}
            </button>
            <button onClick={() => setAddUserOpen(false)} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
          </div>
        </div>
      </SlideOver>

      {/* Edit staff slide-over */}
      <SlideOver open={editUserOpen} onClose={() => setEditUserOpen(false)} title="Edit staff member" subtitle={editingUser ? `${editingUser.first_name} ${editingUser.last_name}` : ''}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>First name</label>
              <input className={inputCls} value={editUserForm.first_name} onChange={e => setEditUserForm({ ...editUserForm, first_name: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Last name</label>
              <input className={inputCls} value={editUserForm.last_name} onChange={e => setEditUserForm({ ...editUserForm, last_name: e.target.value })} />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Email</label>
            <input className={inputCls} type="email" value={editUserForm.email} onChange={e => setEditUserForm({ ...editUserForm, email: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Phone / mobile</label>
            <input className={inputCls} value={editUserForm.phone} onChange={e => setEditUserForm({ ...editUserForm, phone: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Roles</label>
            <div className="border border-slate-200 rounded-lg p-3 space-y-2 max-h-36 overflow-y-auto">
              {roles.map((r: any) => (
                <label key={r.role_id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editUserForm.selected_role_ids.includes(r.role_id)}
                    onChange={e => setEditUserForm(prev => ({
                      ...prev,
                      selected_role_ids: e.target.checked
                        ? [...prev.selected_role_ids, r.role_id]
                        : prev.selected_role_ids.filter(id => id !== r.role_id)
                    }))}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-purple-600"
                  />
                  {r.role_name}
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>New password (leave blank to keep)</label>
            <input className={inputCls} type="password" value={editUserForm.password} onChange={e => setEditUserForm({ ...editUserForm, password: e.target.value })} placeholder="Leave blank to keep current" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="edit-active" checked={editUserForm.is_active} onChange={e => setEditUserForm({ ...editUserForm, is_active: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-purple-600" />
            <label htmlFor="edit-active" className="text-sm font-medium text-slate-700">Active</label>
          </div>
          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => updateUserMut.mutate({ uid: editingUser?.id || editingUser?.user_id, payload: { ...editUserForm, role_ids: editUserForm.selected_role_ids } })}
              disabled={updateUserMut.isPending}
              className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {updateUserMut.isPending ? 'Saving…' : 'Save changes'}
            </button>
            <button onClick={() => setEditUserOpen(false)} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
          </div>
        </div>
      </SlideOver>

    </Layout>
  )
}
