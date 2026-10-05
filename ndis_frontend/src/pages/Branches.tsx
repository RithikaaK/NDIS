import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { SkeletonTable } from '@/components/ui/Skeleton'
import { useAuth } from '@/context/AuthContext'
import { usePermissions } from '@/hooks/usePermissions'
import { getBranches, createBranch } from '@/api/branches'
import { Plus, Search, GitBranch, MapPin, Phone, Mail, ChevronRight } from 'lucide-react'
// MapPin, Phone, Mail kept for list row meta

const STATES = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
const BRANCH_TYPES = ['Head Office', 'Branch Office', 'Service Centre', 'Community Hub', 'Day Programme', 'Respite House', 'Administrative Office', 'Other']
const empty = { branch_name: '', branch_code: '', branch_type: '', branch_status: 'Active', phone: '', email: '', address_line1: '', suburb: '', state_code: '', postcode: '', is_head_office: false, operating_hours: '' }

// ── Working Hours ─────────────────────────────────────────────────────────────
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

const WorkingHoursEditor = ({ value, onChange }: { value?: string | null; onChange: (v: string) => void }) => {
  const tryParse = (raw?: string | null): WeekSchedule | null => {
    if (!raw) return null
    try {
      const p = JSON.parse(raw)
      if (p && typeof p === 'object' && DAYS.every(d => d in p)) return p as WeekSchedule
    } catch { /* ignore */ }
    return null
  }
  const [schedule, setSchedule] = useState<WeekSchedule>(() => tryParse(value) ?? { ...DEFAULT_HOURS })

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
          <div key={day} className="flex items-center gap-2.5">
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

const inputCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls = "text-xs font-semibold text-slate-600 uppercase tracking-wide"

type FilterType = 'all' | 'active' | 'inactive'

export default function Branches() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { can } = usePermissions()

  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<FilterType>('all')
  const [slideOpen, setSlideOpen] = useState(false)
  const [form, setForm]     = useState<any>(empty)
  const [toast, setToast]   = useState('')

  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3000) }
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['branches', tenantId] })

  const { data: branches = [], isLoading } = useQuery({
    queryKey: ['branches', tenantId],
    queryFn: () => getBranches(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  const saveMut = useMutation({
    mutationFn: (payload: any) => createBranch(tenantId, payload),
    onSuccess: () => { invalidate(); setSlideOpen(false); flash('Branch created successfully.') },
    onError:   () => flash('Failed to create branch.'),
  })

  const openNew = () => { setForm(empty); setSlideOpen(true) }
  const save    = () => saveMut.mutate(form)

  const filtered = branches.filter((b: any) => {
    const matchSearch = `${b.branch_name} ${b.branch_code} ${b.suburb} ${b.email}`.toLowerCase().includes(search.toLowerCase())
    const matchFilter =
      filter === 'all' ? true :
      filter === 'active' ? b.is_active :
      !b.is_active
    return matchSearch && matchFilter
  })

  const activeCnt   = branches.filter((b: any) => b.is_active).length
  const inactiveCnt = branches.filter((b: any) => !b.is_active).length

  return (
    <Layout title="Branches">
      <div className="space-y-5 animate-fade-in">

        {/* Toast */}
        {toast && (
          <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl animate-fade-in flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />{toast}
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Branches</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {isLoading ? '…' : `${branches.length} branch${branches.length !== 1 ? 'es' : ''} across your organisation`}
            </p>
          </div>
          {can('branches:create') && (
            <button
              onClick={openNew}
              className="flex items-center gap-1.5 bg-purple-800 hover:bg-purple-900 text-white text-sm font-medium px-4 h-9 rounded-lg transition-colors shrink-0"
            >
              <Plus className="h-4 w-4" /> Add branch
            </button>
          )}
        </div>

        {/* Toolbar: search + filter toggle */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search branches…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full h-9 pl-8 pr-3 rounded-lg border border-slate-200 bg-white text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all"
            />
          </div>
          <div className="flex border border-slate-200 rounded-lg overflow-hidden text-sm shrink-0">
            {(['all', 'active', 'inactive'] as FilterType[]).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 h-9 font-medium capitalize border-r border-slate-200 last:border-r-0 transition-colors ${
                  filter === f
                    ? 'bg-purple-800 text-white'
                    : 'bg-white text-slate-500 hover:bg-slate-50'
                }`}
              >
                {f === 'all' ? `All (${branches.length})` : f === 'active' ? `Active (${activeCnt})` : `Inactive (${inactiveCnt})`}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        {isLoading ? (
          <SkeletonTable rows={5} cols={1} />
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center border border-slate-200 rounded-2xl bg-white">
            <div className="h-14 w-14 rounded-2xl bg-purple-50 flex items-center justify-center mb-4">
              <GitBranch className="h-7 w-7 text-purple-400" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">
              {search || filter !== 'all' ? 'No branches found' : 'No branches yet'}
            </h3>
            <p className="text-sm text-slate-400 max-w-xs mb-5">
              {search || filter !== 'all'
                ? 'Try a different search or filter.'
                : 'Add your first branch location to get started.'}
            </p>
            {!search && filter === 'all' && can('branches:create') && (
              <button onClick={openNew} className="flex items-center gap-1.5 bg-purple-800 hover:bg-purple-900 text-white text-sm font-medium px-4 h-9 rounded-lg transition-colors">
                <Plus className="h-4 w-4" /> Add branch
              </button>
            )}
          </div>
        ) : (
          <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white divide-y divide-slate-100">
            {filtered.map((b: any) => (
              <div
                key={b.id}
                onClick={() => navigate(`/branches/${b.id}`)}
                className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 cursor-pointer transition-colors"
              >
                {/* Icon */}
                <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                  <GitBranch className="h-5 w-5 text-purple-500" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-slate-900">{b.branch_name}</span>
                    {b.is_head_office && (
                      <span className="text-xs bg-purple-100 text-purple-700 rounded px-2 py-0.5 font-medium">Head office</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-1 flex-wrap">
                    {(b.suburb || b.state_code) && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                        {b.suburb ? `${b.suburb}, ${b.state_code}` : b.state_code}
                      </span>
                    )}
                    {b.phone && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Phone className="h-3 w-3 text-slate-400 shrink-0" />{b.phone}
                      </span>
                    )}
                    {b.email && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Mail className="h-3 w-3 text-slate-400 shrink-0" />{b.email}
                      </span>
                    )}
                  </div>
                </div>

                {/* Type badge */}
                {b.branch_type && (
                  <span className="hidden sm:inline-flex text-xs font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 shrink-0">{b.branch_type}</span>
                )}

                {/* Status badge */}
                {(() => {
                  const st = b.branch_status || (b.is_active ? 'Active' : 'Inactive')
                  const cls = st === 'Active' ? 'bg-emerald-50 text-emerald-700' : st === 'Temporarily Closed' ? 'bg-amber-50 text-amber-700' : st === 'Permanently Closed' ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-500'
                  const dot = st === 'Active' ? 'bg-emerald-500' : st === 'Temporarily Closed' ? 'bg-amber-400' : st === 'Permanently Closed' ? 'bg-red-500' : 'bg-slate-400'
                  return (
                    <span className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full shrink-0 ${cls}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />{st}
                    </span>
                  )
                })()}

                {/* Arrow */}
                <ChevronRight className="h-4 w-4 text-slate-300 shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Add branch slide-over ── */}
      <SlideOver open={slideOpen} onClose={() => setSlideOpen(false)}
        title="Add Branch"
        subtitle="Fill in the branch details below"
      >
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-1.5">
              <label className={labelCls}>Branch Name *</label>
              <input className={inputCls} value={form.branch_name} onChange={e => setForm({ ...form, branch_name: e.target.value })} placeholder="Sydney CBD Office" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Branch Code</label>
              <input className={inputCls} value={form.branch_code} onChange={e => setForm({ ...form, branch_code: e.target.value })} placeholder="SYD-01" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Location Type</label>
              <select className={selectCls} value={form.branch_type} onChange={e => setForm({ ...form, branch_type: e.target.value })}>
                <option value="">Select type</option>
                {BRANCH_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Phone</label>
              <input className={inputCls} value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="02 9000 0000" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Status</label>
              <select className={selectCls} value={form.branch_status} onChange={e => setForm({ ...form, branch_status: e.target.value })}>
                {['Active', 'Inactive', 'Temporarily Closed', 'Permanently Closed'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="col-span-2 space-y-1.5">
              <label className={labelCls}>Email</label>
              <input className={inputCls} type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="branch@organisation.com.au" />
            </div>
          </div>

          <div className="border-t border-slate-100 pt-4">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Working hours</p>
            <WorkingHoursEditor
              key={slideOpen ? 'open' : 'closed'}
              value={form.operating_hours}
              onChange={v => setForm((f: any) => ({ ...f, operating_hours: v }))}
            />
          </div>

          <div className="border-t border-slate-100 pt-4">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Address</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2 space-y-1.5">
                <label className={labelCls}>Street Address</label>
                <input className={inputCls} value={form.address_line1} onChange={e => setForm({ ...form, address_line1: e.target.value })} placeholder="123 Main Street" />
              </div>
              <div className="space-y-1.5">
                <label className={labelCls}>Suburb</label>
                <input className={inputCls} value={form.suburb} onChange={e => setForm({ ...form, suburb: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className={labelCls}>State</label>
                <select className={selectCls} value={form.state_code} onChange={e => setForm({ ...form, state_code: e.target.value })}>
                  <option value="">Select state</option>
                  {STATES.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={labelCls}>Postcode</label>
                <input className={inputCls} value={form.postcode} onChange={e => setForm({ ...form, postcode: e.target.value })} maxLength={4} />
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input type="checkbox" id="hq" checked={form.is_head_office} onChange={e => setForm({ ...form, is_head_office: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-purple-600" />
                <label htmlFor="hq" className="text-sm font-medium text-slate-700">Head Office</label>
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={save}
              disabled={saveMut.isPending || !form.branch_name}
              className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {saveMut.isPending && <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
              {saveMut.isPending ? 'Saving…' : 'Add Branch'}
            </button>
            <button onClick={() => setSlideOpen(false)} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </SlideOver>
    </Layout>
  )
}
