/**
 * Staff Management page
 * Tabs: Profile · Employment · Qualifications & Certifications · Availability · Leave · Documents
 */
import { useState, useEffect, useMemo, Fragment } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { useAuth } from '@/context/AuthContext'
import { usePermissions } from '@/hooks/usePermissions'
import {
  Users, Plus, Search, ChevronRight, X, Briefcase,
  Award, Calendar, FileText, Phone, Mail, User, AlertCircle,
  CheckCircle, Clock, Loader2, Trash2, Activity, Filter,
  ShieldCheck, Bell, Download, Upload, RefreshCw, ChevronDown, ChevronUp,
  AlertTriangle, Eye, Pencil, MapPin, ArrowLeft,
} from 'lucide-react'
import {
  getStaffList, createStaff, updateStaff, deleteStaff,
  getPersonalInfo, upsertPersonalInfo,
  getContactInfo, upsertContactInfo,
  getEmployment, upsertEmployment,
  getProbation, upsertProbation,
  getContracts, createContract, updateContract, deleteContract,
  getStaffRoles, addStaffRole, updateStaffRole, deleteStaffRole,
  getExitProcess, upsertExitProcess,
  getEmergencyContacts, addEmergencyContact, updateEmergencyContact, deleteEmergencyContact,
  getIdentifications, addIdentification, updateIdentification, deleteIdentification,
  getPreferences, upsertPreferences,
  getStaffQualifications, addStaffQualification, updateStaffQualification, deleteStaffQualification, getQualificationCatalogue,
  getStaffCertifications, addStaffCertification, updateStaffCertification, deleteStaffCertification, getCertificationCatalogue,
  uploadComplianceDocument,
  getLeaveRequests, createLeaveRequest, updateLeaveRequest, getLeaveBalances,
  getLeaveTypes,
  getStaffDocuments, uploadStaffDocument, deleteStaffDocument, updateStaffDocument,
  getPerformanceReviews, createPerformanceReview, updatePerformanceReview,
  getKpis, createKpi, updateKpi, getGoals, createGoal, updateGoal,
  getAvailability, createAvailability, updateAvailability, deleteAvailability,
  getShifts, createShift, updateShift, deleteShift,
  getTimesheets, createTimesheet, updateTimesheet, deleteTimesheet, getTimesheetLines, addTimesheetLine,
  getComplianceItems, createComplianceItem, updateComplianceItem, deleteComplianceItem,
  sendComplianceReminder, getComplianceAudit,
} from '@/api/staff'
import { getAuditLogs } from '@/api/tenant'
import { getGenericErrorMessage } from '@/lib/errors'

// ─── helpers ──────────────────────────────────────────────────────────────────

const statusBadge = (s: string) => {
  const map: Record<string, string> = {
    Active:      'bg-emerald-100 text-emerald-700',
    Inactive:    'bg-slate-100   text-slate-600',
    Terminated:  'bg-red-100     text-red-700',
    'On Leave':  'bg-amber-100   text-amber-700',
  }
  return map[s] ?? 'bg-slate-100 text-slate-600'
}

const leaveBadge = (s: string) => {
  const map: Record<string, string> = {
    Pending:  'bg-amber-100  text-amber-700',
    Approved: 'bg-emerald-100 text-emerald-700',
    Declined: 'bg-red-100    text-red-700',
    Cancelled:'bg-slate-100  text-slate-500',
  }
  return map[s] ?? 'bg-slate-100 text-slate-600'
}

const Label = ({ text }: { text: string }) => (
  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">{text}</label>
)
// Field-level error message. All three field types below render it the same
// way — directly under the field — so a backend field_errors[name] (see
// src/lib/errors.ts) or client-side validation message shows up consistently
// wherever these shared primitives are used across the Staff screen's forms.
const FieldError = ({ error }: { error?: string | null }) =>
  error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null

// Fragments (not a wrapping <div>) so these drop-in replacements don't change
// box layout anywhere they're already used inside flex rows / grids with
// explicit width classes (e.g. className="w-32" filter dropdowns).
const Input = ({ error, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { error?: string | null }) => (
  <>
    <input
      {...props}
      aria-invalid={!!error}
      className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 bg-white ${error ? 'border-red-300 focus:ring-red-400 bg-red-50' : 'border-slate-200 focus:ring-purple-400'} ${props.className ?? ''}`}
    />
    <FieldError error={error} />
  </>
)
const Select = ({ error, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { error?: string | null }) => (
  <>
    <select
      {...props}
      aria-invalid={!!error}
      className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 bg-white ${error ? 'border-red-300 focus:ring-red-400 bg-red-50' : 'border-slate-200 focus:ring-purple-400'} ${props.className ?? ''}`}
    />
    <FieldError error={error} />
  </>
)
const Textarea = ({ error, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { error?: string | null }) => (
  <>
    <textarea
      {...props}
      rows={3}
      aria-invalid={!!error}
      className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 bg-white resize-none ${error ? 'border-red-300 focus:ring-red-400 bg-red-50' : 'border-slate-200 focus:ring-purple-400'} ${props.className ?? ''}`}
    />
    <FieldError error={error} />
  </>
)
const Btn = ({ children, variant = 'primary', ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost' }) => {
  const cls = {
    primary:   'bg-purple-600 text-white hover:bg-purple-700',
    secondary: 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50',
    danger:    'bg-red-50 border border-red-200 text-red-600 hover:bg-red-100',
    ghost:     'text-purple-600 hover:bg-purple-50',
  }[variant]
  return (
    <button {...rest} className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${cls} disabled:opacity-50 ${rest.className ?? ''}`}>
      {children}
    </button>
  )
}

// ─── TABS ─────────────────────────────────────────────────────────────────────

type Tab = 'profile' | 'employment' | 'compliance' | 'compliance_tracking' | 'availability' | 'timesheets' | 'leave' | 'documents' | 'performance'
const CHIPS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: 'profile',              label: 'Profile',       icon: User        },
  { key: 'employment',           label: 'Employment',    icon: Briefcase   },
  { key: 'compliance',           label: 'Quals & Certs', icon: Award       },
  { key: 'compliance_tracking',  label: 'Compliance',    icon: ShieldCheck },
  { key: 'availability',         label: 'Availability',  icon: Calendar    },
  { key: 'timesheets',           label: 'Timesheets',    icon: Clock       },
  { key: 'leave',                label: 'Leave',         icon: FileText    },
  { key: 'documents',            label: 'Documents',     icon: FileText    },
  { key: 'performance',          label: 'Performance',   icon: Activity    },
]

// ══════════════════════════════════════════════════════════════════════════════
// Staff List (left panel)
// ══════════════════════════════════════════════════════════════════════════════

// ── Staff List (full-width page) ──────────────────────────────────────────────

function StaffListPage({ tenantId, onSelect }: {
  tenantId: number; onSelect: (id: string, s: any) => void
}) {
  const [search, setSearch]           = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: res, isLoading } = useQuery({
    queryKey: ['staff', tenantId, statusFilter],
    queryFn: () => getStaffList(tenantId, statusFilter || undefined),
  })
  const allStaff: any[] = res?.data ?? []
  const list: any[] = allStaff.filter((s: any) => {
    const q = search.toLowerCase()
    return !q || `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) || (s.work_email ?? '').toLowerCase().includes(q)
  })

  const activeCount  = allStaff.filter(s => s.status === 'Active').length
  const leaveCount   = allStaff.filter(s => s.status === 'On Leave').length
  const inactiveCount = allStaff.filter(s => s.status === 'Inactive').length

  const fmtDate = (d?: string) => d ? new Date(d).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'

  return (
    <div className="flex flex-col gap-5">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Staff Management</h1>
          <p className="text-sm text-slate-500 mt-1">Manage your team members, roles and employment details</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 transition-colors">Export</button>
          <button className="px-3 py-1.5 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1">
            <Filter className="h-3.5 w-3.5" /> Filter
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total staff', value: allStaff.length, icon: Users, bg: 'bg-purple-50', color: 'text-purple-600' },
          { label: 'Active',      value: activeCount,     icon: CheckCircle, bg: 'bg-emerald-50', color: 'text-emerald-600' },
          { label: 'On leave',    value: leaveCount,      icon: Clock,  bg: 'bg-amber-50',  color: 'text-amber-600'  },
          { label: 'Inactive',    value: inactiveCount,   icon: AlertCircle, bg: 'bg-slate-100',  color: 'text-slate-500'  },
        ].map(({ label, value, icon: Icon, bg, color }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-xl p-4 flex items-center gap-3 shadow-sm">
            <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center shrink-0`}>
              <Icon className={`h-4.5 w-4.5 ${color}`} />
            </div>
            <div>
              <p className="text-xl font-semibold text-slate-800">{value}</p>
              <p className="text-xs text-slate-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name or email…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-purple-300"
          />
        </div>
        <div className="flex gap-2">
          {['', 'Active', 'On Leave', 'Inactive', 'Terminated'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${statusFilter === s ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-500 border-slate-200 hover:border-purple-400 hover:text-purple-600'}`}
            >
              {s || `All (${allStaff.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div>
        <div className="bg-white border border-slate-100 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide px-4 py-3">Staff member</th>
                <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide px-4 py-3">Email</th>
                <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide px-4 py-3">Status</th>
                <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide px-4 py-3">Since</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-400 text-sm">
                  <Loader2 className="h-5 w-5 animate-spin inline mr-2" />Loading staff…
                </td></tr>
              ) : list.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-400 text-sm">No staff found.</td></tr>
              ) : list.map((s: any) => (
                <tr
                  key={s.staff_id}
                  onClick={() => onSelect(s.staff_id, s)}
                  className="border-b border-slate-50 hover:bg-purple-50 cursor-pointer transition-colors last:border-0"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold shrink-0">
                        {s.first_name?.[0]}{s.last_name?.[0]}
                      </div>
                      <p className="text-sm font-medium text-slate-800">{s.first_name} {s.last_name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">{s.work_email ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusBadge(s.status)}`}>{s.status}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">{fmtDate(s.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <ChevronRight className="h-4 w-4 text-slate-300 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Profile Tab
// ══════════════════════════════════════════════════════════════════════════════

function ProfileTab({ tenantId, staffId, staff, onEditProfile }: { tenantId: number; staffId: string; staff: any; onEditProfile?: () => void }) {
  const qc = useQueryClient()

  // personal info
  const { data: piRes } = useQuery({ queryKey: ['staff-personal', staffId], queryFn: () => getPersonalInfo(tenantId, staffId) })
  const pi = piRes?.data

  const [piForm, setPiForm] = useState<any>(null)
  const piMut = useMutation({
    mutationFn: (d: any) => upsertPersonalInfo(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-personal', staffId] }); setPiForm(null) },
  })

  // contact info
  const { data: ciRes } = useQuery({ queryKey: ['staff-contact', staffId], queryFn: () => getContactInfo(tenantId, staffId) })
  const ci = ciRes?.data

  const [ciForm, setCiForm] = useState<any>(null)
  const ciMut = useMutation({
    mutationFn: (d: any) => upsertContactInfo(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-contact', staffId] }); setCiForm(null) },
  })

  // emergency contacts
  const { data: ecRes } = useQuery({ queryKey: ['staff-emerg', staffId], queryFn: () => getEmergencyContacts(tenantId, staffId) })
  const ecs: any[] = ecRes?.data ?? []
  const [ecForm, setEcForm] = useState<any>(null)
  const [ecEditId, setEcEditId] = useState<string | null>(null)
  const ecAdd = useMutation({
    mutationFn: (d: any) => addEmergencyContact(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-emerg', staffId] }); setEcForm(null); setEcEditId(null) },
  })
  const ecUpdate = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateEmergencyContact(tenantId, staffId, id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-emerg', staffId] }); setEcForm(null); setEcEditId(null) },
  })
  const ecDel = useMutation({ mutationFn: (id: string) => deleteEmergencyContact(tenantId, staffId, id), onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-emerg', staffId] }) })

  // identifications
  const { data: idenRes } = useQuery({ queryKey: ['staff-iden', staffId], queryFn: () => getIdentifications(tenantId, staffId) })
  const idens: any[] = idenRes?.data ?? []
  const [idenForm, setIdenForm] = useState<any>(null)
  const [idenEditForm, setIdenEditForm] = useState<any>(null)
  const idenAdd = useMutation({
    mutationFn: (d: any) => addIdentification(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-iden', staffId] }); setIdenForm(null) },
  })
  const idenUpdate = useMutation({
    mutationFn: (d: any) => updateIdentification(tenantId, staffId, d.staff_iden_id, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-iden', staffId] }); setIdenEditForm(null) },
  })
  const idenDelete = useMutation({
    mutationFn: (idenId: string) => deleteIdentification(tenantId, staffId, idenId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-iden', staffId] }),
  })

  // preferences
  const { data: prefRes } = useQuery({ queryKey: ['staff-pref', staffId], queryFn: () => getPreferences(tenantId, staffId) })
  const pref = prefRes?.data
  const [prefForm, setPrefForm] = useState<any>(null)
  const prefMut = useMutation({
    mutationFn: (d: any) => upsertPreferences(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-pref', staffId] }); setPrefForm(null) },
  })
  const initPref = () => setPrefForm({
    preferred_shift_type: pref?.preferred_shift_type ?? '',
    willing_weekend_work: pref?.willing_weekend_work ?? false,
    willing_public_holiday_work: pref?.willing_public_holiday_work ?? false,
    willing_sleepover_shift: pref?.willing_sleepover_shift ?? false,
    willing_active_overnight: pref?.willing_active_overnight ?? false,
    vehicle_available: pref?.vehicle_available ?? false,
    willing_to_travel: pref?.willing_to_travel ?? false,
    travel_limit_enabled: pref?.travel_limit_enabled ?? false,
    travel_radius_km: pref?.travel_radius_km ?? '',
    preferred_contact_time_from: pref?.preferred_contact_time_from ?? '',
    preferred_contact_time_to: pref?.preferred_contact_time_to ?? '',
    preferred_participant_gender: pref?.preferred_participant_gender ?? '',
  })

  const initPi = () => setPiForm({
    dob:                    pi?.dob?.slice(0, 10) ?? '',
    gender:                 pi?.gender ?? '',
    blood_group:            pi?.blood_group ?? '',
    nationality:            pi?.nationality ?? '',
    language_spoken:        pi?.language_spoken ?? '',
    permanent_street_no:    pi?.permanent_street_no ?? '',
    permanent_city:         pi?.permanent_city ?? '',
    permanent_state:        pi?.permanent_state ?? '',
    permanent_post_code:    pi?.permanent_post_code ?? '',
    residential_street_no:  pi?.residential_street_no ?? '',
    residential_city:       pi?.residential_city ?? '',
    residential_state:      pi?.residential_state ?? '',
    residential_post_code:  pi?.residential_post_code ?? '',
  })

  const initCi = () => setCiForm({
    primary_email:      ci?.primary_email      ?? '',
    secondary_email:    ci?.secondary_email    ?? '',
    primary_contact_no: ci?.primary_contact_no ?? '',
    secondary_contact_no: ci?.secondary_contact_no ?? '',
  })

  return (
    <div className="space-y-6">

      {/* ── Staff basic info ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center text-xl font-bold shrink-0">
            {staff.first_name?.[0]}{staff.last_name?.[0]}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-bold text-slate-800">{staff.first_name} {staff.middle_name ?? ''} {staff.last_name}</h2>
            <p className="text-sm text-slate-500">{staff.work_email ?? 'No work email'}</p>
            <span className={`mt-1 inline-block text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(staff.status)}`}>{staff.status}</span>
          </div>
          {onEditProfile && (
            <Btn variant="secondary" onClick={onEditProfile} className="shrink-0 text-xs py-1.5">
              Edit Profile
            </Btn>
          )}
        </div>
      </section>

      {/* ── Personal Info ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Personal Information</h3>
          {!piForm && <Btn variant="ghost" onClick={initPi} className="text-xs py-1">Edit</Btn>}
        </div>
        {piForm ? (
          <form onSubmit={e => { e.preventDefault(); piMut.mutate(piForm) }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Date of Birth" /><Input type="date" value={piForm.dob} onChange={e => setPiForm({ ...piForm, dob: e.target.value })} /></div>
              <div><Label text="Gender" />
                <Select value={piForm.gender} onChange={e => setPiForm({ ...piForm, gender: e.target.value })}>
                  <option value="">Select</option>
                  {['Male','Female','Non-binary','Prefer not to say'].map(g => <option key={g}>{g}</option>)}
                </Select>
              </div>
              <div><Label text="Blood Group" /><Input value={piForm.blood_group} onChange={e => setPiForm({ ...piForm, blood_group: e.target.value })} placeholder="e.g. A+" /></div>
              <div><Label text="Nationality" /><Input value={piForm.nationality} onChange={e => setPiForm({ ...piForm, nationality: e.target.value })} /></div>
              <div><Label text="Language(s) Spoken" /><Input value={piForm.language_spoken} onChange={e => setPiForm({ ...piForm, language_spoken: e.target.value })} /></div>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Permanent Address</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2"><Label text="Street" /><Input value={piForm.permanent_street_no} onChange={e => setPiForm({ ...piForm, permanent_street_no: e.target.value })} /></div>
                <div><Label text="Suburb / City" /><Input value={piForm.permanent_city} onChange={e => setPiForm({ ...piForm, permanent_city: e.target.value })} /></div>
                <div><Label text="State" /><Input value={piForm.permanent_state} onChange={e => setPiForm({ ...piForm, permanent_state: e.target.value })} /></div>
                <div><Label text="Postcode" /><Input value={piForm.permanent_post_code} onChange={e => setPiForm({ ...piForm, permanent_post_code: e.target.value })} /></div>
              </div>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Residential Address</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2"><Label text="Street" /><Input value={piForm.residential_street_no} onChange={e => setPiForm({ ...piForm, residential_street_no: e.target.value })} /></div>
                <div><Label text="Suburb / City" /><Input value={piForm.residential_city} onChange={e => setPiForm({ ...piForm, residential_city: e.target.value })} /></div>
                <div><Label text="State" /><Input value={piForm.residential_state} onChange={e => setPiForm({ ...piForm, residential_state: e.target.value })} /></div>
                <div><Label text="Postcode" /><Input value={piForm.residential_post_code} onChange={e => setPiForm({ ...piForm, residential_post_code: e.target.value })} /></div>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Btn type="submit" variant="primary" disabled={piMut.isPending}>{piMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setPiForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : pi ? (
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Date of Birth', pi.dob?.slice(0, 10)],
              ['Gender', pi.gender],
              ['Blood Group', pi.blood_group],
              ['Nationality', pi.nationality],
              ['Language(s)', pi.language_spoken],
            ].map(([k, v]) => (
              <div key={k}><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v ?? '—'}</p></div>
            ))}
            <div className="col-span-2 border-t border-slate-100 pt-3 mt-1">
              <span className="text-xs text-slate-500">Permanent Address</span>
              <p className="font-medium text-slate-700">{[pi.permanent_street_no, pi.permanent_city, pi.permanent_state, pi.permanent_post_code].filter(Boolean).join(', ') || '—'}</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No personal info added yet.</p>
        )}
      </section>

      {/* ── Contact Info ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Contact Information</h3>
          {!ciForm && <Btn variant="ghost" onClick={initCi} className="text-xs py-1">Edit</Btn>}
        </div>
        {ciForm ? (
          <form onSubmit={e => { e.preventDefault(); ciMut.mutate(ciForm) }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Primary Email" /><Input type="email" value={ciForm.primary_email} onChange={e => setCiForm({ ...ciForm, primary_email: e.target.value })} /></div>
              <div><Label text="Secondary Email" /><Input type="email" value={ciForm.secondary_email} onChange={e => setCiForm({ ...ciForm, secondary_email: e.target.value })} /></div>
              <div><Label text="Primary Phone" /><Input value={ciForm.primary_contact_no} onChange={e => setCiForm({ ...ciForm, primary_contact_no: e.target.value })} /></div>
              <div><Label text="Secondary Phone" /><Input value={ciForm.secondary_contact_no} onChange={e => setCiForm({ ...ciForm, secondary_contact_no: e.target.value })} /></div>
            </div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={ciMut.isPending}>{ciMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setCiForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Primary Email', ci?.primary_email],
              ['Secondary Email', ci?.secondary_email],
              ['Primary Phone', ci?.primary_contact_no],
              ['Secondary Phone', ci?.secondary_contact_no],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center gap-2">
                {k?.includes('Email') ? <Mail className="h-3.5 w-3.5 text-slate-400" /> : <Phone className="h-3.5 w-3.5 text-slate-400" />}
                <div><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v ?? '—'}</p></div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Emergency Contacts ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Emergency Contacts</h3>
          <Btn variant="ghost" onClick={() => setEcForm({ first_name: '', last_name: '', relationship_with_staff: '', primary_contact_no: '', primary_email: '', is_primary_emerg_cntact: false })} className="text-xs py-1">
            <Plus className="h-3 w-3" /> Add
          </Btn>
        </div>
        {ecForm && (
          <form onSubmit={e => { e.preventDefault(); ecEditId ? ecUpdate.mutate({ id: ecEditId, data: ecForm }) : ecAdd.mutate(ecForm) }} className="border border-slate-100 rounded-lg p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="First Name" /><Input required value={ecForm.first_name} onChange={e => setEcForm({ ...ecForm, first_name: e.target.value })} /></div>
              <div><Label text="Last Name" /><Input value={ecForm.last_name} onChange={e => setEcForm({ ...ecForm, last_name: e.target.value })} /></div>
              <div><Label text="Relationship" /><Input value={ecForm.relationship_with_staff} onChange={e => setEcForm({ ...ecForm, relationship_with_staff: e.target.value })} /></div>
              <div><Label text="Phone" /><Input value={ecForm.primary_contact_no} onChange={e => setEcForm({ ...ecForm, primary_contact_no: e.target.value })} /></div>
              <div><Label text="Email" /><Input type="email" value={ecForm.primary_email} onChange={e => setEcForm({ ...ecForm, primary_email: e.target.value })} /></div>
            </div>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={ecForm.is_primary_emerg_cntact} onChange={e => setEcForm({ ...ecForm, is_primary_emerg_cntact: e.target.checked })} className="rounded" />
              Primary emergency contact
            </label>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={ecAdd.isPending || ecUpdate.isPending}>
                {ecEditId ? (ecUpdate.isPending ? 'Saving…' : 'Save Changes') : (ecAdd.isPending ? 'Adding…' : 'Add Contact')}
              </Btn>
              <Btn type="button" variant="secondary" onClick={() => { setEcForm(null); setEcEditId(null) }}>Cancel</Btn>
            </div>
          </form>
        )}
        <div className="space-y-2">
          {ecs.length === 0 && !ecForm && <p className="text-sm text-slate-400 italic">No emergency contacts added.</p>}
          {ecs.map((ec: any) => (
            <div key={ec.emergency_contact_id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              {ec.is_primary_emerg_cntact && <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700">{ec.first_name} {ec.last_name} {ec.relationship_with_staff && <span className="text-xs text-slate-400">({ec.relationship_with_staff})</span>}</p>
                <p className="text-xs text-slate-500">{ec.primary_contact_no} {ec.primary_email && `· ${ec.primary_email}`}</p>
              </div>
              <button
                onClick={() => { setEcEditId(ec.emergency_contact_id); setEcForm({ first_name: ec.first_name ?? '', last_name: ec.last_name ?? '', relationship_with_staff: ec.relationship_with_staff ?? '', primary_contact_no: ec.primary_contact_no ?? '', primary_email: ec.primary_email ?? '', is_primary_emerg_cntact: ec.is_primary_emerg_cntact ?? false }) }}
                className="text-slate-400 hover:text-indigo-500"
              ><Pencil className="h-3.5 w-3.5" /></button>
              <button onClick={() => ecDel.mutate(ec.emergency_contact_id)} className="text-slate-400 hover:text-red-500"><Trash2 className="h-3.5 w-3.5" /></button>
            </div>
          ))}
        </div>
      </section>

      {/* ── Identifications ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Identity Documents</h3>
          <Btn variant="ghost" onClick={() => setIdenForm({ identification_type: '', identification_other: '', identification_number: '', expiry_date: '', document_attached: false, verified: false })} className="text-xs py-1">
            <Plus className="h-3 w-3" /> Add
          </Btn>
        </div>
        {idenForm && (
          <form
            onSubmit={e => {
              e.preventDefault()
              const finalType = idenForm.identification_type === 'Other' ? (idenForm.identification_other || 'Other') : idenForm.identification_type
              idenAdd.mutate({ identification_type: finalType, identification_number: idenForm.identification_number, expiry_date: idenForm.expiry_date, document_attached: idenForm.document_attached, verified: idenForm.verified })
            }}
            className="border border-slate-100 rounded-lg p-4 space-y-3"
          >
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Document Type" />
                <Select value={idenForm.identification_type} onChange={e => setIdenForm({ ...idenForm, identification_type: e.target.value, identification_other: '' })} required>
                  <option value="">Select</option>
                  {['Passport','Driver Licence','Medicare Card','Tax File Number','Birth Certificate','Visa','Other'].map(t => <option key={t} value={t}>{t}</option>)}
                </Select>
              </div>
              <div><Label text="Document Number" /><Input value={idenForm.identification_number} onChange={e => setIdenForm({ ...idenForm, identification_number: e.target.value })} /></div>
              {idenForm.identification_type === 'Other' && (
                <div className="col-span-2">
                  <Label text="Please specify document type" />
                  <Input value={idenForm.identification_other} onChange={e => setIdenForm({ ...idenForm, identification_other: e.target.value })} placeholder="e.g. NDIS Worker Screening, Working with Children Check…" required />
                </div>
              )}
              <div><Label text="Expiry Date" /><Input type="date" value={idenForm.expiry_date} onChange={e => setIdenForm({ ...idenForm, expiry_date: e.target.value })} /></div>
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={idenForm.document_attached} onChange={e => setIdenForm({ ...idenForm, document_attached: e.target.checked })} className="rounded" />
                Document attached
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={idenForm.verified} onChange={e => setIdenForm({ ...idenForm, verified: e.target.checked })} className="rounded" />
                Verified
              </label>
            </div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={idenAdd.isPending}>{idenAdd.isPending ? 'Adding…' : 'Add Document'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setIdenForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}
        <div className="space-y-2">
          {idens.length === 0 && !idenForm && <p className="text-sm text-slate-400 italic">No identity documents added.</p>}
          {idens.map((id: any) => {
            const expired = id.expiry_date && new Date(id.expiry_date) < new Date()
            const expiringSoon = id.expiry_date && !expired && (new Date(id.expiry_date).getTime() - Date.now()) / (1000*60*60*24) <= 90
            const isEditing = idenEditForm?.staff_iden_id === id.staff_iden_id
            return (
              <div key={id.staff_iden_id}>
                {isEditing ? (
                  /* ── Inline edit form ── */
                  <form
                    onSubmit={e => {
                      e.preventDefault()
                      const finalType = idenEditForm.identification_type === 'Other'
                        ? (idenEditForm.identification_other || 'Other')
                        : idenEditForm.identification_type
                      idenUpdate.mutate({ ...idenEditForm, identification_type: finalType })
                    }}
                    className="border border-purple-200 rounded-lg p-4 space-y-3 bg-purple-50"
                  >
                    <div className="grid grid-cols-2 gap-3">
                      <div><Label text="Document Type" />
                        <Select value={idenEditForm.identification_type} onChange={e => setIdenEditForm({ ...idenEditForm, identification_type: e.target.value, identification_other: '' })} required>
                          <option value="">Select</option>
                          {['Passport','Driver Licence','Medicare Card','Tax File Number','Birth Certificate','Visa','Other'].map(t => <option key={t} value={t}>{t}</option>)}
                        </Select>
                      </div>
                      <div><Label text="Document Number" /><Input value={idenEditForm.identification_number ?? ''} onChange={e => setIdenEditForm({ ...idenEditForm, identification_number: e.target.value })} /></div>
                      {idenEditForm.identification_type === 'Other' && (
                        <div className="col-span-2">
                          <Label text="Please specify document type" />
                          <Input value={idenEditForm.identification_other ?? ''} onChange={e => setIdenEditForm({ ...idenEditForm, identification_other: e.target.value })} placeholder="e.g. NDIS Worker Screening…" required />
                        </div>
                      )}
                      <div><Label text="Expiry Date" /><Input type="date" value={idenEditForm.expiry_date?.slice(0,10) ?? ''} onChange={e => setIdenEditForm({ ...idenEditForm, expiry_date: e.target.value })} /></div>
                    </div>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input type="checkbox" checked={!!idenEditForm.document_attached} onChange={e => setIdenEditForm({ ...idenEditForm, document_attached: e.target.checked })} className="rounded" />
                        Document attached
                      </label>
                      <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input type="checkbox" checked={!!idenEditForm.verified} onChange={e => setIdenEditForm({ ...idenEditForm, verified: e.target.checked })} className="rounded" />
                        Verified
                      </label>
                    </div>
                    <div className="flex gap-2">
                      <Btn type="submit" variant="primary" disabled={idenUpdate.isPending}>{idenUpdate.isPending ? 'Saving…' : 'Save'}</Btn>
                      <Btn type="button" variant="secondary" onClick={() => setIdenEditForm(null)}>Cancel</Btn>
                    </div>
                  </form>
                ) : (
                  /* ── Read-only row ── */
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700">{id.identification_type}</p>
                      <p className="text-xs text-slate-500">
                        {id.identification_number ?? '—'}
                        {id.expiry_date ? ` · Exp: ${id.expiry_date.slice(0, 10)}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {id.verified && <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-medium">Verified</span>}
                      {expired && <span className="text-[10px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-medium">Expired</span>}
                      {expiringSoon && <span className="text-[10px] bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded font-medium">Expiring Soon</span>}
                      {id.document_attached && <span className="text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-medium">Doc Attached</span>}
                      <button
                        className="text-slate-400 hover:text-purple-600 transition-colors p-1"
                        title="Edit"
                        onClick={() => setIdenEditForm({
                          staff_iden_id: id.staff_iden_id,
                          identification_type: id.identification_type ?? '',
                          identification_other: '',
                          identification_number: id.identification_number ?? '',
                          expiry_date: id.expiry_date?.slice(0,10) ?? '',
                          document_attached: !!id.document_attached,
                          verified: !!id.verified,
                        })}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        className="text-slate-400 hover:text-red-500 transition-colors p-1"
                        title="Delete"
                        disabled={idenDelete.isPending}
                        onClick={() => { if (confirm('Delete this identity document?')) idenDelete.mutate(id.staff_iden_id) }}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* ── Work Preferences ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Work Preferences</h3>
          {!prefForm && <Btn variant="ghost" onClick={initPref} className="text-xs py-1">{pref ? 'Edit' : 'Add'}</Btn>}
        </div>
        {prefForm ? (
          <form onSubmit={e => { e.preventDefault(); prefMut.mutate(prefForm) }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Preferred Shift Type" />
                <Select value={prefForm.preferred_shift_type} onChange={e => setPrefForm({ ...prefForm, preferred_shift_type: e.target.value })}>
                  <option value="">Any</option>
                  {['Morning','Afternoon','Evening','Night','Flexible'].map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
              <div><Label text="Preferred Participant Gender" />
                <Select value={prefForm.preferred_participant_gender} onChange={e => setPrefForm({ ...prefForm, preferred_participant_gender: e.target.value })}>
                  <option value="">No Preference</option>
                  {['Male','Female'].map(g => <option key={g}>{g}</option>)}
                </Select>
              </div>
              <div><Label text="Contact From" /><Input type="time" value={prefForm.preferred_contact_time_from} onChange={e => setPrefForm({ ...prefForm, preferred_contact_time_from: e.target.value })} /></div>
              <div><Label text="Contact To" /><Input type="time" value={prefForm.preferred_contact_time_to} onChange={e => setPrefForm({ ...prefForm, preferred_contact_time_to: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {([
                ['willing_weekend_work',        'Weekend work'],
                ['willing_public_holiday_work', 'Public holiday work'],
                ['willing_sleepover_shift',     'Sleepover shifts'],
                ['willing_active_overnight',    'Active overnight shifts'],
                ['vehicle_available',           'Vehicle available'],
                ['willing_to_travel',           'Willing to travel'],
              ] as [string, string][]).map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={prefForm[key]} onChange={e => setPrefForm({ ...prefForm, [key]: e.target.checked })} className="rounded" />
                  {label}
                </label>
              ))}
            </div>
            {prefForm.willing_to_travel && (
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={prefForm.travel_limit_enabled} onChange={e => setPrefForm({ ...prefForm, travel_limit_enabled: e.target.checked })} className="rounded" />
                  Limit travel radius
                </label>
                {prefForm.travel_limit_enabled && (
                  <div className="flex items-center gap-2">
                    <Input type="number" value={prefForm.travel_radius_km} onChange={e => setPrefForm({ ...prefForm, travel_radius_km: e.target.value })} className="w-20" />
                    <span className="text-sm text-slate-500">km</span>
                  </div>
                )}
              </div>
            )}
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={prefMut.isPending}>{prefMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setPrefForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : pref ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                ['Preferred Shift',    pref.preferred_shift_type || 'Any'],
                ['Preferred Gender',   pref.preferred_participant_gender || 'No preference'],
                ['Contact Hours',      pref.preferred_contact_time_from ? `${pref.preferred_contact_time_from} – ${pref.preferred_contact_time_to}` : '—'],
                ['Travel Radius',      pref.willing_to_travel ? (pref.travel_limit_enabled ? `${pref.travel_radius_km} km` : 'No limit') : 'Not willing'],
              ].map(([k, v]) => (
                <div key={k}><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v}</p></div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {([
                ['willing_weekend_work',        'Weekend work'],
                ['willing_public_holiday_work', 'Public holiday work'],
                ['willing_sleepover_shift',     'Sleepover shifts'],
                ['willing_active_overnight',    'Active overnight shifts'],
                ['vehicle_available',           'Vehicle available'],
              ] as [string, string][]).map(([key, label]) => (
                <div key={key} className="flex items-center gap-2 text-sm">
                  {pref[key]
                    ? <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    : <div className="h-3.5 w-3.5 rounded-full border-2 border-slate-300 shrink-0" />}
                  <span className={pref[key] ? 'text-slate-700' : 'text-slate-400'}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No work preferences set.</p>
        )}
      </section>

      {/* ── Staff Status Management (1.7) ─────────────────────────────────── */}
      <StaffStatusSection tenantId={tenantId} staffId={staffId} staff={staff} />

      {/* ── System Access ──────────────────────────────────────────────────── */}
      <SystemAccessSection tenantId={tenantId} staffId={staffId} staff={staff} />

    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Staff Status Management Section (1.7)
// ══════════════════════════════════════════════════════════════════════════════

const STATUS_COLORS: Record<string, string> = {
  Active:     'bg-emerald-100 text-emerald-700',
  Inactive:   'bg-slate-100   text-slate-600',
  'On Leave': 'bg-amber-100   text-amber-700',
  Terminated: 'bg-red-100     text-red-700',
  Suspended:  'bg-orange-100  text-orange-700',
}

function StaffStatusSection({ tenantId, staffId, staff }: { tenantId: number; staffId: string; staff: any }) {
  const qc = useQueryClient()
  const { can } = usePermissions()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ status: '', reason: '', effective_date: '' })

  // Status history stored in localStorage per staff member
  const historyKey = `staff-status-history-${staffId}`
  const [history, setHistory] = useState<any[]>(() => {
    try { return JSON.parse(localStorage.getItem(historyKey) ?? '[]') } catch { return [] }
  })

  const updateMut = useMutation({
    mutationFn: (d: any) => updateStaff(tenantId, staffId, { status: d.status }),
    onSuccess: (_, d) => {
      const entry = {
        id: `SH${Date.now()}`,
        from: staff.status,
        to: d.status,
        reason: d.reason,
        effective_date: d.effective_date || new Date().toISOString().slice(0, 10),
        changed_at: new Date().toISOString(),
      }
      const next = [entry, ...history].slice(0, 20)
      setHistory(next)
      try { localStorage.setItem(historyKey, JSON.stringify(next)) } catch {}
      qc.invalidateQueries({ queryKey: ['staff-list'] })
      setShowForm(false)
    },
    onError: (err: any) => alert(`Status update failed: ${err?.message ?? 'Unknown error'}`),
  })

  const currentStatus = staff?.status ?? 'Active'
  const fmt = (d: string) => { try { return new Date(d).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' }) } catch { return d } }

  return (
    <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-700">Staff Status</h3>
        {can('staff:edit') && !showForm && (
          <Btn variant="ghost" onClick={() => { setForm({ status: currentStatus, reason: '', effective_date: new Date().toISOString().slice(0, 10) }); setShowForm(true) }} className="text-xs py-1">
            Change Status
          </Btn>
        )}
      </div>

      {/* Current status */}
      <div className="flex items-center gap-3">
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${STATUS_COLORS[currentStatus] ?? 'bg-slate-100 text-slate-600'}`}>{currentStatus}</span>
        {history.length > 0 && (
          <span className="text-xs text-slate-400">Last changed: {fmt(history[0].effective_date)}</span>
        )}
      </div>

      {/* Change status form */}
      {showForm && (
        <div className="border border-purple-100 bg-purple-50/40 rounded-xl p-4 space-y-3">
          <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Change Status</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label text="New Status *" />
              <Select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                {['Active', 'Inactive', 'On Leave', 'Suspended', 'Terminated'].map(s => <option key={s}>{s}</option>)}
              </Select>
            </div>
            <div>
              <Label text="Effective Date *" />
              <Input type="date" value={form.effective_date} onChange={e => setForm(f => ({ ...f, effective_date: e.target.value }))} />
            </div>
            <div className="col-span-2">
              <Label text="Reason" />
              <Input value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} placeholder="Reason for status change…" />
            </div>
          </div>
          <div className="flex gap-2">
            <Btn type="button" variant="primary" disabled={updateMut.isPending || !form.status}
              onClick={() => { if (!form.status) return; updateMut.mutate(form) }}>
              {updateMut.isPending ? 'Saving…' : 'Save'}
            </Btn>
            <Btn type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Btn>
          </div>
        </div>
      )}

      {/* Status history */}
      {history.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Status History</p>
          <div className="space-y-1.5 max-h-40 overflow-y-auto">
            {history.map((h: any) => (
              <div key={h.id} className="flex items-start gap-2 text-xs text-slate-500 border-l-2 border-slate-100 pl-3">
                <div className="flex-1">
                  <span className={`inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[h.from] ?? 'bg-slate-100 text-slate-500'}`}>{h.from}</span>
                  <span className="mx-1 text-slate-400">→</span>
                  <span className={`inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[h.to] ?? 'bg-slate-100 text-slate-500'}`}>{h.to}</span>
                  {h.reason && <span className="ml-2 italic text-slate-400">{h.reason}</span>}
                </div>
                <span className="shrink-0 text-slate-400">{fmt(h.effective_date)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// System Access Section (shown inside ProfileTab)
// ══════════════════════════════════════════════════════════════════════════════

function SystemAccessSection({ tenantId, staffId, staff }: { tenantId: number; staffId: string; staff: any }) {
  const qc = useQueryClient()
  const { can } = usePermissions()
  const hasAccess = !!staff?.user_id
  const [grantOpen, setGrantOpen] = useState(false)
  const [grantForm, setGrantForm] = useState({ send_invite: true })

  const grantMut = useMutation({
    mutationFn: (d: any) =>
      import('@/api/users').then(m => m.createUser(tenantId, {
        first_name: staff.first_name,
        last_name:  staff.last_name,
        email:      d.email || staff.work_email,
        is_active:  true,
        staff_id:   staffId,
      })),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff', tenantId] })
      qc.invalidateQueries({ queryKey: ['staff-detail', staffId] })
      setGrantOpen(false)
    },
  })

  const revokeMut = useMutation({
    mutationFn: () =>
      import('@/api/users').then(m => m.deactivateUser(tenantId, staff.user_id)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-detail', staffId] }),
  })

  return (
    <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-700">System Access</h3>
        {can('users:create') && !hasAccess && (
          <Btn variant="secondary" onClick={() => setGrantOpen(true)} className="text-xs py-1">
            Grant access
          </Btn>
        )}
        {can('users:edit') && hasAccess && (
          <Btn variant="ghost" onClick={() => { if (confirm('Revoke system access for this staff member?')) revokeMut.mutate() }} className="text-xs py-1 text-red-600 hover:text-red-700">
            Revoke access
          </Btn>
        )}
      </div>

      {hasAccess ? (
        <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-100 rounded-lg">
          <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-emerald-800">System login active</p>
            <p className="text-xs text-emerald-600 mt-0.5">Linked user ID: {staff.user_id}</p>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Active</span>
        </div>
      ) : (
        <div className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="h-5 w-5 rounded-full border-2 border-slate-300 shrink-0" />
          <div>
            <p className="text-sm font-medium text-slate-600">No system login</p>
            <p className="text-xs text-slate-400 mt-0.5">This staff member cannot log into the system</p>
          </div>
        </div>
      )}

      {/* Grant access form */}
      {grantOpen && !hasAccess && (
        <div className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50">
          <p className="text-xs font-bold text-slate-600 uppercase tracking-wide">Create system login</p>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="send-invite"
              checked={grantForm.send_invite}
              onChange={e => setGrantForm({ ...grantForm, send_invite: e.target.checked })}
              className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="send-invite" className="text-xs text-slate-600">
              Send welcome email with temporary password to <span className="font-medium">{staff.work_email}</span>
            </label>
          </div>
          {grantMut.isError && (
            <p className="text-xs text-red-600 flex items-center gap-1"><AlertCircle className="h-3 w-3" /> Failed to create login. Check email is not already in use.</p>
          )}
          <div className="flex gap-2 pt-1">
            <Btn variant="primary" disabled={grantMut.isPending} onClick={() => grantMut.mutate(grantForm)} className="text-xs">
              {grantMut.isPending ? 'Creating…' : 'Create login'}
            </Btn>
            <Btn variant="secondary" onClick={() => setGrantOpen(false)} className="text-xs">Cancel</Btn>
          </div>
        </div>
      )}
    </section>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Employment Tab
// ══════════════════════════════════════════════════════════════════════════════

function EmploymentTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()

  // ── Employment ────────────────────────────────────────────────────────────
  const { data: empRes }       = useQuery({ queryKey: ['staff-emp', staffId],       queryFn: () => getEmployment(tenantId, staffId) })
  const { data: probRes }      = useQuery({ queryKey: ['staff-prob', staffId],      queryFn: () => getProbation(tenantId, staffId) })
  const { data: contractsRes } = useQuery({ queryKey: ['staff-contracts', staffId], queryFn: () => getContracts(tenantId, staffId) })
  const { data: rolesRes }     = useQuery({ queryKey: ['staff-roles', staffId],     queryFn: () => getStaffRoles(tenantId, staffId) })
  const { data: exitRes }      = useQuery({ queryKey: ['staff-exit', staffId],      queryFn: () => getExitProcess(tenantId, staffId) })

  const emp  = empRes?.data
  const prob = probRes?.data
  const contracts: any[] = contractsRes?.data ?? []
  const roles: any[]     = rolesRes?.data ?? []
  const exit = exitRes?.data

  const [empForm,      setEmpForm]      = useState<any>(null)
  const [probForm,     setProbForm]     = useState<any>(null)
  const [contractForm,     setContractForm]     = useState<any>(null)
  const [editContractForm, setEditContractForm] = useState<any>(null)
  const [roleForm,         setRoleForm]         = useState<any>(null)
  const [editRoleForm,     setEditRoleForm]     = useState<any>(null)
  const [exitForm,     setExitForm]     = useState<any>(null)

  const empMut      = useMutation({ mutationFn: (d: any) => upsertEmployment(tenantId, staffId, d),  onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-emp', staffId] });       setEmpForm(null) } })
  const probMut     = useMutation({ mutationFn: (d: any) => upsertProbation(tenantId, staffId, d),   onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-prob', staffId] });      setProbForm(null) } })
  const contractMut       = useMutation({ mutationFn: (d: any) => createContract(tenantId, staffId, d),                                            onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-contracts', staffId] }); setContractForm(null) } })
  const contractUpdateMut = useMutation({ mutationFn: (d: any) => updateContract(tenantId, staffId, d.contract_id, d),                             onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-contracts', staffId] }); setEditContractForm(null) } })
  const contractDeleteMut = useMutation({ mutationFn: (contractId: string) => deleteContract(tenantId, staffId, contractId),                        onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-contracts', staffId] }) } })
  const roleMut       = useMutation({ mutationFn: (d: any) => addStaffRole(tenantId, staffId, d),                               onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-roles', staffId] }); setRoleForm(null) } })
  const roleUpdateMut = useMutation({ mutationFn: (d: any) => updateStaffRole(tenantId, staffId, d.staff_role_id, d),          onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-roles', staffId] }); setEditRoleForm(null) } })
  const roleDeleteMut = useMutation({ mutationFn: (roleId: string) => deleteStaffRole(tenantId, staffId, roleId),               onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-roles', staffId] }) } })
  const exitMut     = useMutation({ mutationFn: (d: any) => upsertExitProcess(tenantId, staffId, d), onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-exit', staffId] });      setExitForm(null) } })

  const initEmp  = () => setEmpForm({
    employment_type: emp?.employment_type ?? '', employment_status: emp?.employment_status ?? 'Active',
    pay_level: emp?.pay_level ?? '', pay_point: emp?.pay_point ?? '',
    employment_start_date: emp?.employment_start_date?.slice(0, 10) ?? '',
    employment_end_date: emp?.employment_end_date?.slice(0, 10) ?? '',
    contracted_hours_per_week: emp?.contracted_hours_per_week ?? '',
    position_title: emp?.position_title ?? '', department: emp?.department ?? '', notes: emp?.notes ?? '',
  })
  const initProb = () => setProbForm({
    probation_start_date: prob?.probation_start_date?.slice(0, 10) ?? '',
    probation_end_date: prob?.probation_end_date?.slice(0, 10) ?? '',
    probation_status: prob?.probation_status ?? 'Active',
    probation_extension_date: prob?.probation_extension_date?.slice(0, 10) ?? '',
    probation_review_notes: prob?.probation_review_notes ?? '',
  })
  const initExit = () => setExitForm({
    exit_type: exit?.exit_type ?? '', notice_date: exit?.notice_date?.slice(0, 10) ?? '',
    last_working_day: exit?.last_working_day?.slice(0, 10) ?? '',
    resignation_received: exit?.resignation_received ?? false,
    exit_interview_completed: exit?.exit_interview_completed ?? false,
    equipment_returned: exit?.equipment_returned ?? false,
    system_access_revoked: exit?.system_access_revoked ?? false,
    final_pay_processed: exit?.final_pay_processed ?? false,
    notes: exit?.notes ?? '',
  })

  return (
    <div className="space-y-6">

      {/* ── Employment Details ─────────────────────────────────────────────── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Employment Details</h3>
          {!empForm && <Btn variant="ghost" onClick={initEmp} className="text-xs py-1">Edit</Btn>}
        </div>
        {empForm ? (
          <form onSubmit={e => {
            e.preventDefault()
            const payload = { ...empForm }
            // Convert empty strings to null for date/number fields
            ;['employment_start_date','employment_end_date'].forEach(k => { if (!payload[k]) payload[k] = null })
            if (payload.contracted_hours_per_week === '' || payload.contracted_hours_per_week === undefined) payload.contracted_hours_per_week = null
            else payload.contracted_hours_per_week = parseFloat(payload.contracted_hours_per_week)
            empMut.mutate(payload)
          }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Employment Type" />
                <Select value={empForm.employment_type} onChange={e => setEmpForm({ ...empForm, employment_type: e.target.value })}>
                  <option value="">Select</option>
                  {['Full-time','Part-time','Casual','Contractor','Volunteer'].map(t => <option key={t}>{t}</option>)}
                </Select>
              </div>
              <div><Label text="Employment Status" />
                <Select value={empForm.employment_status} onChange={e => setEmpForm({ ...empForm, employment_status: e.target.value })}>
                  {['Active','On Leave','Suspended','Terminated'].map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
              <div><Label text="Position Title" /><Input value={empForm.position_title} onChange={e => setEmpForm({ ...empForm, position_title: e.target.value })} /></div>
              <div><Label text="Department" /><Input value={empForm.department} onChange={e => setEmpForm({ ...empForm, department: e.target.value })} /></div>
              <div><Label text="SCHADS Pay Level" /><Input value={empForm.pay_level} onChange={e => setEmpForm({ ...empForm, pay_level: e.target.value })} placeholder="e.g. Level 2" /></div>
              <div><Label text="Pay Point" /><Input value={empForm.pay_point} onChange={e => setEmpForm({ ...empForm, pay_point: e.target.value })} placeholder="e.g. 1.1" /></div>
              <div><Label text="Start Date" /><Input type="date" value={empForm.employment_start_date} onChange={e => setEmpForm({ ...empForm, employment_start_date: e.target.value })} /></div>
              <div><Label text="End Date" /><Input type="date" value={empForm.employment_end_date} onChange={e => setEmpForm({ ...empForm, employment_end_date: e.target.value })} /></div>
              <div><Label text="Contracted Hours / Week" /><Input type="number" value={empForm.contracted_hours_per_week} onChange={e => setEmpForm({ ...empForm, contracted_hours_per_week: e.target.value })} /></div>
            </div>
            <div><Label text="Notes" /><Textarea value={empForm.notes} onChange={e => setEmpForm({ ...empForm, notes: e.target.value })} /></div>
            {empMut.isError && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                Save failed — {(empMut.error as any)?.response?.data?.detail ?? 'please try again'}
              </p>
            )}
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={empMut.isPending}>{empMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setEmpForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : emp ? (
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Employment Type',  emp.employment_type],
              ['Status',           emp.employment_status],
              ['Position',         emp.position_title],
              ['Department',       emp.department],
              ['SCHADS Pay Level', emp.pay_level],
              ['Pay Point',        emp.pay_point],
              ['Start Date',       emp.employment_start_date?.slice(0, 10)],
              ['End Date',         emp.employment_end_date?.slice(0, 10)],
              ['Hours / Week',     emp.contracted_hours_per_week],
            ].map(([k, v]) => (
              <div key={k}><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v ?? '—'}</p></div>
            ))}
            {emp.notes && <div className="col-span-2"><span className="text-xs text-slate-500">Notes</span><p className="text-slate-700">{emp.notes}</p></div>}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No employment record yet.</p>
        )}
      </section>

      {/* ── Probation ──────────────────────────────────────────────────────── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Probation</h3>
          {!probForm && <Btn variant="ghost" onClick={initProb} className="text-xs py-1">{prob ? 'Edit' : 'Add'}</Btn>}
        </div>
        {probForm ? (
          <form onSubmit={e => { e.preventDefault(); const p = { ...probForm }; if (!p.probation_extension_date) p.probation_extension_date = null; probMut.mutate(p) }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Start Date" /><Input type="date" value={probForm.probation_start_date} onChange={e => setProbForm({ ...probForm, probation_start_date: e.target.value })} /></div>
              <div><Label text="End Date" /><Input type="date" value={probForm.probation_end_date} onChange={e => setProbForm({ ...probForm, probation_end_date: e.target.value })} /></div>
              <div><Label text="Extension Date" /><Input type="date" value={probForm.probation_extension_date} onChange={e => setProbForm({ ...probForm, probation_extension_date: e.target.value })} /></div>
              <div><Label text="Status" />
                <Select value={probForm.probation_status} onChange={e => setProbForm({ ...probForm, probation_status: e.target.value })}>
                  {['Active','Completed','Extended','Terminated'].map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
            </div>
            <div><Label text="Review Notes" /><Textarea value={probForm.probation_review_notes} onChange={e => setProbForm({ ...probForm, probation_review_notes: e.target.value })} /></div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={probMut.isPending}>{probMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setProbForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : prob ? (
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Start Date',      prob.probation_start_date?.slice(0, 10)],
              ['End Date',        prob.probation_end_date?.slice(0, 10)],
              ['Extension Date',  prob.probation_extension_date?.slice(0, 10)],
              ['Status',          prob.probation_status],
            ].map(([k, v]) => (
              <div key={k}><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v ?? '—'}</p></div>
            ))}
            {prob.probation_review_notes && <div className="col-span-2"><span className="text-xs text-slate-500">Review Notes</span><p className="text-slate-700">{prob.probation_review_notes}</p></div>}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No probation record.</p>
        )}
      </section>

      {/* ── Contracts ──────────────────────────────────────────────────────── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Contracts</h3>
          <Btn variant="ghost" onClick={() => setContractForm({ contract_type: '', contract_start_date: '', contract_end_date: '', contract_file_path: '' })} className="text-xs py-1">
            <Plus className="h-3 w-3" /> Add
          </Btn>
        </div>
        {contractForm && (
          <form onSubmit={e => { e.preventDefault(); const c = { ...contractForm }; if (!c.contract_start_date) c.contract_start_date = null; if (!c.contract_end_date) c.contract_end_date = null; contractMut.mutate(c) }} className="border border-slate-100 rounded-lg p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Contract Type" />
                <Select value={contractForm.contract_type} onChange={e => setContractForm({ ...contractForm, contract_type: e.target.value })} required>
                  <option value="">Select</option>
                  {['Permanent','Fixed Term','Casual','Contractor'].map(t => <option key={t}>{t}</option>)}
                </Select>
              </div>
              <div><Label text="Start Date" /><Input type="date" value={contractForm.contract_start_date} onChange={e => setContractForm({ ...contractForm, contract_start_date: e.target.value })} /></div>
              <div><Label text="End Date" /><Input type="date" value={contractForm.contract_end_date} onChange={e => setContractForm({ ...contractForm, contract_end_date: e.target.value })} /></div>
              <div><Label text="Contract File Path" /><Input value={contractForm.contract_file_path} onChange={e => setContractForm({ ...contractForm, contract_file_path: e.target.value })} placeholder="https://… or file path" /></div>
            </div>
            {contractMut.isError && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                Save failed — {(contractMut.error as any)?.response?.data?.detail ?? 'please try again'}
              </p>
            )}
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={contractMut.isPending}>{contractMut.isPending ? 'Adding…' : 'Add Contract'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setContractForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}
        <div className="space-y-2">
          {contracts.length === 0 && !contractForm && <p className="text-sm text-slate-400 italic">No contracts added.</p>}
          {contracts.map((c: any) => (
            <div key={c.contract_id}>
              {editContractForm?.contract_id === c.contract_id ? (
                <form onSubmit={e => { e.preventDefault(); const d = { ...editContractForm }; if (!d.contract_start_date) d.contract_start_date = null; if (!d.contract_end_date) d.contract_end_date = null; contractUpdateMut.mutate(d) }} className="border border-purple-200 rounded-lg p-4 space-y-3 bg-purple-50">
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label text="Contract Type" />
                      <Select value={editContractForm.contract_type} onChange={e => setEditContractForm({ ...editContractForm, contract_type: e.target.value })} required>
                        <option value="">Select</option>
                        {['Permanent','Fixed Term','Casual','Contractor'].map(t => <option key={t}>{t}</option>)}
                      </Select>
                    </div>
                    <div><Label text="Start Date" /><Input type="date" value={editContractForm.contract_start_date ?? ''} onChange={e => setEditContractForm({ ...editContractForm, contract_start_date: e.target.value })} /></div>
                    <div><Label text="End Date" /><Input type="date" value={editContractForm.contract_end_date ?? ''} onChange={e => setEditContractForm({ ...editContractForm, contract_end_date: e.target.value })} /></div>
                    <div><Label text="Contract File Path" /><Input value={editContractForm.contract_file_path ?? ''} onChange={e => setEditContractForm({ ...editContractForm, contract_file_path: e.target.value })} placeholder="https://… or file path" /></div>
                  </div>
                  {contractUpdateMut.isError && (
                    <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                      Save failed — {(contractUpdateMut.error as any)?.response?.data?.detail ?? 'please try again'}
                    </p>
                  )}
                  <div className="flex gap-2">
                    <Btn type="submit" variant="primary" disabled={contractUpdateMut.isPending}>{contractUpdateMut.isPending ? 'Saving…' : 'Save'}</Btn>
                    <Btn type="button" variant="secondary" onClick={() => setEditContractForm(null)}>Cancel</Btn>
                  </div>
                </form>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <FileText className="h-4 w-4 text-blue-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700">{c.contract_type}</p>
                    <p className="text-xs text-slate-500">{c.contract_start_date?.slice(0, 10) ?? '—'} → {c.contract_end_date?.slice(0, 10) ?? 'Ongoing'}</p>
                  </div>
                  {c.contract_file_path && (
                    <a href={c.contract_file_path} target="_blank" rel="noreferrer" className="text-xs text-purple-600 hover:underline mr-2">View</a>
                  )}
                  <button className="text-slate-400 hover:text-purple-600 transition-colors p-1" title="Edit" onClick={() => setEditContractForm({ contract_id: c.contract_id, contract_type: c.contract_type ?? '', contract_start_date: c.contract_start_date?.slice(0,10) ?? '', contract_end_date: c.contract_end_date?.slice(0,10) ?? '', contract_file_path: c.contract_file_path ?? '' })}><Pencil className="h-3.5 w-3.5" /></button>
                  <button className="text-slate-400 hover:text-red-500 transition-colors p-1" title="Delete" disabled={contractDeleteMut.isPending} onClick={() => { if (confirm('Delete this contract?')) contractDeleteMut.mutate(c.contract_id) }}><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Job Roles ──────────────────────────────────────────────────────── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Job Roles</h3>
          <Btn variant="ghost" onClick={() => setRoleForm({ role_name: '', role_level: '', role_description: '', role_start_date: '', role_end_date: '', is_active: true })} className="text-xs py-1">
            <Plus className="h-3 w-3" /> Add
          </Btn>
        </div>
        {roleForm && (
          <form onSubmit={e => { e.preventDefault(); const d = { ...roleForm }; if (!d.role_start_date) d.role_start_date = null; if (!d.role_end_date) d.role_end_date = null; roleMut.mutate(d) }} className="border border-slate-100 rounded-lg p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Role Name" /><Input value={roleForm.role_name} onChange={e => setRoleForm({ ...roleForm, role_name: e.target.value })} required /></div>
              <div><Label text="Role Level" /><Input value={roleForm.role_level} onChange={e => setRoleForm({ ...roleForm, role_level: e.target.value })} placeholder="e.g. Senior, Junior" /></div>
              <div><Label text="Start Date" /><Input type="date" value={roleForm.role_start_date} onChange={e => setRoleForm({ ...roleForm, role_start_date: e.target.value })} /></div>
              <div><Label text="End Date" /><Input type="date" value={roleForm.role_end_date} onChange={e => setRoleForm({ ...roleForm, role_end_date: e.target.value })} /></div>
            </div>
            <div><Label text="Key Responsibilities" /><Textarea value={roleForm.role_description} onChange={e => setRoleForm({ ...roleForm, role_description: e.target.value })} placeholder="List the key duties and responsibilities for this role…" /></div>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={roleForm.is_active} onChange={e => setRoleForm({ ...roleForm, is_active: e.target.checked })} className="rounded" />
              Active role
            </label>
            {roleMut.isError && <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">Save failed — {(roleMut.error as any)?.response?.data?.detail ?? 'please try again'}</p>}
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={roleMut.isPending}>{roleMut.isPending ? 'Adding…' : 'Add Role'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setRoleForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}
        <div className="space-y-2">
          {roles.length === 0 && !roleForm && <p className="text-sm text-slate-400 italic">No job roles added.</p>}
          {roles.map((r: any) => (
            <div key={r.staff_role_id}>
              {editRoleForm?.staff_role_id === r.staff_role_id ? (
                <form onSubmit={e => { e.preventDefault(); const d = { ...editRoleForm }; if (!d.role_start_date) d.role_start_date = null; if (!d.role_end_date) d.role_end_date = null; roleUpdateMut.mutate(d) }} className="border border-purple-200 rounded-lg p-4 space-y-3 bg-purple-50">
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label text="Role Name" /><Input value={editRoleForm.role_name} onChange={e => setEditRoleForm({ ...editRoleForm, role_name: e.target.value })} required /></div>
                    <div><Label text="Role Level" /><Input value={editRoleForm.role_level ?? ''} onChange={e => setEditRoleForm({ ...editRoleForm, role_level: e.target.value })} placeholder="e.g. Senior, Junior" /></div>
                    <div><Label text="Start Date" /><Input type="date" value={editRoleForm.role_start_date ?? ''} onChange={e => setEditRoleForm({ ...editRoleForm, role_start_date: e.target.value })} /></div>
                    <div><Label text="End Date" /><Input type="date" value={editRoleForm.role_end_date ?? ''} onChange={e => setEditRoleForm({ ...editRoleForm, role_end_date: e.target.value })} /></div>
                  </div>
                  <div><Label text="Key Responsibilities" /><Textarea value={editRoleForm.role_description ?? ''} onChange={e => setEditRoleForm({ ...editRoleForm, role_description: e.target.value })} placeholder="List the key duties and responsibilities for this role…" /></div>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" checked={editRoleForm.is_active} onChange={e => setEditRoleForm({ ...editRoleForm, is_active: e.target.checked })} className="rounded" />
                    Active role
                  </label>
                  {roleUpdateMut.isError && <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">Save failed — {(roleUpdateMut.error as any)?.response?.data?.detail ?? 'please try again'}</p>}
                  <div className="flex gap-2">
                    <Btn type="submit" variant="primary" disabled={roleUpdateMut.isPending}>{roleUpdateMut.isPending ? 'Saving…' : 'Save'}</Btn>
                    <Btn type="button" variant="secondary" onClick={() => setEditRoleForm(null)}>Cancel</Btn>
                  </div>
                </form>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  {r.is_active
                    ? <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
                    : <Briefcase className="h-4 w-4 text-slate-400 shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700">{r.role_name}</p>
                    <p className="text-xs text-slate-500">
                      {r.role_level && <span className="mr-2">{r.role_level}</span>}
                      {r.role_start_date && <span>From {r.role_start_date.slice(0, 10)}</span>}
                      {r.role_end_date && <span> → {r.role_end_date.slice(0, 10)}</span>}
                    </p>
                    {r.role_description && <p className="text-xs text-slate-400 mt-0.5 truncate">{r.role_description}</p>}
                  </div>
                  {r.is_active && <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-medium">Active</span>}
                  <button className="text-slate-400 hover:text-purple-600 transition-colors p-1" title="Edit" onClick={() => setEditRoleForm({ staff_role_id: r.staff_role_id, role_name: r.role_name ?? '', role_level: r.role_level ?? '', role_description: r.role_description ?? '', role_start_date: r.role_start_date?.slice(0,10) ?? '', role_end_date: r.role_end_date?.slice(0,10) ?? '', is_active: r.is_active })}><Pencil className="h-3.5 w-3.5" /></button>
                  <button className="text-slate-400 hover:text-red-500 transition-colors p-1" title="Delete" disabled={roleDeleteMut.isPending} onClick={() => { if (confirm('Delete this role?')) roleDeleteMut.mutate(r.staff_role_id) }}><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Exit Process ───────────────────────────────────────────────────── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Exit Process</h3>
          {!exitForm && <Btn variant="ghost" onClick={initExit} className="text-xs py-1">{exit ? 'Edit' : 'Add'}</Btn>}
        </div>
        {exitForm ? (
          <form onSubmit={e => { e.preventDefault(); exitMut.mutate(exitForm) }} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Exit Type" />
                <Select value={exitForm.exit_type} onChange={e => setExitForm({ ...exitForm, exit_type: e.target.value })}>
                  <option value="">Select</option>
                  {['Resignation','Redundancy','Termination','Retirement','Contract End'].map(t => <option key={t}>{t}</option>)}
                </Select>
              </div>
              <div><Label text="Notice Date" /><Input type="date" value={exitForm.notice_date} onChange={e => setExitForm({ ...exitForm, notice_date: e.target.value })} /></div>
              <div><Label text="Last Working Day" /><Input type="date" value={exitForm.last_working_day} onChange={e => setExitForm({ ...exitForm, last_working_day: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {([
                ['resignation_received',      'Resignation received'],
                ['exit_interview_completed',  'Exit interview completed'],
                ['equipment_returned',        'Equipment returned'],
                ['system_access_revoked',     'System access revoked'],
                ['final_pay_processed',       'Final pay processed'],
              ] as [string, string][]).map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={exitForm[key]} onChange={e => setExitForm({ ...exitForm, [key]: e.target.checked })} className="rounded" />
                  {label}
                </label>
              ))}
            </div>
            <div><Label text="Notes" /><Textarea value={exitForm.notes} onChange={e => setExitForm({ ...exitForm, notes: e.target.value })} /></div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={exitMut.isPending}>{exitMut.isPending ? 'Saving…' : 'Save'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setExitForm(null)}>Cancel</Btn>
            </div>
          </form>
        ) : exit ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                ['Exit Type',       exit.exit_type],
                ['Notice Date',     exit.notice_date?.slice(0, 10)],
                ['Last Working Day',exit.last_working_day?.slice(0, 10)],
              ].map(([k, v]) => (
                <div key={k}><span className="text-xs text-slate-500">{k}</span><p className="font-medium text-slate-700">{v ?? '—'}</p></div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {([
                ['resignation_received',      'Resignation received'],
                ['exit_interview_completed',  'Exit interview completed'],
                ['equipment_returned',        'Equipment returned'],
                ['system_access_revoked',     'System access revoked'],
                ['final_pay_processed',       'Final pay processed'],
              ] as [string, string][]).map(([key, label]) => (
                <div key={key} className="flex items-center gap-2 text-sm">
                  {exit[key]
                    ? <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    : <div className="h-3.5 w-3.5 rounded-full border-2 border-slate-300 shrink-0" />}
                  <span className={exit[key] ? 'text-slate-700' : 'text-slate-400'}>{label}</span>
                </div>
              ))}
            </div>
            {exit.notes && <p className="text-sm text-slate-600 pt-1">{exit.notes}</p>}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No exit process record.</p>
        )}
      </section>

    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Shared expiry helpers
// ══════════════════════════════════════════════════════════════════════════════

const _now = () => Date.now()
const _isExpired      = (d?: string) => !!d && new Date(d).getTime() < _now()
const _isExpiringSoon = (d?: string) => { if (!d) return false; const diff = (new Date(d).getTime() - _now()) / 86400000; return diff >= 0 && diff <= 90 }
const _daysLeft       = (d?: string) => d ? Math.ceil((new Date(d).getTime() - _now()) / 86400000) : null
/** Remaining validity as % (100 = just issued, 0 = expired/at limit). */
const _remainPct      = (issued?: string, expiry?: string) => {
  if (!issued || !expiry) return null
  const total   = new Date(expiry).getTime() - new Date(issued).getTime()
  const elapsed = _now() - new Date(issued).getTime()
  return Math.min(100, Math.max(0, Math.round(((total - elapsed) / total) * 100)))
}
const _barColor = (pct: number) => pct < 25 ? '#ef4444' : pct < 50 ? '#f59e0b' : '#10b981'

/** Download a .ics calendar reminder file */
function _downloadIcs(title: string, reminderDate: string, expiryDate: string) {
  const fmt = (d: string) => d.replace(/-/g, '')
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//NDIS//Staff Portal//EN',
    'BEGIN:VEVENT',
    `DTSTART;VALUE=DATE:${fmt(reminderDate)}`,
    `DTEND;VALUE=DATE:${fmt(reminderDate)}`,
    `SUMMARY:Renew: ${title}`,
    `DESCRIPTION:${title} expires on ${expiryDate}. Please arrange renewal.`,
    'BEGIN:VALARM',
    'ACTION:DISPLAY',
    'DESCRIPTION:Renewal reminder',
    'TRIGGER:-P0D',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n')
  const blob = new Blob([ics], { type: 'text/calendar' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `reminder-${title.replace(/\s+/g, '-')}.ics`; a.click()
  URL.revokeObjectURL(url)
}

// ══════════════════════════════════════════════════════════════════════════════
// Qualifications & Certifications Tab  (features 2.1 – 2.6)
// ══════════════════════════════════════════════════════════════════════════════

function ComplianceTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const [subTab, setSubTab] = useState<'qualifications' | 'certifications'>('qualifications')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showQForm,    setShowQForm]    = useState(false)
  const [showCForm,    setShowCForm]    = useState(false)
  const [qForm,        setQForm]        = useState<any>({ qualification_id: '', qual_other: '', issuing_institution: '', year_completed: '', expiry_date: '', document_url: '', verification_status: 'Unverified' })
  const [cForm,        setCForm]        = useState<any>({ certification_id: '', cert_other: '', certification_status: 'Active', issue_date: '', expiry_date: '', issuing_provider: '', document_url: '' })
  const [editQual,     setEditQual]     = useState<any>(null) // { staff_qualification_id, ...fields }
  const [editCert,     setEditCert]     = useState<any>(null) // { staff_certification_id, ...fields }
  const [reminderTarget, setReminderTarget] = useState<{id: string, expiry: string, name: string} | null>(null)
  const [reminderDays,   setReminderDays]   = useState(30)

  const { data: quals } = useQuery({ queryKey: ['staff-quals', staffId], queryFn: () => getStaffQualifications(tenantId, staffId) })
  const { data: certs } = useQuery({ queryKey: ['staff-certs', staffId], queryFn: () => getStaffCertifications(tenantId, staffId) })
  const { data: qCat }  = useQuery({ queryKey: ['qual-catalogue'],         queryFn: () => getQualificationCatalogue() })
  const { data: cCat }  = useQuery({ queryKey: ['cert-catalogue'],         queryFn: () => getCertificationCatalogue() })

  const qualMut       = useMutation({ mutationFn: (d: any) => addStaffQualification(tenantId, staffId, d),                              onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-quals', staffId] }); setShowQForm(false); setQForm({ qualification_id: '', qual_other: '', issuing_institution: '', year_completed: '', expiry_date: '', document_url: '', verification_status: 'Unverified' }) } })
  const qualUpdateMut = useMutation({ mutationFn: (d: any) => updateStaffQualification(tenantId, staffId, d.staff_qualification_id, d), onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-quals', staffId] }); setEditQual(null) } })
  const qualDeleteMut = useMutation({ mutationFn: (id: string) => deleteStaffQualification(tenantId, staffId, id),                       onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-quals', staffId] }) } })
  const certMut       = useMutation({ mutationFn: (d: any) => addStaffCertification(tenantId, staffId, d),                              onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-certs', staffId] }); setShowCForm(false); setCForm({ certification_id: '', cert_other: '', certification_status: 'Active', issue_date: '', expiry_date: '', issuing_provider: '', document_url: '' }) } })
  const certUpdateMut = useMutation({ mutationFn: (d: any) => updateStaffCertification(tenantId, staffId, d.staff_certification_id, d), onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-certs', staffId] }); setEditCert(null) } })
  const certDeleteMut = useMutation({ mutationFn: (id: string) => deleteStaffCertification(tenantId, staffId, id),                       onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-certs', staffId] }) } })

  // Shared file upload mutation — uploads file, then PATCHes the qual or cert record
  const [uploadingId, setUploadingId] = useState<string | null>(null)
  const uploadDocMut = useMutation({
    mutationFn: async ({ file, recordId, type }: { file: File; recordId: string; type: 'qual' | 'cert' }) => {
      setUploadingId(recordId)
      const res = await uploadComplianceDocument(tenantId, staffId, file)
      const url: string = res.data.url
      if (type === 'qual') {
        await updateStaffQualification(tenantId, staffId, recordId, { document_url: url, certificate_uploaded: true })
      } else {
        await updateStaffCertification(tenantId, staffId, recordId, { document_url: url, certificate_uploaded: true })
      }
      return url
    },
    onSuccess: (_url, { type }) => {
      setUploadingId(null)
      qc.invalidateQueries({ queryKey: [type === 'qual' ? 'staff-quals' : 'staff-certs', staffId] })
    },
    onError: () => setUploadingId(null),
  })

  const qualList: any[] = quals?.data ?? []
  const certList: any[] = certs?.data ?? []
  const qCatList: any[] = qCat?.data ?? []
  const cCatList: any[] = cCat?.data ?? []

  // Stat counts
  const expiringQuals = qualList.filter(q => _isExpiringSoon(q.expiry_date) || _isExpired(q.expiry_date))
  const expiringCerts = certList.filter(c => _isExpiringSoon(c.expiry_date) || _isExpired(c.expiry_date))
  const totalItems = qualList.length + certList.length
  const expiring   = expiringQuals.length + expiringCerts.length
  const overallPct = totalItems > 0 ? Math.round(((totalItems - expiring) / totalItems) * 100) : 100

  const statusBadge = (item: any) => {
    const expired = _isExpired(item.expiry_date) || item.certification_status === 'Expired'
    if (expired) return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-red-100 text-red-600">Expired</span>
    if (_isExpiringSoon(item.expiry_date)) return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700">Expiring Soon</span>
    if (item.verification_status === 'Verified') return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700">Verified</span>
    if (item.certification_status === 'Active') return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700">Active</span>
    return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-slate-100 text-slate-600">Current</span>
  }

  const alertBanners = subTab === 'qualifications' ? expiringQuals : expiringCerts

  return (
    <div className="space-y-3">

      {/* ── 4-stat summary row ── */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Qualifications',    value: qualList.length, color: 'text-purple-700'  },
          { label: 'Certifications',    value: certList.length, color: 'text-purple-700'  },
          { label: 'Expiring <90 days', value: expiring,        color: 'text-amber-600'   },
          { label: 'Overall status',    value: `${overallPct}%`, color: 'text-emerald-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-100 p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* ── Alert banners for expiring items (2.5) — shown above toggle ── */}
      {alertBanners.map((item: any) => {
        const name = item.qualification_id ?? item.certification_id
        const exp  = item.expiry_date
        const gone = _isExpired(exp)
        const days = _daysLeft(exp)
        return (
          <div key={item.staff_qualification_id ?? item.staff_certification_id}
            className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg border ${gone ? 'bg-red-50 border-red-200 text-red-700' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-bold">{gone ? 'Expired:' : '1 qualification expiring soon'}</p>
              <p className="text-[11px] mt-0.5">{name}{exp ? ` ${gone ? 'expired' : 'expires in'} ${gone ? exp.slice(0,10) : `${days} days`}.` : '.'} {!gone && 'Renewal booking required.'}</p>
            </div>
            <button className="text-[10px] px-2 py-1 rounded border border-current font-semibold whitespace-nowrap shrink-0 hover:opacity-80">Set reminder</button>
          </div>
        )
      })}

      {/* ── Sub-tab toggle ── */}
      <div className="flex gap-1 p-1 bg-slate-100 rounded-lg w-fit">
        {(['qualifications', 'certifications'] as const).map(t => (
          <button key={t} onClick={() => { setSubTab(t); setExpandedId(null) }}
            className={`px-4 py-1.5 rounded-md text-[11px] font-semibold transition-all ${subTab === t ? 'bg-white text-purple-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
            {t === 'qualifications' ? 'Qualifications' : 'Certifications'}
          </button>
        ))}
      </div>

      {/* ── QUALIFICATIONS list ── */}
      {subTab === 'qualifications' && (
        <div className="space-y-2">
          {qualList.length === 0 && !showQForm && (
            <p className="text-sm text-slate-400 italic text-center py-6">No qualifications added yet.</p>
          )}
          {qualList.map((q: any) => {
            const id   = q.staff_qualification_id
            const open = expandedId === id
            const pct  = _remainPct(q.issue_date ?? q.year_completed ? `${q.year_completed}-01-01` : undefined, q.expiry_date) ?? 100
            const gone = _isExpired(q.expiry_date)
            const soon = _isExpiringSoon(q.expiry_date)
            const iconBg = gone ? '#fee2e2' : soon ? '#fef3c7' : '#d1fae5'
            const iconColor = gone ? '#dc2626' : soon ? '#d97706' : '#059669'
            return (
              <div key={id} className="border border-[#ede9ff] rounded-xl overflow-hidden bg-white">
                {/* Card header */}
                <button onClick={() => setExpandedId(open ? null : id)} className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-[#f9f8ff] text-left">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: iconBg }}>
                    <Award className="h-4 w-4" style={{ color: iconColor }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold text-slate-800 leading-snug">{{
                      'CERT3-IND-SUP': 'Certificate III in Individual Support',
                      'CERT4-DIS-SUP': 'Certificate IV in Disability Support',
                      'CERT4-AGED':    'Certificate IV in Ageing Support',
                      'DIP-COM-SRV':   'Diploma of Community Services',
                      'DIP-COUNSEL':   'Diploma of Counselling',
                      'BACH-SW':       'Bachelor of Social Work',
                      'BACH-NURSING':  'Bachelor of Nursing',
                      'BACH-OT':       'Bachelor of Occupational Therapy',
                      'BACH-PSYCH':    'Bachelor of Psychology',
                      'BACH-PHYSIO':   'Bachelor of Physiotherapy',
                      'CERT3-CHILDCARE':'Certificate III in Early Childhood',
                      'CERT4-MENTAL':  'Certificate IV in Mental Health',
                      'DIP-NURSING':   'Diploma of Nursing',
                      'OTHER':         'Other',
                    }[q.qualification_id] ?? q.qualification_id}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{q.issuing_institution ?? '—'}{q.year_completed ? ` · ${q.year_completed}` : ''}</p>
                  </div>
                  {statusBadge(q)}
                  {open ? <ChevronUp className="h-4 w-4 text-slate-300 shrink-0" /> : <ChevronDown className="h-4 w-4 text-slate-300 shrink-0" />}
                  <button className="text-slate-400 hover:text-purple-600 transition-colors p-1 shrink-0" title="Edit" onClick={e => { e.stopPropagation(); setEditQual({ staff_qualification_id: q.staff_qualification_id, qualification_id: q.qualification_id ?? '', issuing_institution: q.issuing_institution ?? '', year_completed: q.year_completed ?? '', expiry_date: q.expiry_date?.slice(0,10) ?? '', document_url: q.document_url ?? '', verification_status: q.verification_status ?? 'Unverified' }) }}><Pencil className="h-3.5 w-3.5" /></button>
                  <button className="text-slate-400 hover:text-red-500 transition-colors p-1 shrink-0" title="Delete" onClick={e => { e.stopPropagation(); if (confirm('Delete this qualification?')) qualDeleteMut.mutate(q.staff_qualification_id) }}><Trash2 className="h-3.5 w-3.5" /></button>
                </button>
                {/* Edit form */}
                {editQual?.staff_qualification_id === id && (
                  <div className="px-3 pb-3 pt-2 border-t border-purple-100 bg-purple-50 space-y-3">
                    <p className="text-[11px] font-bold text-purple-700 uppercase tracking-wide">Edit Qualification</p>
                    <form onSubmit={e => { e.preventDefault(); const d = { ...editQual }; if (d.year_completed) d.year_completed = parseInt(d.year_completed); else delete d.year_completed; if (!d.expiry_date) d.expiry_date = null; if (!d.document_url) d.document_url = null; qualUpdateMut.mutate(d) }} className="space-y-3">
                      <div className="grid grid-cols-2 gap-2.5">
                        <div className="col-span-2"><Label text="Qualification Name" /><Input value={editQual.qualification_id} onChange={e => setEditQual({ ...editQual, qualification_id: e.target.value })} required /></div>
                        <div><Label text="Institution" /><Input value={editQual.issuing_institution} onChange={e => setEditQual({ ...editQual, issuing_institution: e.target.value })} /></div>
                        <div><Label text="Year Completed" /><Input type="number" value={editQual.year_completed} onChange={e => setEditQual({ ...editQual, year_completed: e.target.value })} /></div>
                        <div><Label text="Expiry Date" /><Input type="date" value={editQual.expiry_date} onChange={e => setEditQual({ ...editQual, expiry_date: e.target.value })} /></div>
                        <div><Label text="Verification" /><Select value={editQual.verification_status} onChange={e => setEditQual({ ...editQual, verification_status: e.target.value })}>{['Unverified','Verified','Pending'].map(s => <option key={s}>{s}</option>)}</Select></div>
                        <div className="col-span-2">
                          <Label text="Document URL" />
                          <div className="flex gap-2 items-center">
                            <Input value={editQual.document_url} onChange={e => setEditQual({ ...editQual, document_url: e.target.value })} placeholder="Paste link or upload…" className="flex-1" />
                            <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-medium px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 shrink-0">
                              <Upload className="h-3.5 w-3.5" /> Upload
                              <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => { const f = e.target.files?.[0]; if (f) setEditQual({ ...editQual, document_url: f.name, certificate_uploaded: true }) }} />
                            </label>
                          </div>
                        </div>
                      </div>
                      {qualUpdateMut.isError && <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">Save failed — {(qualUpdateMut.error as any)?.response?.data?.detail ?? 'please try again'}</p>}
                      <div className="flex gap-2"><Btn type="submit" variant="primary" disabled={qualUpdateMut.isPending}>{qualUpdateMut.isPending ? 'Saving…' : 'Save'}</Btn><Btn type="button" variant="secondary" onClick={() => setEditQual(null)}>Cancel</Btn></div>
                    </form>
                  </div>
                )}
                {/* Card body */}
                {open && (
                  <div className="px-3 pb-3 pt-2 border-t border-[#f4f2fb] bg-[#fafaff] space-y-2.5">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Date Achieved</p>
                        <p className="text-[11px] text-slate-700 font-medium">{q.year_completed ? `${q.year_completed}` : '—'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Expiry Date</p>
                        <p className="text-[11px] text-slate-700 font-medium">{q.expiry_date?.slice(0,10) ?? 'No expiry'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Institution</p>
                        <p className="text-[11px] text-slate-700 font-medium">{q.issuing_institution ?? '—'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Document</p>
                        <p className="text-[11px] font-medium">{q.document_url ? <span className="text-emerald-600">✓ On file</span> : <span className="text-red-500">✗ Missing</span>}</p>
                      </div>
                    </div>
                    {/* Expiry bar (2.4) */}
                    {q.expiry_date && (
                      <div>
                        <p className="text-[10px] text-slate-400 mb-1">Validity remaining</p>
                        <div className="h-1.5 bg-[#ede9ff] rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: _barColor(pct) }} />
                        </div>
                        {soon && !gone && <p className="text-[10px] text-amber-600 mt-1">Expires in approx. {_daysLeft(q.expiry_date)} days</p>}
                        {gone && <p className="text-[10px] text-red-500 mt-1">Expired</p>}
                      </div>
                    )}
                    {/* Action buttons (2.5 / 2.6) */}
                    <div className="flex gap-1.5 flex-wrap pt-0.5">
                      {q.document_url && (
                        <a href={q.document_url} download target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold">
                          <Download className="h-3 w-3" /> Download
                        </a>
                      )}
                      <label className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold cursor-pointer transition-opacity ${uploadingId === q.staff_qualification_id ? 'opacity-50 pointer-events-none' : ''}`}>
                        <Upload className="h-3 w-3" /> {uploadingId === q.staff_qualification_id ? 'Uploading…' : q.document_url ? 'Replace doc' : 'Upload doc'}
                        <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                          const file = e.target.files?.[0]
                          if (file) uploadDocMut.mutate({ file, recordId: q.staff_qualification_id, type: 'qual' })
                          e.target.value = ''
                        }} />
                      </label>
                      {q.expiry_date && (
                        <button onClick={() => { setReminderTarget(reminderTarget?.id === id ? null : { id, expiry: q.expiry_date.slice(0,10), name: ({
                          'CERT3-IND-SUP':'Certificate III in Individual Support','CERT4-DIS-SUP':'Certificate IV in Disability Support','CERT4-AGED':'Certificate IV in Ageing Support','DIP-COM-SRV':'Diploma of Community Services','DIP-COUNSEL':'Diploma of Counselling','BACH-SW':'Bachelor of Social Work','BACH-NURSING':'Bachelor of Nursing','BACH-OT':'Bachelor of Occupational Therapy','BACH-PSYCH':'Bachelor of Psychology','BACH-PHYSIO':'Bachelor of Physiotherapy','CERT3-CHILDCARE':'Certificate III in Early Childhood','CERT4-MENTAL':'Certificate IV in Mental Health','DIP-NURSING':'Diploma of Nursing','OTHER':'Other'
                        } as any)[q.qualification_id] ?? q.qualification_id }); setReminderDays(30) }}
                          className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md font-semibold ml-auto transition-colors ${reminderTarget?.id === id ? 'bg-purple-700 text-white' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}>
                          <Bell className="h-3 w-3" /> {reminderTarget?.id === id ? 'Close' : 'Set renewal reminder'}
                        </button>
                      )}
                    </div>
                    {/* Reminder picker */}
                    {reminderTarget?.id === id && (
                      <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 space-y-2">
                        <p className="text-[11px] font-semibold text-purple-800">Remind me before expiry</p>
                        <p className="text-[10px] text-slate-500">Expiry: <span className="font-medium text-slate-700">{reminderTarget.expiry}</span></p>
                        <div className="flex gap-1.5 flex-wrap">
                          {[14, 30, 60, 90].map(d => (
                            <button key={d} type="button" onClick={() => setReminderDays(d)}
                              className={`text-[10px] px-2.5 py-1 rounded-md font-semibold border transition-colors ${reminderDays === d ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-purple-50'}`}>
                              {d} days before
                            </button>
                          ))}
                        </div>
                        <p className="text-[10px] text-slate-500">
                          Reminder date: <span className="font-semibold text-purple-700">{
                            (() => { const d = new Date(reminderTarget.expiry); d.setDate(d.getDate() - reminderDays); return d.toISOString().slice(0,10) })()
                          }</span>
                        </p>
                        <button type="button" onClick={() => {
                          const d = new Date(reminderTarget.expiry); d.setDate(d.getDate() - reminderDays)
                          _downloadIcs(reminderTarget.name, d.toISOString().slice(0,10), reminderTarget.expiry)
                          setReminderTarget(null)
                        }} className="inline-flex items-center gap-1.5 text-[10px] px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white font-semibold">
                          <Bell className="h-3 w-3" /> Add to Calendar (.ics)
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
          {/* Add form */}
          {showQForm && (
            <form onSubmit={e => { e.preventDefault(); const d = { ...qForm }; if (d.qualification_id === 'OTHER') d.qualification_id = d.qual_other || 'OTHER'; delete d.qual_other; if (d.year_completed) d.year_completed = parseInt(d.year_completed); else delete d.year_completed; if (!d.expiry_date) d.expiry_date = null; if (!d.document_url) d.document_url = null; qualMut.mutate(d) }} className="border border-purple-100 bg-purple-50 rounded-xl p-4 space-y-3">
              <p className="text-[11px] font-bold text-purple-700 uppercase tracking-wide">Add Qualification</p>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="col-span-2">
                  <Label text="Qualification" />
                  <Select value={qForm.qualification_id} onChange={e => setQForm({ ...qForm, qualification_id: e.target.value })} required>
                    <option value="">Select…</option>
                    {[
                      ['CERT3-IND-SUP', 'Certificate III in Individual Support'],
                      ['CERT4-DIS-SUP', 'Certificate IV in Disability Support'],
                      ['CERT4-AGED',    'Certificate IV in Ageing Support'],
                      ['DIP-COM-SRV',   'Diploma of Community Services'],
                      ['DIP-COUNSEL',   'Diploma of Counselling'],
                      ['BACH-SW',       'Bachelor of Social Work'],
                      ['BACH-NURSING',  'Bachelor of Nursing'],
                      ['BACH-OT',       'Bachelor of Occupational Therapy'],
                      ['BACH-PSYCH',    'Bachelor of Psychology'],
                      ['BACH-PHYSIO',   'Bachelor of Physiotherapy'],
                      ['CERT3-CHILDCARE','Certificate III in Early Childhood'],
                      ['CERT4-MENTAL',  'Certificate IV in Mental Health'],
                      ['DIP-NURSING',   'Diploma of Nursing'],
                      ['OTHER',         'Other'],
                    ].map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                  </Select>
                </div>
                {qForm.qualification_id === 'OTHER' && (
                  <div className="col-span-2">
                    <Label text="Please specify qualification name" />
                    <Input value={qForm.qual_other} onChange={e => setQForm({ ...qForm, qual_other: e.target.value })} placeholder="e.g. Bachelor of Disability Studies…" required />
                  </div>
                )}
                <div><Label text="Institution" /><Input value={qForm.issuing_institution} onChange={e => setQForm({ ...qForm, issuing_institution: e.target.value })} /></div>
                <div><Label text="Year Completed" /><Input type="number" value={qForm.year_completed} onChange={e => setQForm({ ...qForm, year_completed: e.target.value })} placeholder="e.g. 2022" /></div>
                <div><Label text="Expiry Date (if any)" /><Input type="date" value={qForm.expiry_date} onChange={e => setQForm({ ...qForm, expiry_date: e.target.value })} /></div>
                <div>
                  <Label text="Verification Status" />
                  <Select value={qForm.verification_status} onChange={e => setQForm({ ...qForm, verification_status: e.target.value })}>
                    {['Unverified','Verified','Pending'].map(s => <option key={s}>{s}</option>)}
                  </Select>
                </div>
                <div className="col-span-2">
                  <Label text="Document URL" />
                  <div className="flex gap-2 items-center">
                    <Input value={qForm.document_url} onChange={e => setQForm({ ...qForm, document_url: e.target.value })} placeholder="Paste link or upload below…" className="flex-1" />
                    <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-medium px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors shrink-0">
                      <Upload className="h-3.5 w-3.5" /> Upload
                      <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                        const file = e.target.files?.[0]
                        if (file) setQForm({ ...qForm, document_url: file.name, certificate_uploaded: true })
                      }} />
                    </label>
                  </div>
                </div>
              </div>
              {qualMut.isError && <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">Save failed — {(qualMut.error as any)?.response?.data?.detail ?? 'please try again'}</p>}
              <div className="flex gap-2">
                <Btn type="submit" variant="primary" disabled={qualMut.isPending}>{qualMut.isPending ? 'Adding…' : 'Add Qualification'}</Btn>
                <Btn type="button" variant="secondary" onClick={() => setShowQForm(false)}>Cancel</Btn>
              </div>
            </form>
          )}
          {!showQForm && (
            <button onClick={() => setShowQForm(true)} className="w-full flex items-center justify-center gap-1.5 text-[11px] font-semibold text-slate-500 hover:text-purple-700 border border-dashed border-slate-200 hover:border-purple-300 rounded-xl py-2.5 transition-colors">
              <Plus className="h-3.5 w-3.5" /> Add qualification
            </button>
          )}
        </div>
      )}

      {/* ── CERTIFICATIONS list ── */}
      {subTab === 'certifications' && (
        <div className="space-y-2">
          {certList.length === 0 && !showCForm && (
            <p className="text-sm text-slate-400 italic text-center py-6">No certifications added yet.</p>
          )}
          {certList.map((c: any) => {
            const id   = c.staff_certification_id
            const open = expandedId === id
            const pct  = _remainPct(c.issue_date, c.expiry_date) ?? 100
            const gone = _isExpired(c.expiry_date) || c.certification_status === 'Expired'
            const soon = _isExpiringSoon(c.expiry_date)
            return (
              <div key={id} className="border border-[#ede9ff] rounded-xl overflow-hidden bg-white">
                <button onClick={() => setExpandedId(open ? null : id)} className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-[#f9f8ff] text-left">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-[#ede9ff]">
                    <Award className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold text-slate-800 leading-snug">{{
                      'WWCC':         'Working with Children Check',
                      'NDIS-WORKER':  'NDIS Worker Screening Check',
                      'POLICE-CHK':   'National Police Check',
                      'FIRST-AID':    'First Aid Certificate',
                      'CPR':          'CPR Certificate',
                      'MANUAL-HAND':  'Manual Handling Certificate',
                      'FOOD-SAFETY':  'Food Safety Certificate',
                      'MED-ADMIN':    'Medication Administration',
                      'INFECTION-CTL':'Infection Control',
                      'FIRE-SAFETY':  'Fire Safety Training',
                      'SAFEGUARD':    'Child Safe Environments',
                      'DRIVING':      'Current Drivers Licence',
                      'OTHER':        'Other',
                    }[c.certification_id] ?? c.certification_id}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{c.issuing_provider ?? '—'} · {c.certification_status}</p>
                  </div>
                  {statusBadge(c)}
                  <button className="text-slate-400 hover:text-purple-600 transition-colors p-1 shrink-0" title="Edit"
                    onClick={e => { e.stopPropagation(); setEditCert({ staff_certification_id: c.staff_certification_id, certification_id: c.certification_id ?? '', issuing_provider: c.issuing_provider ?? '', certification_status: c.certification_status ?? 'Active', issue_date: c.issue_date?.slice(0,10) ?? '', expiry_date: c.expiry_date?.slice(0,10) ?? '', document_url: c.document_url ?? '' }) }}>
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button className="text-slate-400 hover:text-red-500 transition-colors p-1 shrink-0" title="Delete"
                    onClick={e => { e.stopPropagation(); if (confirm('Delete this certification?')) certDeleteMut.mutate(c.staff_certification_id) }}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                  {open ? <ChevronUp className="h-4 w-4 text-slate-300 shrink-0" /> : <ChevronDown className="h-4 w-4 text-slate-300 shrink-0" />}
                </button>
                {editCert?.staff_certification_id === id && (
                  <form onSubmit={e => { e.preventDefault(); const d = { ...editCert }; if (!d.issue_date) d.issue_date = null; if (!d.expiry_date) d.expiry_date = null; if (!d.document_url) d.document_url = null; certUpdateMut.mutate(d) }} className="px-3 pb-3 pt-3 border-t border-purple-100 bg-purple-50 space-y-3">
                    <p className="text-[11px] font-bold text-purple-700 uppercase tracking-wide">Edit Certification</p>
                    <div className="grid grid-cols-2 gap-2.5">
                      <div className="col-span-2">
                        <Label text="Certification" />
                        <Select value={editCert.certification_id} onChange={e => setEditCert({ ...editCert, certification_id: e.target.value })} required>
                          <option value="">Select…</option>
                          {[
                            ['WWCC',         'Working with Children Check'],
                            ['NDIS-WORKER',  'NDIS Worker Screening Check'],
                            ['POLICE-CHK',   'National Police Check'],
                            ['FIRST-AID',    'First Aid Certificate'],
                            ['CPR',          'CPR Certificate'],
                            ['MANUAL-HAND',  'Manual Handling Certificate'],
                            ['FOOD-SAFETY',  'Food Safety Certificate'],
                            ['MED-ADMIN',    'Medication Administration'],
                            ['INFECTION-CTL','Infection Control'],
                            ['FIRE-SAFETY',  'Fire Safety Training'],
                            ['SAFEGUARD',    'Child Safe Environments'],
                            ['DRIVING',      'Current Drivers Licence'],
                            ['OTHER',        'Other'],
                          ].map(([cid, label]) => <option key={cid} value={cid}>{label}</option>)}
                        </Select>
                      </div>
                      <div><Label text="Provider / Issuer" /><Input value={editCert.issuing_provider} onChange={e => setEditCert({ ...editCert, issuing_provider: e.target.value })} /></div>
                      <div>
                        <Label text="Status" />
                        <Select value={editCert.certification_status} onChange={e => setEditCert({ ...editCert, certification_status: e.target.value })}>
                          {['Active','Expired','Pending Renewal','Suspended'].map(s => <option key={s}>{s}</option>)}
                        </Select>
                      </div>
                      <div><Label text="Issue Date" /><Input type="date" value={editCert.issue_date} onChange={e => setEditCert({ ...editCert, issue_date: e.target.value })} /></div>
                      <div><Label text="Expiry Date" /><Input type="date" value={editCert.expiry_date} onChange={e => setEditCert({ ...editCert, expiry_date: e.target.value })} /></div>
                      <div className="col-span-2">
                        <Label text="Document URL" />
                        <div className="flex gap-2 items-center">
                          <Input value={editCert.document_url} onChange={e => setEditCert({ ...editCert, document_url: e.target.value })} placeholder="Paste link or upload below…" className="flex-1" />
                          <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-medium px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors shrink-0">
                            <Upload className="h-3.5 w-3.5" /> Upload
                            <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                              const file = e.target.files?.[0]
                              if (file) setEditCert({ ...editCert, document_url: file.name, certificate_uploaded: true })
                            }} />
                          </label>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 justify-end pt-1">
                      <button type="button" onClick={() => setEditCert(null)} className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 font-medium">Cancel</button>
                      <button type="submit" disabled={certUpdateMut.isPending} className="px-3 py-1.5 text-xs rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-semibold disabled:opacity-60">
                        {certUpdateMut.isPending ? 'Saving…' : 'Save Changes'}
                      </button>
                    </div>
                  </form>
                )}
                {open && (
                  <div className="px-3 pb-3 pt-2 border-t border-[#f4f2fb] bg-[#fafaff] space-y-2.5">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Date Issued</p>
                        <p className="text-[11px] text-slate-700 font-medium">{c.issue_date?.slice(0,10) ?? '—'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Expiry Date</p>
                        <p className="text-[11px] text-slate-700 font-medium">{c.expiry_date?.slice(0,10) ?? 'No expiry'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Provider</p>
                        <p className="text-[11px] text-slate-700 font-medium">{c.issuing_provider ?? '—'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Document</p>
                        <p className="text-[11px] font-medium">{c.document_url ? <span className="text-emerald-600">✓ On file</span> : <span className="text-slate-400">Not uploaded</span>}</p>
                      </div>
                    </div>
                    {c.expiry_date && (
                      <div>
                        <div className="h-1.5 bg-[#ede9ff] rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: _barColor(pct) }} />
                        </div>
                        {gone && <p className="text-[10px] text-red-500 mt-1">Expired</p>}
                        {!gone && soon && <p className="text-[10px] text-amber-600 mt-1">Expires in {_daysLeft(c.expiry_date)} days</p>}
                      </div>
                    )}
                    <div className="flex gap-1.5 flex-wrap pt-0.5">
                      {c.document_url && (
                        <a href={c.document_url} download target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold">
                          <Download className="h-3 w-3" /> Download
                        </a>
                      )}
                      <label className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold cursor-pointer transition-opacity ${uploadingId === c.staff_certification_id ? 'opacity-50 pointer-events-none' : ''}`}>
                        <Upload className="h-3 w-3" /> {uploadingId === c.staff_certification_id ? 'Uploading…' : c.document_url ? 'Replace doc' : 'Upload doc'}
                        <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                          const file = e.target.files?.[0]
                          if (file) uploadDocMut.mutate({ file, recordId: c.staff_certification_id, type: 'cert' })
                          e.target.value = ''
                        }} />
                      </label>
                      {c.expiry_date && (
                        <button onClick={() => { setReminderTarget(reminderTarget?.id === id ? null : { id, expiry: c.expiry_date.slice(0,10), name: ({
                          'WWCC':'Working with Children Check','NDIS-WORKER':'NDIS Worker Screening Check','POLICE-CHK':'National Police Check','FIRST-AID':'First Aid Certificate','CPR':'CPR Certificate','MANUAL-HAND':'Manual Handling Certificate','FOOD-SAFETY':'Food Safety Certificate','MED-ADMIN':'Medication Administration','INFECTION-CTL':'Infection Control','FIRE-SAFETY':'Fire Safety Training','SAFEGUARD':'Child Safe Environments','DRIVING':'Current Drivers Licence','OTHER':'Other'
                        } as any)[c.certification_id] ?? c.certification_id }); setReminderDays(30) }}
                          className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md font-semibold ml-auto transition-colors ${reminderTarget?.id === id ? 'bg-purple-700 text-white' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}>
                          <Bell className="h-3 w-3" /> {reminderTarget?.id === id ? 'Close' : 'Set renewal reminder'}
                        </button>
                      )}
                    </div>
                    {/* Reminder picker */}
                    {reminderTarget?.id === id && (
                      <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 space-y-2">
                        <p className="text-[11px] font-semibold text-purple-800">Remind me before expiry</p>
                        <p className="text-[10px] text-slate-500">Expiry: <span className="font-medium text-slate-700">{reminderTarget.expiry}</span></p>
                        <div className="flex gap-1.5 flex-wrap">
                          {[14, 30, 60, 90].map(d => (
                            <button key={d} type="button" onClick={() => setReminderDays(d)}
                              className={`text-[10px] px-2.5 py-1 rounded-md font-semibold border transition-colors ${reminderDays === d ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-purple-50'}`}>
                              {d} days before
                            </button>
                          ))}
                        </div>
                        <p className="text-[10px] text-slate-500">
                          Reminder date: <span className="font-semibold text-purple-700">{
                            (() => { const d = new Date(reminderTarget.expiry); d.setDate(d.getDate() - reminderDays); return d.toISOString().slice(0,10) })()
                          }</span>
                        </p>
                        <button type="button" onClick={() => {
                          const d = new Date(reminderTarget.expiry); d.setDate(d.getDate() - reminderDays)
                          _downloadIcs(reminderTarget.name, d.toISOString().slice(0,10), reminderTarget.expiry)
                          setReminderTarget(null)
                        }} className="inline-flex items-center gap-1.5 text-[10px] px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white font-semibold">
                          <Bell className="h-3 w-3" /> Add to Calendar (.ics)
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
          {showCForm && (
            <form onSubmit={e => { e.preventDefault(); const d = { ...cForm }; if (d.certification_id === 'OTHER') d.certification_id = d.cert_other || 'OTHER'; delete d.cert_other; if (!d.issue_date) d.issue_date = null; if (!d.expiry_date) d.expiry_date = null; if (!d.document_url) d.document_url = null; certMut.mutate(d) }} className="border border-purple-100 bg-purple-50 rounded-xl p-4 space-y-3">
              <p className="text-[11px] font-bold text-purple-700 uppercase tracking-wide">Add Certification</p>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="col-span-2">
                  <Label text="Certification" />
                  <Select value={cForm.certification_id} onChange={e => setCForm({ ...cForm, certification_id: e.target.value })} required>
                    <option value="">Select…</option>
                    {[
                      ['WWCC',         'Working with Children Check'],
                      ['NDIS-WORKER',  'NDIS Worker Screening Check'],
                      ['POLICE-CHK',   'National Police Check'],
                      ['FIRST-AID',    'First Aid Certificate'],
                      ['CPR',          'CPR Certificate'],
                      ['MANUAL-HAND',  'Manual Handling Certificate'],
                      ['FOOD-SAFETY',  'Food Safety Certificate'],
                      ['MED-ADMIN',    'Medication Administration'],
                      ['INFECTION-CTL','Infection Control'],
                      ['FIRE-SAFETY',  'Fire Safety Training'],
                      ['SAFEGUARD',    'Child Safe Environments'],
                      ['DRIVING',      'Current Drivers Licence'],
                      ['OTHER',        'Other'],
                    ].map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                  </Select>
                </div>
                {cForm.certification_id === 'OTHER' && (
                  <div className="col-span-2">
                    <Label text="Please specify certification name" />
                    <Input value={cForm.cert_other} onChange={e => setCForm({ ...cForm, cert_other: e.target.value })} placeholder="e.g. Autism Awareness Training…" required />
                  </div>
                )}
                <div><Label text="Provider / Issuer" /><Input value={cForm.issuing_provider} onChange={e => setCForm({ ...cForm, issuing_provider: e.target.value })} /></div>
                <div>
                  <Label text="Status" />
                  <Select value={cForm.certification_status} onChange={e => setCForm({ ...cForm, certification_status: e.target.value })}>
                    {['Active','Expired','Pending Renewal','Suspended'].map(s => <option key={s}>{s}</option>)}
                  </Select>
                </div>
                <div><Label text="Issue Date" /><Input type="date" value={cForm.issue_date} onChange={e => setCForm({ ...cForm, issue_date: e.target.value })} /></div>
                <div><Label text="Expiry Date" /><Input type="date" value={cForm.expiry_date} onChange={e => setCForm({ ...cForm, expiry_date: e.target.value })} /></div>
                <div className="col-span-2">
                  <Label text="Document URL" />
                  <div className="flex gap-2 items-center">
                    <Input value={cForm.document_url} onChange={e => setCForm({ ...cForm, document_url: e.target.value })} placeholder="Paste link or upload below…" className="flex-1" />
                    <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-medium px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors shrink-0">
                      <Upload className="h-3.5 w-3.5" /> Upload
                      <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                        const file = e.target.files?.[0]
                        if (file) setCForm({ ...cForm, document_url: file.name, certificate_uploaded: true })
                      }} />
                    </label>
                  </div>
                </div>
              </div>
              {certMut.isError && <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">Save failed — {(certMut.error as any)?.response?.data?.detail ?? 'please try again'}</p>}
              <div className="flex gap-2">
                <Btn type="submit" variant="primary" disabled={certMut.isPending}>{certMut.isPending ? 'Adding…' : 'Add Certification'}</Btn>
                <Btn type="button" variant="secondary" onClick={() => setShowCForm(false)}>Cancel</Btn>
              </div>
            </form>
          )}
          {!showCForm && (
            <button onClick={() => setShowCForm(true)} className="w-full flex items-center justify-center gap-1.5 text-[11px] font-semibold text-slate-500 hover:text-purple-700 border border-dashed border-slate-200 hover:border-purple-300 rounded-xl py-2.5 transition-colors">
              <Plus className="h-3.5 w-3.5" /> Add certification
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Compliance Tracking Tab  (features 3.1 – 3.6)
// ══════════════════════════════════════════════════════════════════════════════

function ComplianceTrackingTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<any>({
    requirement_name: '', category: '', requirement_type: 'Mandatory',
    completed_date: '', expiry_date: '', reference_no: '',
    is_mandatory: true, reminder_days_before: 30, notes: '',
  })

  const { data: itemsRes  } = useQuery({ queryKey: ['compliance-items', staffId],  queryFn: () => getComplianceItems(tenantId, staffId) })

  const items: any[]  = itemsRes?.data  ?? []

  const createMut   = useMutation({ mutationFn: (d: any) => createComplianceItem(tenantId, staffId, d),                                  onSuccess: () => { qc.invalidateQueries({ queryKey: ['compliance-items', staffId] }); qc.invalidateQueries({ queryKey: ['compliance-audit', staffId] }); setShowForm(false); setForm({ requirement_name: '', category: '', requirement_type: 'Mandatory', completed_date: '', expiry_date: '', reference_no: '', is_mandatory: true, reminder_days_before: 30, notes: '' }) } })
  const updateMut   = useMutation({ mutationFn: ({ id, d }: any) => updateComplianceItem(tenantId, staffId, id, d),                      onSuccess: () => { qc.invalidateQueries({ queryKey: ['compliance-items', staffId] }); qc.invalidateQueries({ queryKey: ['compliance-audit', staffId] }) } })
  const deleteMut   = useMutation({ mutationFn: (id: string) => deleteComplianceItem(tenantId, staffId, id),                              onSuccess: () => { qc.invalidateQueries({ queryKey: ['compliance-items', staffId] }); qc.invalidateQueries({ queryKey: ['compliance-audit', staffId] }) } })
  const remindMut   = useMutation({ mutationFn: (id: string) => sendComplianceReminder(tenantId, staffId, id),                            onSuccess: () => { qc.invalidateQueries({ queryKey: ['compliance-items', staffId] }); qc.invalidateQueries({ queryKey: ['compliance-audit', staffId] }) } })

  // 3.4 Document upload — same generic-upload-then-attach pattern already
  // used for qualifications/certifications: upload the file, then PATCH the
  // compliance item's document_url to point at it.
  const [uploadingItemId, setUploadingItemId] = useState<string | null>(null)
  const docUploadMut = useMutation({
    mutationFn: async ({ file, itemId }: { file: File; itemId: string }) => {
      setUploadingItemId(itemId)
      const res = await uploadComplianceDocument(tenantId, staffId, file)
      const url: string = res.data.url
      await updateComplianceItem(tenantId, staffId, itemId, { document_url: url, document_filename: file.name })
      return url
    },
    onSuccess: () => { setUploadingItemId(null); qc.invalidateQueries({ queryKey: ['compliance-items', staffId] }); qc.invalidateQueries({ queryKey: ['compliance-audit', staffId] }) },
    onError: () => { setUploadingItemId(null); alert('Failed to upload document.') },
  })

  // 3.6 Compliance History / Audit Trail — backed by the dedicated
  // staff_compliance_audit table (already built server-side, just never
  // surfaced in the UI until now).
  const [showAudit, setShowAudit] = useState(false)
  const { data: auditRes, isLoading: auditLoading } = useQuery({
    queryKey: ['compliance-audit', staffId],
    queryFn: () => getComplianceAudit(tenantId, staffId),
    enabled: showAudit,
  })
  const auditLog: any[] = (auditRes as any)?.data ?? []

  // Stats (3.1) — includes auto-synced items
  const compliantCount = items.filter(i => i.status === 'Compliant' || i.status === 'Current').length
  const dueSoonCount   = items.filter(i => (_isExpiringSoon(i.expiry_date) && !_isExpired(i.expiry_date)) || i.status === 'Due soon').length
  const overdueCount   = items.filter(i => _isExpired(i.expiry_date) || i.status === 'Overdue' || i.status === 'Expired').length
  const score          = items.length > 0 ? Math.round((compliantCount / items.length) * 100) : 100

  // Alert items (3.5 / 3.2) — include auto-synced items with Expired/Due Soon status
  const alertItems = items.filter(i => _isExpiringSoon(i.expiry_date) || _isExpired(i.expiry_date) || i.status === 'Overdue' || i.status === 'Expired')

  const statusBadge = (item: any) => {
    const s = item.status
    if (s === 'Compliant' || s === 'Current') return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700">{s === 'Current' ? 'Current' : 'Compliant'}</span>
    if (s === 'Overdue' || s === 'Expired' || _isExpired(item.expiry_date)) return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-red-100 text-red-600">Expired</span>
    if (s === 'Due soon' || _isExpiringSoon(item.expiry_date)) return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700">Due Soon</span>
    return <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-slate-100 text-slate-600">{s ?? 'Pending'}</span>
  }


  return (
    <div className="space-y-3">

      {/* ── 4-stat summary row (3.1) ── */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Compliant', value: compliantCount, color: 'text-emerald-600' },
          { label: 'Due Soon',  value: dueSoonCount,   color: 'text-amber-600'   },
          { label: 'Overdue',   value: overdueCount,   color: 'text-red-600'     },
          { label: 'Score',     value: `${score}%`,    color: 'text-purple-700'  },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-100 p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* ── Alert banners (3.5 / 3.2) shown ABOVE toggle ── */}
      {alertItems.map((item: any) => {
        const isAutoAlert = item.source === 'qualification' || item.source === 'certification'
        const expired = _isExpired(item.expiry_date) || item.status === 'Overdue' || item.status === 'Expired'
        const days = _daysLeft(item.expiry_date)
        return (
          <div key={item.compliance_item_id}
            className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg border ${expired ? 'bg-red-50 border-red-200 text-red-700' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-bold">{expired ? 'Expired' : 'Expiring soon'}{isAutoAlert ? ` — ${item.category}` : ' — Compliance requirement'}</p>
              <p className="text-[11px] mt-0.5">{item.requirement_name}{item.expiry_date ? ` ${expired ? `expired ${item.expiry_date.slice(0,10)}` : `expires in ${days} days`}.` : '.'}</p>
            </div>
            {!isAutoAlert && (
              <button onClick={() => remindMut.mutate(item.compliance_item_id)} disabled={remindMut.isPending}
                className="text-[10px] px-2 py-1 rounded border border-current font-semibold whitespace-nowrap shrink-0 hover:opacity-80">
                <Bell className="h-3 w-3 inline mr-0.5" /> Remind
              </button>
            )}
          </div>
        )
      })}

      {/* ── Requirements ── */}
      {(
        <div className="space-y-2">
          {items.length === 0 && !showForm && (
            <div className="text-center py-6 space-y-1">
              <p className="text-sm text-slate-400 italic">No compliance items yet.</p>
              <p className="text-[11px] text-slate-400">Qualifications &amp; certifications with expiry dates will appear here automatically. You can also add manual requirements below.</p>
            </div>
          )}
          {items.map((item: any) => {
            const id      = item.compliance_item_id
            const open    = expandedId === id
            const isAuto  = item.source === 'qualification' || item.source === 'certification'
            const pct     = _remainPct(item.completed_date, item.expiry_date) ?? 100
            const gone    = _isExpired(item.expiry_date) || item.status === 'Overdue' || item.status === 'Expired'
            const soon    = _isExpiringSoon(item.expiry_date)
            const iconBg    = gone ? '#fee2e2' : soon ? '#fef3c7' : '#d1fae5'
            const iconColor = gone ? '#dc2626' : soon ? '#d97706' : '#059669'
            return (
              <div key={id} className="border border-[#ede9ff] rounded-xl overflow-hidden bg-white">
                {/* Card header */}
                <button onClick={() => setExpandedId(open ? null : id)} className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-[#f9f8ff] text-left">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: iconBg }}>
                    <ShieldCheck className="h-4 w-4" style={{ color: iconColor }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold text-slate-800 leading-snug">{item.requirement_name}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {item.category ?? '—'}
                      {item.reference_no && ` · Ref: ${item.reference_no}`}
                      {isAuto
                        ? <span className="ml-1.5 bg-blue-50 text-blue-600 px-1 rounded text-[9px]">Auto-synced</span>
                        : item.is_mandatory && <span className="ml-1.5 bg-red-50 text-red-500 px-1 rounded text-[9px]">Mandatory</span>
                      }
                    </p>
                  </div>
                  {statusBadge(item)}
                  {open ? <ChevronUp className="h-4 w-4 text-slate-300 shrink-0" /> : <ChevronDown className="h-4 w-4 text-slate-300 shrink-0" />}
                </button>

                {/* Card body */}
                {open && (
                  <div className="px-3 pb-3 pt-2 border-t border-[#f4f2fb] bg-[#fafaff] space-y-2.5">
                    {/* Description / Notes in gray box */}
                    {item.notes && (
                      <div className="bg-slate-100 rounded-md px-2.5 py-2">
                        <p className="text-[11px] text-slate-600">{item.notes}</p>
                      </div>
                    )}
                    {/* Detail grid */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Completed</p>
                        <p className="text-[11px] text-slate-700 font-medium">{item.completed_date?.slice(0,10) ?? '—'}</p>
                      </div>
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Expiry</p>
                        <p className="text-[11px] text-slate-700 font-medium">{item.expiry_date?.slice(0,10) ?? 'No expiry'}</p>
                      </div>
                      {item.reference_no && (
                        <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                          <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Reference No.</p>
                          <p className="text-[11px] text-slate-700 font-medium">{item.reference_no}</p>
                        </div>
                      )}
                      <div className="bg-white border border-[#f0eef8] rounded-md px-2.5 py-1.5">
                        <p className="text-[9px] text-slate-400 font-semibold uppercase mb-0.5">Reminder</p>
                        <p className="text-[11px] text-slate-700 font-medium">{item.reminder_days_before ? `${item.reminder_days_before}d before` : '—'}</p>
                      </div>
                    </div>
                    {/* Validity bar (3.4) — remaining % */}
                    {item.expiry_date && (
                      <div>
                        <p className="text-[10px] text-slate-400 mb-1">Validity remaining</p>
                        <div className="h-1.5 bg-[#ede9ff] rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: _barColor(pct) }} />
                        </div>
                        {gone && <p className="text-[10px] text-red-500 mt-1">Overdue</p>}
                        {!gone && soon && <p className="text-[10px] text-amber-600 mt-1">Due in {_daysLeft(item.expiry_date)} days</p>}
                      </div>
                    )}
                    {/* Action buttons */}
                    <div className="flex gap-1.5 flex-wrap pt-0.5">
                      {item.document_url && (
                        <a href={item.document_url} target="_blank" rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold">
                          <Download className="h-3 w-3" /> Download
                        </a>
                      )}
                      {!isAuto && (
                        <label className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold cursor-pointer transition-opacity ${uploadingItemId === id ? 'opacity-50 pointer-events-none' : ''}`}>
                          <Upload className="h-3 w-3" /> {uploadingItemId === id ? 'Uploading…' : item.document_url ? 'Replace doc' : 'Upload doc'}
                          <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={e => {
                            const file = e.target.files?.[0]
                            if (file) docUploadMut.mutate({ file, itemId: id })
                            e.target.value = ''
                          }} />
                        </label>
                      )}
                      <button onClick={() => remindMut.mutate(id)} disabled={remindMut.isPending}
                        className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold">
                        <Bell className="h-3 w-3" /> {remindMut.isPending ? 'Sending…' : 'Set reminder'}
                      </button>
                      {!isAuto && (
                        <button onClick={() => updateMut.mutate({ id, d: { status: 'Compliant' } })}
                          disabled={updateMut.isPending || item.status === 'Compliant'}
                          className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-semibold disabled:opacity-50">
                          <CheckCircle className="h-3 w-3" /> Mark compliant
                        </button>
                      )}
                      {isAuto ? (
                        <span className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-blue-50 text-blue-500 font-medium italic ml-auto">
                          Edit in Quals &amp; Certs tab
                        </span>
                      ) : (
                        <button onClick={() => { if (confirm('Delete this requirement?')) deleteMut.mutate(id) }}
                          disabled={deleteMut.isPending}
                          className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-md bg-white border border-red-200 hover:bg-red-50 text-red-600 font-semibold ml-auto">
                          <Trash2 className="h-3 w-3" /> Delete
                        </button>
                      )}
                    </div>
                    {item.reminder_sent_at && (
                      <p className="text-[10px] text-slate-400 italic">Last reminder: {item.reminder_sent_at.slice(0,10)}</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}

          {/* Add form */}
          {showForm && (
            <form onSubmit={e => { e.preventDefault(); createMut.mutate(form) }} className="border border-purple-100 bg-purple-50 rounded-xl p-4 space-y-3">
              <p className="text-[11px] font-bold text-purple-700 uppercase tracking-wide">Add Compliance Requirement</p>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="col-span-2">
                  <Label text="Requirement Name" />
                  <Input value={form.requirement_name} onChange={e => setForm({ ...form, requirement_name: e.target.value })} required placeholder="e.g. NDIS Worker Screening Check" />
                </div>
                <div>
                  <Label text="Category" />
                  <Select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                    {['NDIS Screening', 'Working With Children', 'Police Check', 'First Aid', 'Training', 'Certification', 'Other'].map(c => <option key={c}>{c}</option>)}
                  </Select>
                </div>
                <div>
                  <Label text="Type" />
                  <Select value={form.requirement_type} onChange={e => setForm({ ...form, requirement_type: e.target.value })}>
                    {['Mandatory', 'Recommended', 'Role-Specific'].map(t => <option key={t}>{t}</option>)}
                  </Select>
                </div>
                <div><Label text="Reference No." /><Input value={form.reference_no} onChange={e => setForm({ ...form, reference_no: e.target.value })} placeholder="NDIS-12345" /></div>
                <div><Label text="Reminder (days before expiry)" /><Input type="number" value={form.reminder_days_before} onChange={e => setForm({ ...form, reminder_days_before: parseInt(e.target.value) || 30 })} min={1} max={365} /></div>
                <div><Label text="Completed Date" /><Input type="date" value={form.completed_date} onChange={e => setForm({ ...form, completed_date: e.target.value })} /></div>
                <div><Label text="Expiry Date" /><Input type="date" value={form.expiry_date} onChange={e => setForm({ ...form, expiry_date: e.target.value })} /></div>
                <div className="col-span-2"><Label text="Notes" /><Input value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></div>
              </div>
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input type="checkbox" checked={form.is_mandatory} onChange={e => setForm({ ...form, is_mandatory: e.target.checked })} className="rounded" /> Mandatory requirement
              </label>
              <div className="flex gap-2">
                <Btn type="submit" variant="primary" disabled={createMut.isPending}>{createMut.isPending ? 'Adding…' : 'Add Requirement'}</Btn>
                <Btn type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Btn>
              </div>
            </form>
          )}
          {!showForm && (
            <button onClick={() => setShowForm(true)} className="w-full flex items-center justify-center gap-1.5 text-[11px] font-semibold text-slate-500 hover:text-purple-700 border border-dashed border-slate-200 hover:border-purple-300 rounded-xl py-2.5 transition-colors">
              <Plus className="h-3.5 w-3.5" /> Add requirement
            </button>
          )}
        </div>
      )}

      {/* ── 3.6 Compliance History / Audit Trail ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-4">
        <button
          type="button"
          onClick={() => setShowAudit(s => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <h3 className="text-xs font-bold text-slate-700 flex items-center gap-1.5 uppercase tracking-wide">
            <Clock className="h-3.5 w-3.5 text-slate-400" /> Compliance History / Audit Trail
          </h3>
          {showAudit ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
        </button>
        {showAudit && (
          <div className="mt-3 space-y-2">
            {auditLoading ? (
              <div className="flex items-center gap-2 py-3 text-slate-400 text-xs">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading history…
              </div>
            ) : auditLog.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-2">No compliance activity recorded yet.</p>
            ) : (
              auditLog.map((a: any) => (
                <div key={a.audit_id} className="flex items-start gap-2 text-xs bg-slate-50 rounded-lg px-3 py-2">
                  <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide ${
                    a.action_type === 'created' ? 'bg-emerald-100 text-emerald-700' :
                    a.action_type === 'deleted' ? 'bg-red-100 text-red-600' :
                    a.action_type === 'reminder_sent' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {(a.action_type ?? 'update').replace(/_/g, ' ')}
                  </span>
                  <span className="flex-1 min-w-0 text-slate-600">
                    {a.action_description}
                    {a.previous_status && a.new_status && a.previous_status !== a.new_status && (
                      <> — status {a.previous_status} changed to {a.new_status}</>
                    )}
                    {' '}by <span className="font-medium text-slate-700">{a.changed_by_name ?? 'System'}</span>
                  </span>
                  <span className="shrink-0 text-slate-400">
                    {a.created_at ? new Date(a.created_at).toLocaleString('en-AU', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </section>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Leave Tab — 5.5–5.8
// ══════════════════════════════════════════════════════════════════════════════

function LeaveTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const { data: reqRes }  = useQuery({ queryKey: ['staff-leave-reqs', staffId],  queryFn: () => getLeaveRequests(tenantId, staffId) })
  const { data: balRes }  = useQuery({ queryKey: ['staff-leave-bal', staffId],   queryFn: () => getLeaveBalances(tenantId, staffId) })
  const { data: ltRes }   = useQuery({ queryKey: ['leave-types'],                queryFn: () => getLeaveTypes() })

  const requests: any[]  = reqRes?.data ?? []
  const balances: any[]  = balRes?.data ?? []
  const leaveTypes: any[] = ltRes?.data ?? []

  const [leaveView, setLeaveView] = useState<'requests' | 'balances' | 'history'>('requests')
  const [statusFilter, setStatusFilter] = useState<string>('All')
  const [form, setForm] = useState<{
    leave_type_id: string
    other_leave_name?: string
    start_date: string
    end_date: string
    reason_for_leave: string
  } | null>(null)

  const calculateDays = (sStr?: string, eStr?: string): number | null => {
    if (!sStr || !eStr) return null
    const s = new Date(sStr)
    const e = new Date(eStr)
    if (isNaN(s.getTime()) || isNaN(e.getTime())) return null
    if (e < s) return null
    const diffTime = e.getTime() - s.getTime()
    return Math.round(diffTime / (1000 * 3600 * 24)) + 1
  }

  const isDateInvalid = Boolean(form?.start_date && form?.end_date && form.end_date < form.start_date)
  const formDays = calculateDays(form?.start_date, form?.end_date)

  const createMut = useMutation({
    mutationFn: (d: any) => {
      const { other_leave_name, start_date, end_date, ...rest } = d
      let reason = rest.reason_for_leave?.trim() || null
      if (d.leave_type_id === 'OTHER' && other_leave_name) {
        reason = reason ? `[${other_leave_name.trim()}] ${reason}` : `[${other_leave_name.trim()}]`
      }
      const daysVal = calculateDays(start_date, end_date)
      const payload: any = {
        leave_type_id: rest.leave_type_id,
        start_date: start_date || null,
        end_date: end_date || null,
        total_days: daysVal,
        reason_for_leave: reason,
        submitted_date: new Date().toISOString().split('T')[0],
      }
      return createLeaveRequest(tenantId, staffId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-leave-reqs', staffId] })
      qc.invalidateQueries({ queryKey: ['staff-leave-bal', staffId] })
      setForm(null)
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      const msg = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
        ? detail.map((e: any) => e.msg || e.message).join(', ')
        : (err?.message || 'Failed to submit leave request')
      alert(`Submission failed: ${msg}`)
    },
  })

  const approveMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateLeaveRequest(tenantId, staffId, id, { leave_status: status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-leave-reqs', staffId] })
      qc.invalidateQueries({ queryKey: ['staff-leave-bal', staffId] })
    },
  })

  // Summary counts
  const pending  = requests.filter(r => r.leave_status === 'Pending').length
  const approved = requests.filter(r => r.leave_status === 'Approved').length
  const declined = requests.filter(r => r.leave_status === 'Declined').length
  const totalDays = requests
    .filter(r => r.leave_status === 'Approved')
    .reduce((s, r) => {
      let d = r.total_days
      if (d == null && r.start_date && r.end_date) {
        d = calculateDays(r.start_date, r.end_date)
      }
      return s + (Number(d ?? r.dates?.length ?? 1) || 0)
    }, 0)

  // Real DB balances only
  const displayBalances = balances.map(b => {
    const lt = leaveTypes.find((item: any) => item.leave_type_id === b.leave_type_id)
    const available = Number(b.available_balance ?? 0)
    const accrued = Number(b.accrued_leave ?? 0) + Number(b.opening_balance ?? 0)
    const used = Math.max(0, accrued - available)
    return {
      id: b.leave_balance_id,
      leave_type_id: b.leave_type_id,
      label: lt?.leave_type_name ?? b.leave_type_id,
      available,
      accrued,
      used,
      color: 'bg-purple-600',
    }
  })

  const filteredRequests = statusFilter === 'All' ? requests : requests.filter(r => r.leave_status === statusFilter)

  return (
    <div className="space-y-4">

      {/* Sub-view tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
        {(['requests', 'balances', 'history'] as const).map(v => (
          <button key={v} onClick={() => setLeaveView(v)}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold capitalize transition-all ${leaveView === v ? 'bg-white shadow text-purple-700' : 'text-slate-500 hover:text-slate-700'}`}>
            {v === 'requests' ? '📋 Requests' : v === 'balances' ? '⚖️ Balances' : '📜 History'}
          </button>
        ))}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Pending',      value: pending,   color: 'text-amber-600'   },
          { label: 'Approved',     value: approved,  color: 'text-emerald-600' },
          { label: 'Declined',     value: declined,  color: 'text-red-500'     },
          { label: 'Days Taken',   value: totalDays, color: 'text-purple-600'  },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-100 p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* ── REQUESTS VIEW ──────────────────────────────────────── */}
      {leaveView === 'requests' && (
        <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h3 className="text-sm font-bold text-slate-700">Leave Requests</h3>
            <div className="flex gap-2 items-center">
              <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="text-xs py-1 w-32">
                {['All','Pending','Approved','Declined'].map(s => <option key={s}>{s}</option>)}
              </Select>
              <Btn variant="ghost" onClick={() => setForm({ leave_type_id: '', start_date: '', end_date: '', reason_for_leave: '', other_leave_name: '' })} className="text-xs py-1">
                <Plus className="h-3 w-3" /> Apply Leave
              </Btn>
            </div>
          </div>

          {form && (
            <form onSubmit={e => {
              e.preventDefault()
              if (!form.leave_type_id || !form.start_date || !form.end_date || isDateInvalid) {
                if (isDateInvalid) alert("End date cannot be earlier than start date.")
                return
              }
              createMut.mutate(form)
            }} className="border border-purple-100 bg-purple-50/40 rounded-xl p-4 space-y-3">
              <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Apply Leave Request</p>

              <div>
                <Label text="Leave Type *" />
                <Select value={form.leave_type_id} onChange={e => setForm({ ...form, leave_type_id: e.target.value, other_leave_name: '' })} required>
                  <option value="">Select leave type…</option>
                  {leaveTypes.length === 0 && <option disabled>Loading leave types…</option>}
                  {leaveTypes.map((lt: any) => <option key={lt.leave_type_id} value={lt.leave_type_id}>{lt.leave_type_name}</option>)}
                </Select>
              </div>
              {form.leave_type_id === 'OTHER' && (
                <div>
                  <Label text="Specify Leave Name *" />
                  <Input value={form.other_leave_name ?? ''} onChange={e => setForm({ ...form, other_leave_name: e.target.value })} placeholder="e.g. Study leave, Volunteer leave…" required />
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <Label text="Start Date *" />
                  <Input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} required />
                </div>
                <div>
                  <Label text="End Date *" />
                  <Input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} required />
                  {isDateInvalid && (
                    <p className="text-xs text-red-500 mt-1 font-medium">End date cannot be earlier than start date.</p>
                  )}
                </div>
                <div>
                  <Label text="Days" />
                  <Input
                    type="text"
                    readOnly
                    value={formDays !== null ? `${formDays} day${formDays === 1 ? '' : 's'}` : '—'}
                    className="bg-slate-100/70 font-semibold text-slate-700 cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <Label text="Reason" />
                <Textarea value={form.reason_for_leave} onChange={e => setForm({ ...form, reason_for_leave: e.target.value })} placeholder="Optional reason…" />
              </div>

              <div className="flex gap-2">
                <Btn type="submit" variant="primary" disabled={createMut.isPending || isDateInvalid}>{createMut.isPending ? 'Submitting…' : 'Submit Request'}</Btn>
                <Btn type="button" variant="secondary" onClick={() => setForm(null)}>Cancel</Btn>
              </div>
            </form>
          )}

          <div className="space-y-2">
            {filteredRequests.length === 0 && !form && (
              <p className="text-sm text-slate-400 italic text-center py-4">No {statusFilter !== 'All' ? statusFilter.toLowerCase() : ''} leave requests.</p>
            )}
            {filteredRequests.map((r: any) => {
              const ltName = leaveTypes.find((lt: any) => lt.leave_type_id === r.leave_type_id)?.leave_type_name ?? r.leave_type_id
              const otherMatch = r.leave_type_id === 'OTHER' && r.reason_for_leave?.match(/^\[([^\]]+)\]/)
              const displayName = otherMatch ? `Other — ${otherMatch[1]}` : ltName
              const displayReason = otherMatch
                ? r.reason_for_leave.replace(/^\[[^\]]+\]\s*/, '').slice(0, 60) || null
                : r.reason_for_leave?.slice(0, 60)

              const startDateStr = r.start_date || (r.dates && r.dates.length > 0 ? r.dates[0].leave_date : null) || r.submitted_date
              const endDateStr = r.end_date || (r.dates && r.dates.length > 0 ? r.dates[r.dates.length - 1].leave_date : null) || startDateStr
              const fmtD = (d?: string) => d ? new Date(d).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'

              const daysVal = (() => {
                if (r.total_days != null) return r.total_days
                if (startDateStr && endDateStr) {
                  const s = new Date(startDateStr)
                  const e = new Date(endDateStr)
                  if (!isNaN(s.getTime()) && !isNaN(e.getTime()) && e >= s) {
                    return Math.round((e.getTime() - s.getTime()) / (1000 * 3600 * 24)) + 1
                  }
                }
                return r.dates?.length ?? 1
              })()

              return (
                <div key={r.leave_request_id} className={`border rounded-lg p-3 flex items-start gap-3 ${r.leave_status === 'Pending' ? 'border-amber-200 bg-amber-50/20' : 'border-slate-100'}`}>
                  <Calendar className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-slate-700">{displayName}</p>
                      <span className="text-[10px] font-semibold bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">{daysVal} day{daysVal === 1 ? '' : 's'}</span>
                    </div>
                    {startDateStr && <p className="text-xs text-slate-500 mt-0.5">{fmtD(startDateStr)} {endDateStr && endDateStr !== startDateStr ? `– ${fmtD(endDateStr)}` : ''}</p>}
                    {displayReason && <p className="text-xs text-slate-500 mt-0.5">{displayReason}</p>}
                    {r.submitted_date && <p className="text-[10px] text-slate-400 mt-0.5">Submitted: {new Date(r.submitted_date).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })}</p>}
                    {r.decline_reason && <p className="text-xs text-red-500 mt-0.5 italic">Decline reason: {r.decline_reason}</p>}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${leaveBadge(r.leave_status)}`}>{r.leave_status}</span>
                    {r.leave_status === 'Pending' && (
                      <div className="flex gap-1">
                        <button onClick={() => approveMut.mutate({ id: r.leave_request_id, status: 'Approved' })} title="Approve" className="text-emerald-600 hover:text-emerald-700"><CheckCircle className="h-4 w-4" /></button>
                        <button onClick={() => approveMut.mutate({ id: r.leave_request_id, status: 'Declined' })} title="Decline" className="text-red-400 hover:text-red-600"><X className="h-4 w-4" /></button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* ── BALANCES VIEW ───────────────────────────────────────────── */}
      {leaveView === 'balances' && (
        <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-700">Leave Balances</h3>
            <p className="text-xs text-slate-400">Financial year 2025–2026 · Hours</p>
          </div>
          {displayBalances.length === 0 ? (
            <div className="text-center py-8 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
              <p className="text-sm font-medium text-slate-600">No leave balances recorded</p>
              <p className="text-xs text-slate-400 mt-1">Available balance is 0h. Balances will appear once leave allocations or accruals are recorded.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {displayBalances.map((b: any) => {
                const pct = b.accrued > 0 ? Math.min(100, Math.round((b.used / b.accrued) * 100)) : 0
                return (
                  <div key={b.id} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">{b.label}</span>
                      <span className="text-xs text-slate-500">
                        <span className="font-semibold text-slate-700">{b.available}h</span> available of {b.accrued}h
                      </span>
                    </div>
                    <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${b.color} opacity-80 transition-all`} style={{ width: `${pct}%` }} />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>{b.used}h used</span>
                      <span>{pct}% utilised</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      )}

      {/* ── HISTORY VIEW ───────────────────────────────────────────── */}
      {leaveView === 'history' && (() => {
        const fmtD = (d?: string) => d ? new Date(d).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
        const realHistory = requests.filter((r: any) => r.leave_status === 'Approved' || r.leave_status === 'Declined')
        return (
          <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-700">Leave History</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400">
                    <th className="text-left pb-2 font-medium">Leave Type</th>
                    <th className="text-left pb-2 font-medium">Start Date</th>
                    <th className="text-left pb-2 font-medium">End Date</th>
                    <th className="text-center pb-2 font-medium">Days</th>
                    <th className="text-left pb-2 font-medium">Status</th>
                    <th className="text-left pb-2 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {realHistory.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-xs text-slate-400 italic">
                        No leave history recorded.
                      </td>
                    </tr>
                  ) : (
                    realHistory.map((r: any) => {
                      const ltName = leaveTypes.find((lt: any) => lt.leave_type_id === r.leave_type_id)?.leave_type_name ?? r.leave_type_id ?? '—'
                      const startDateStr = r.start_date || (r.dates && r.dates.length > 0 ? r.dates[0].leave_date : null) || r.submitted_date || r.created_at
                      const endDateStr = r.end_date || (r.dates && r.dates.length > 0 ? r.dates[r.dates.length - 1].leave_date : null) || startDateStr

                      const daysVal = (() => {
                        if (r.total_days != null && !isNaN(Number(r.total_days))) return String(r.total_days)
                        if (startDateStr && endDateStr) {
                          const s = new Date(startDateStr)
                          const e = new Date(endDateStr)
                          if (!isNaN(s.getTime()) && !isNaN(e.getTime()) && e >= s) {
                            return String(Math.round((e.getTime() - s.getTime()) / (1000 * 3600 * 24)) + 1)
                          }
                        }
                        if (r.dates && r.dates.length > 0) return String(r.dates.length)
                        return 'N/A'
                      })()

                      const reason = r.reason_for_leave?.replace(/^\[[^\]]+\]\s*/, '').slice(0, 60) || (r.decline_reason ? `Declined: ${r.decline_reason.slice(0, 50)}` : '—')

                      return (
                        <tr key={r.leave_request_id}>
                          <td className="py-2.5 font-medium text-slate-700">{ltName}</td>
                          <td className="py-2.5 text-slate-500">{fmtD(startDateStr)}</td>
                          <td className="py-2.5 text-slate-500">{fmtD(endDateStr)}</td>
                          <td className="py-2.5 text-center font-semibold text-slate-700">{daysVal}</td>
                          <td className="py-2.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${r.leave_status === 'Approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'}`}>{r.leave_status}</span>
                          </td>
                          <td className="py-2.5 text-slate-400 italic max-w-[140px] truncate">{reason}</td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )
      })()}

    </div>
  )
}

// ── Availability & Roster sample data ─────────────────────────────────────────
const SAMPLE_SHIFTS_TMPL = [
  { id: 'S1', dayIndex: 0, startH: 7,  endH: 15, type: 'Morning',           location: 'Eastwood Community Centre',  recurring: true,  status: 'Confirmed', bg: 'bg-blue-500'   },
  { id: 'S2', dayIndex: 1, startH: 7,  endH: 15, type: 'Morning',           location: 'Eastwood Community Centre',  recurring: true,  status: 'Confirmed', bg: 'bg-blue-500'   },
  { id: 'S3', dayIndex: 2, startH: 14, endH: 22, type: 'Afternoon',         location: 'Home Care – Client A',       recurring: false, status: 'Confirmed', bg: 'bg-purple-500' },
  { id: 'S4', dayIndex: 3, startH: 7,  endH: 15, type: 'Morning',           location: 'Eastwood Community Centre',  recurring: true,  status: 'Pending',   bg: 'bg-amber-400'  },
  { id: 'S5', dayIndex: 4, startH: 9,  endH: 17, type: 'Community Support', location: 'Various Locations',          recurring: false, status: 'Confirmed', bg: 'bg-indigo-500' },
  { id: 'S6', dayIndex: 5, startH: 8,  endH: 14, type: 'Casual',            location: 'Home Care – Client B',       recurring: false, status: 'Confirmed', bg: 'bg-teal-500'   },
]
const SAMPLE_PATTERNS = [
  { id: 'RP1', name: 'Weekday Mornings', days: 'Mon – Fri', time: '7:00 AM – 3:00 PM', type: 'Morning', active: true,  since: '01 Jan 2024' },
  { id: 'RP2', name: 'Weekend Casual',   days: 'Saturday',  time: '8:00 AM – 2:00 PM', type: 'Casual',  active: true,  since: '01 Mar 2024' },
  { id: 'RP3', name: 'On-Call Weekends', days: 'Sunday',    time: '6:00 PM – 10:00 PM',type: 'On-Call', active: false, since: '01 Jun 2024' },
]
const CAL_START_H = 6
const CAL_END_H   = 22
const ROW_PX      = 40

// ══════════════════════════════════════════════════════════════════════════════
// Availability Tab — 4.1–4.7
// ══════════════════════════════════════════════════════════════════════════════

const AVAIL_TYPES    = ['Regular', 'Casual', 'On-Call', 'Overtime', 'Temporary']
const AVAIL_STATUSES = ['Active', 'Inactive', 'Pending']
const DAY_NAMES      = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const SHIFT_STATUSES = ['Confirmed', 'Pending', 'Cancelled']

function AvailabilityTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const { can } = usePermissions()
  const { data: res } = useQuery({
    queryKey: ['staff-avail', staffId],
    queryFn: () => getAvailability(tenantId, staffId),
  })
  const records: any[] = res?.data ?? []

  const [subView, setSubView] = useState<'records' | 'calendar' | 'roster'>('records')
  const [calWeekOffset, setCalWeekOffset] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [showShiftForm, setShowShiftForm] = useState(false)
  const [editRec, setEditRec] = useState<any>(null)

  // ── Shifts & roster (4.3–4.5) — backend-persisted, visible to every admin,
  // not just the browser that created them.
  const { data: shiftsRes } = useQuery({
    queryKey: ['staff-shifts', staffId],
    queryFn: () => getShifts(tenantId, staffId),
  })
  const SHIFT_TYPE_COLORS: Record<string, string> = {
    Morning: 'bg-blue-500', Afternoon: 'bg-purple-500', Night: 'bg-indigo-500',
    'Community Support': 'bg-teal-500', Casual: 'bg-emerald-500', 'On-Call': 'bg-amber-500',
  }
  const extraShifts = useMemo(() => ((shiftsRes as any)?.data ?? []).map((s: any) => ({
    id: s.shift_id,
    dayIndex: s.day_of_week,
    startH: s.start_hour,
    endH: s.end_hour,
    type: s.shift_type ?? 'Shift',
    location: s.location ?? '',
    recurring: !!s.is_recurring,
    recurringFrom: s.recurring_from ?? '',
    recurringTo: s.recurring_to ?? '',
    status: s.shift_status ?? 'Confirmed',
    bg: SHIFT_TYPE_COLORS[s.shift_type] ?? 'bg-blue-500',
  })), [shiftsRes])

  const [editExtraShift, setEditExtraShift] = useState<any>(null)   // extraShift being edited
  const BLANK_SHIFT = { dayIndex: 0, startH: 9, endH: 17, type: 'Morning', location: '', recurring: false, recurringFrom: '', recurringTo: '', status: 'Confirmed', bg: 'bg-blue-500' }
  const [newShift, setNewShift] = useState(BLANK_SHIFT)

  const shiftAddMut = useMutation({
    mutationFn: (s: typeof newShift) => createShift(tenantId, staffId, {
      day_of_week: s.dayIndex, shift_type: s.type, start_hour: s.startH, end_hour: s.endH,
      location: s.location || undefined, shift_status: s.status,
      is_recurring: s.recurring,
      recurring_from: s.recurring ? s.recurringFrom : undefined,
      recurring_to: s.recurring && s.recurringTo ? s.recurringTo : undefined,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-shifts', staffId] }); setShowShiftForm(false); setNewShift(BLANK_SHIFT) },
    onError: (err: any) => alert(`Failed to add shift: ${err?.response?.data?.detail ?? err?.message ?? 'Unknown error'}`),
  })
  const shiftUpdateMut = useMutation({
    mutationFn: ({ id, s }: { id: string; s: any }) => updateShift(tenantId, staffId, id, {
      day_of_week: s.dayIndex, shift_type: s.type, start_hour: s.startH, end_hour: s.endH,
      location: s.location || undefined, shift_status: s.status,
      is_recurring: s.recurring,
      recurring_from: s.recurring ? (s.recurringFrom || null) : null,
      recurring_to: s.recurring ? (s.recurringTo || null) : null,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-shifts', staffId] }); setEditExtraShift(null) },
    onError: (err: any) => alert(`Failed to update shift: ${err?.response?.data?.detail ?? err?.message ?? 'Unknown error'}`),
  })
  const shiftDeleteMut = useMutation({
    mutationFn: (id: string) => deleteShift(tenantId, staffId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-shifts', staffId] }),
  })

  const BLANK_FORM = {
    availability_type: 'Regular', availability_status: 'Active',
    availability_effective_from: '', availability_effective_to: '',
    available_for_overtime: false, available_for_on_call: false, availability_notes: '',
  }
  const [form, setForm] = useState<any>(BLANK_FORM)

  const addMut = useMutation({
    mutationFn: (d: any) => createAvailability(tenantId, staffId, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-avail', staffId] }); setShowForm(false); setForm(BLANK_FORM) },
  })
  const editMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateAvailability(tenantId, staffId, id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['staff-avail', staffId] }); setEditRec(null) },
    onError: (err: any) => alert(`Save failed: ${err?.response?.data?.detail ?? err?.message ?? 'Unknown error'}`),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteAvailability(tenantId, staffId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-avail', staffId] }),
  })

  const fmt = (dt?: string) => {
    if (!dt) return '—'
    return new Date(dt).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  const isActive = (r: any) => {
    const now = new Date()
    if (r.availability_status !== 'Active') return false
    const from = r.availability_effective_from ? new Date(r.availability_effective_from) : null
    const to   = r.availability_effective_to   ? new Date(r.availability_effective_to)   : null
    if (from && from > now) return false
    if (to   && to   < now) return false
    return true
  }

  // 4.7 Conflict detection — overlapping active records
  const conflicts = useMemo(() => {
    const active = records.filter(isActive)
    const found: string[] = []
    for (let i = 0; i < active.length; i++) {
      for (let j = i + 1; j < active.length; j++) {
        const a = active[i]; const b = active[j]
        const aFrom = a.availability_effective_from ? new Date(a.availability_effective_from).getTime() : 0
        const aTo   = a.availability_effective_to   ? new Date(a.availability_effective_to).getTime()   : Infinity
        const bFrom = b.availability_effective_from ? new Date(b.availability_effective_from).getTime() : 0
        const bTo   = b.availability_effective_to   ? new Date(b.availability_effective_to).getTime()   : Infinity
        if (aFrom < bTo && bFrom < aTo) {
          if (!found.includes(a.availability_id)) found.push(a.availability_id)
          if (!found.includes(b.availability_id)) found.push(b.availability_id)
        }
      }
    }
    return found
  }, [records])

  // 4.7 Conflict detection (shifts) — two shifts on the same day of the week
  // with overlapping hours. Both one-off and recurring shifts are checked;
  // for a recurring vs. recurring pair, only flagged if their recurring
  // date ranges also overlap (so a Mon-morning shift that ended last year
  // doesn't falsely conflict with a new one starting this year).
  const shiftConflicts = useMemo(() => {
    const found: string[] = []
    const rangesOverlap = (a: any, b: any) => {
      if (!a.recurring && !b.recurring) return true // both one-off — day+hour match is enough
      const aFrom = a.recurring && a.recurringFrom ? new Date(a.recurringFrom).getTime() : -Infinity
      const aTo   = a.recurring && a.recurringTo   ? new Date(a.recurringTo).getTime()   : Infinity
      const bFrom = b.recurring && b.recurringFrom ? new Date(b.recurringFrom).getTime() : -Infinity
      const bTo   = b.recurring && b.recurringTo   ? new Date(b.recurringTo).getTime()   : Infinity
      return aFrom < bTo && bFrom < aTo
    }
    for (let i = 0; i < extraShifts.length; i++) {
      for (let j = i + 1; j < extraShifts.length; j++) {
        const a = extraShifts[i]; const b = extraShifts[j]
        if (a.dayIndex !== b.dayIndex) continue
        if (a.startH >= b.endH || b.startH >= a.endH) continue // no hour overlap
        if (!rangesOverlap(a, b)) continue
        if (!found.includes(a.id)) found.push(a.id)
        if (!found.includes(b.id)) found.push(b.id)
      }
    }
    return found
  }, [extraShifts])

  // 4.2/4.6 Calendar — week dates
  const weekDates = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7) + calWeekOffset * 7)
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      return d
    })
  }, [calWeekOffset])

  const hourLabels = Array.from({ length: CAL_END_H - CAL_START_H }, (_, i) => CAL_START_H + i)

  // ── Calendar helpers ─────────────────────────────────────────────────────────
  // Type → Tailwind bg colour
  const TYPE_COLORS: Record<string, string> = {
    Regular:   'bg-blue-500',
    Casual:    'bg-teal-500',
    'On-Call': 'bg-purple-500',
    Overtime:  'bg-amber-400',
    Temporary: 'bg-indigo-500',
  }
  // Type → default [startHour, endHour] when no specific time is stored
  const TYPE_HOURS: Record<string, [number, number]> = {
    Regular:   [7, 15],
    Casual:    [8, 14],
    'On-Call': [18, 22],
    Overtime:  [15, 23],
    Temporary: [9, 17],
  }

  const calBlocks = useMemo(() => {
    const blocks: {
      id: string; dayIndex: number; startH: number; endH: number
      type: string; location: string; bg: string
    }[] = []

    weekDates.forEach((dayDate, dayIndex) => {
      const dayStart = new Date(dayDate); dayStart.setHours(0, 0, 0, 0)
      const dayEnd   = new Date(dayDate); dayEnd.setHours(23, 59, 59, 999)

      // Deduplicate: one block per availability_type per day.
      // Availability records are date-ranges — a "Regular Jan–Dec" record should
      // show on EVERY day it covers, but NOT as multiple stacked duplicates.
      const seenTypes = new Set<string>()

      records.forEach(r => {
        if (r.availability_status !== 'Active') return
        const from = r.availability_effective_from ? new Date(r.availability_effective_from) : null
        const to   = r.availability_effective_to   ? new Date(r.availability_effective_to)   : null
        // skip if record's range doesn't cover this day
        if (from && from > dayEnd)   return
        if (to   && to   < dayStart) return

        const type = r.availability_type ?? 'Regular'
        if (seenTypes.has(type)) return   // already have this type on this day
        seenTypes.add(type)

        const [defStart, defEnd] = TYPE_HOURS[type] ?? [9, 17]

        // Use the record's specific time only when its from/to falls ON this exact
        // day and has a non-midnight time — otherwise use the type default.
        const fromSameDay = from && from >= dayStart && from <= dayEnd
        const toSameDay   = to   && to   >= dayStart && to   <= dayEnd
        const startH = (fromSameDay && from!.getHours() !== 0) ? from!.getHours() : defStart
        const endH   = (toSameDay   && to!.getHours()   !== 0) ? to!.getHours()   : defEnd

        blocks.push({
          id: `${r.availability_id}-d${dayIndex}`,
          dayIndex, startH, endH: Math.max(startH + 1, endH),
          type,
          location: r.availability_notes ?? '',
          bg: TYPE_COLORS[type] ?? 'bg-slate-400',
        })
      })
    })
    return blocks
  }, [records, weekDates])

  return (
    <div className="space-y-4">

      {/* Sub-view tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
        {(['records', 'calendar', 'roster'] as const).map(v => (
          <button
            key={v}
            onClick={() => setSubView(v)}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold capitalize transition-all ${
              subView === v ? 'bg-white shadow text-purple-700' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {v === 'records' ? '📋 Records' : v === 'calendar' ? '📅 Calendar' : '📆 Roster'}
          </button>
        ))}
      </div>

      {/* 4.7 Conflict banner */}
      {conflicts.length > 0 && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-700">Availability Conflict Detected</p>
            <p className="text-xs text-red-600 mt-0.5">
              {conflicts.length} active record{conflicts.length > 1 ? 's' : ''} overlap in date range. Review and resolve below.
            </p>
          </div>
        </div>
      )}

      {/* 4.7 Conflict banner (shifts) */}
      {shiftConflicts.length > 0 && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-700">Shift Conflict Detected</p>
            <p className="text-xs text-red-600 mt-0.5">
              {shiftConflicts.length} rostered shift{shiftConflicts.length > 1 ? 's' : ''} overlap on the same day. Review in the Roster tab.
            </p>
          </div>
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total Records',    value: records.length,                                             color: 'text-slate-700'   },
          { label: 'Active Now',       value: records.filter(isActive).length,                            color: 'text-emerald-600' },
          { label: 'On-Call Eligible', value: records.filter(r => r.available_for_on_call && isActive(r)).length, color: 'text-purple-600' },
          { label: 'Shifts This Week', value: calBlocks.length + extraShifts.length,                    color: 'text-blue-600'    },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-100 p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* ── RECORDS VIEW (4.1) ─────────────────────────────────────────────── */}
      {subView === 'records' && (
        <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-700">Availability Records</h3>
            <Btn variant="ghost" onClick={() => setShowForm(v => !v)} className="text-xs py-1">
              <Plus className="h-3 w-3" /> Add Record
            </Btn>
          </div>

          {showForm && (
            <form onSubmit={e => { e.preventDefault(); addMut.mutate(form) }}
              className="border border-purple-100 bg-purple-50/40 rounded-xl p-4 space-y-4">
              <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">New Availability Record</p>
              <div className="grid grid-cols-2 gap-3">
                <div><Label text="Availability Type" /><Select value={form.availability_type} onChange={e => setForm({ ...form, availability_type: e.target.value })}>{AVAIL_TYPES.map(t => <option key={t}>{t}</option>)}</Select></div>
                <div><Label text="Status" /><Select value={form.availability_status} onChange={e => setForm({ ...form, availability_status: e.target.value })}>{AVAIL_STATUSES.map(s => <option key={s}>{s}</option>)}</Select></div>
                <div><Label text="Effective From" /><Input type="datetime-local" value={form.availability_effective_from} onChange={e => setForm({ ...form, availability_effective_from: e.target.value })} /></div>
                <div><Label text="Effective To" /><Input type="datetime-local" value={form.availability_effective_to} onChange={e => setForm({ ...form, availability_effective_to: e.target.value })} /></div>
              </div>
              <div className="flex gap-5">
                {(['available_for_overtime', 'available_for_on_call'] as const).map(field => (
                  <label key={field} className="flex items-center gap-2 text-sm cursor-pointer select-none">
                    <button type="button" onClick={() => setForm((f: any) => ({ ...f, [field]: !f[field] }))}
                      className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${form[field] ? 'bg-purple-500' : 'bg-slate-200'}`}>
                      <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${form[field] ? 'translate-x-4' : 'translate-x-0'}`} />
                    </button>
                    {field === 'available_for_overtime' ? 'Available for Overtime' : 'Available for On-Call'}
                  </label>
                ))}
              </div>
              <div><Label text="Notes" /><Textarea value={form.availability_notes} onChange={e => setForm({ ...form, availability_notes: e.target.value })} placeholder="Any additional notes…" /></div>
              <div className="flex gap-2">
                <Btn type="submit" variant="primary" disabled={addMut.isPending}>{addMut.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving…</> : 'Save Record'}</Btn>
                <Btn type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Btn>
              </div>
            </form>
          )}

          {records.length === 0 && !showForm ? (
            <div className="py-8 text-center text-slate-400">
              <Clock className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No availability records yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {records.map((r: any) => {
                const active = isActive(r)
                const hasConflict = conflicts.includes(r.availability_id)
                const isEditing = editRec?.availability_id === r.availability_id
                return (
                  <div key={r.availability_id}>
                    {isEditing && (
                      <form onSubmit={e => { e.preventDefault(); editMut.mutate({ id: r.availability_id, data: editRec }) }}
                        className="border border-purple-100 bg-purple-50/40 rounded-xl p-4 space-y-4 mb-2">
                        <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Edit Availability Record</p>
                        <div className="grid grid-cols-2 gap-3">
                          <div><Label text="Availability Type" /><Select value={editRec.availability_type ?? 'Regular'} onChange={e => setEditRec({ ...editRec, availability_type: e.target.value })}>{AVAIL_TYPES.map(t => <option key={t}>{t}</option>)}</Select></div>
                          <div><Label text="Status" /><Select value={editRec.availability_status ?? 'Active'} onChange={e => setEditRec({ ...editRec, availability_status: e.target.value })}>{AVAIL_STATUSES.map(s => <option key={s}>{s}</option>)}</Select></div>
                          <div><Label text="Effective From" /><Input type="datetime-local" value={editRec.availability_effective_from ? new Date(editRec.availability_effective_from).toISOString().slice(0,16) : ''} onChange={e => setEditRec({ ...editRec, availability_effective_from: e.target.value })} /></div>
                          <div><Label text="Effective To" /><Input type="datetime-local" value={editRec.availability_effective_to ? new Date(editRec.availability_effective_to).toISOString().slice(0,16) : ''} onChange={e => setEditRec({ ...editRec, availability_effective_to: e.target.value })} /></div>
                        </div>
                        <div className="flex gap-5">
                          {(['available_for_overtime', 'available_for_on_call'] as const).map(field => (
                            <label key={field} className="flex items-center gap-2 text-sm cursor-pointer select-none">
                              <button type="button" onClick={() => setEditRec((f: any) => ({ ...f, [field]: !f[field] }))}
                                className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${editRec[field] ? 'bg-purple-500' : 'bg-slate-200'}`}>
                                <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${editRec[field] ? 'translate-x-4' : 'translate-x-0'}`} />
                              </button>
                              {field === 'available_for_overtime' ? 'Available for Overtime' : 'Available for On-Call'}
                            </label>
                          ))}
                        </div>
                        <div><Label text="Notes" /><Textarea value={editRec.availability_notes ?? ''} onChange={e => setEditRec({ ...editRec, availability_notes: e.target.value })} /></div>
                        <div className="flex gap-2">
                          <Btn type="submit" variant="primary" disabled={editMut.isPending}>{editMut.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving…</> : 'Save Changes'}</Btn>
                          <Btn type="button" variant="secondary" onClick={() => setEditRec(null)}>Cancel</Btn>
                        </div>
                      </form>
                    )}
                    <div className={`rounded-lg border p-4 ${hasConflict ? 'border-red-200 bg-red-50/30' : active ? 'border-emerald-200 bg-emerald-50/30' : 'border-slate-100 bg-white'}`}>
                      <div className="flex items-start gap-3">
                        <div className={`shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${hasConflict ? 'bg-red-100' : active ? 'bg-emerald-100' : 'bg-slate-100'}`}>
                          {hasConflict
                            ? <AlertTriangle className="h-4 w-4 text-red-500" />
                            : <Clock className={`h-4 w-4 ${active ? 'text-emerald-600' : 'text-slate-400'}`} />
                          }
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-semibold text-slate-700">{r.availability_type ?? 'General'}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${r.availability_status === 'Active' ? 'bg-emerald-100 text-emerald-700' : r.availability_status === 'Inactive' ? 'bg-slate-100 text-slate-500' : 'bg-amber-100 text-amber-700'}`}>{r.availability_status ?? 'Unknown'}</span>
                            {hasConflict && <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-red-100 text-red-600">⚠ Conflict</span>}
                            {r.available_for_overtime && <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-purple-100 text-purple-700">Overtime</span>}
                            {r.available_for_on_call && <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">On-Call</span>}
                          </div>
                          <p className="text-xs text-slate-500 mt-1">
                            {r.availability_effective_from || r.availability_effective_to
                              ? <>{fmt(r.availability_effective_from)} → {r.availability_effective_to ? fmt(r.availability_effective_to) : 'Ongoing'}</>
                              : 'No date range set'}
                          </p>
                          {r.availability_notes && <p className="text-xs text-slate-500 mt-1 italic">{r.availability_notes}</p>}
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <div className="text-right mr-2">
                            <p className="text-[10px] text-slate-400">Added</p>
                            <p className="text-[10px] text-slate-500">{fmt(r.created_at)}</p>
                          </div>
                          <button onClick={() => setEditRec({ ...r })} className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600" title="Edit"><Pencil className="h-3.5 w-3.5" /></button>
                          <button onClick={() => { if (confirm('Delete this record?')) deleteMut.mutate(r.availability_id) }} disabled={deleteMut.isPending} className="p-1.5 rounded hover:bg-red-50 text-slate-400 hover:text-red-500" title="Delete"><Trash2 className="h-3.5 w-3.5" /></button>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      )}

      {/* ── CALENDAR VIEW (4.2, 4.6) ──────────────────────────────────────── */}
      {subView === 'calendar' && (
        <section className="bg-white rounded-xl border border-slate-100 overflow-hidden">
          {/* Week navigator */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
            <button onClick={() => setCalWeekOffset(o => o - 1)} className="p-1.5 rounded hover:bg-slate-100 text-slate-500">‹</button>
            <span className="text-sm font-semibold text-slate-700">
              {weekDates[0].toLocaleDateString('en-AU', { day: '2-digit', month: 'short' })} –{' '}
              {weekDates[6].toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })}
            </span>
            <div className="flex gap-1">
              <button onClick={() => setCalWeekOffset(0)} className="text-xs text-purple-600 hover:underline px-2">Today</button>
              <button onClick={() => setCalWeekOffset(o => o + 1)} className="p-1.5 rounded hover:bg-slate-100 text-slate-500">›</button>
            </div>
          </div>

          <div className="flex overflow-x-auto">
            {/* Hour column */}
            <div className="shrink-0 w-14 border-r border-slate-100" style={{ marginTop: 40 }}>
              {hourLabels.map(h => (
                <div key={h} className="flex items-start justify-end pr-2" style={{ height: ROW_PX }}>
                  <span className="text-[10px] text-slate-400 -mt-2">{h}:00</span>
                </div>
              ))}
            </div>

            {/* Day columns */}
            {weekDates.map((d, dayIdx) => {
              const isToday = d.toDateString() === new Date().toDateString()
              const dayShifts = [...calBlocks, ...extraShifts].filter(s => s.dayIndex === dayIdx)

              // Detect overlapping blocks (same hour range) and split them side-by-side
              // Build groups: blocks in the same time slot get equal-width columns
              type Block = typeof dayShifts[number]
              const overlaps = (a: Block, b: Block) => a.startH < b.endH && b.startH < a.endH
              const cols: Block[][] = []
              dayShifts.forEach(s => {
                const col = cols.find(c => !c.some(b => overlaps(b, s)))
                if (col) col.push(s)
                else cols.push([s])
              })
              const totalCols = cols.length || 1

              return (
                <div key={dayIdx} className="flex-1 min-w-[90px] border-r border-slate-100 last:border-r-0">
                  {/* Day header */}
                  <div className={`h-10 flex flex-col items-center justify-center border-b border-slate-100 ${isToday ? 'bg-purple-50' : ''}`}>
                    <span className="text-[10px] text-slate-500">{DAY_NAMES[dayIdx]}</span>
                    <span className={`text-sm font-bold ${isToday ? 'text-purple-600' : 'text-slate-700'}`}>{d.getDate()}</span>
                  </div>
                  {/* Hour grid */}
                  <div className="relative" style={{ height: (CAL_END_H - CAL_START_H) * ROW_PX }}>
                    {hourLabels.map(h => (
                      <div key={h} className="absolute w-full border-t border-slate-50" style={{ top: (h - CAL_START_H) * ROW_PX }} />
                    ))}
                    {cols.map((colBlocks, colIdx) =>
                      colBlocks.map(s => {
                        // Clamp start/end to grid bounds
                        const clampedStart = Math.max(s.startH, CAL_START_H)
                        const clampedEnd   = Math.min(s.endH,   CAL_END_H)
                        if (clampedEnd <= clampedStart) return null
                        const top    = (clampedStart - CAL_START_H) * ROW_PX
                        const height = (clampedEnd - clampedStart) * ROW_PX
                        const pct    = 100 / totalCols
                        return (
                          <div
                            key={s.id}
                            className={`absolute rounded-md px-1.5 py-1 text-white overflow-hidden ${s.bg}`}
                            style={{
                              top, height,
                              left:  `calc(${colIdx * pct}% + 2px)`,
                              width: `calc(${pct}% - 4px)`,
                            }}
                          >
                            <p className="text-[10px] font-bold leading-tight truncate">{s.type}</p>
                            <p className="text-[9px] opacity-90 leading-tight">{clampedStart}:00–{clampedEnd}:00</p>
                            {height >= 60 && s.location && (
                              <p className="text-[9px] opacity-80 leading-tight mt-0.5 truncate">{s.location}</p>
                            )}
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Empty state */}
          {calBlocks.length === 0 && extraShifts.length === 0 && (
            <div className="px-5 py-6 text-center text-slate-400 border-t border-slate-50">
              <p className="text-sm">No availability this week.</p>
              <p className="text-xs mt-0.5">Add availability records in the Records tab to populate the calendar.</p>
            </div>
          )}

          {/* Legend */}
          <div className="px-5 py-3 border-t border-slate-100 flex flex-wrap gap-3">
            {Object.entries(TYPE_COLORS).map(([label, bg]) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className={`h-2.5 w-2.5 rounded-sm ${bg}`} />
                <span className="text-[10px] text-slate-500">{label}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── ROSTER VIEW (4.3, 4.4, 4.5) ──────────────────────────────────── */}
      {subView === 'roster' && (
        <div className="space-y-4">
          {/* Shift list (4.3, 4.4) */}
          <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-700">Scheduled Shifts</h3>
              {can('schedules:create') && (
                <Btn variant="ghost" onClick={() => setShowShiftForm(v => !v)} className="text-xs py-1"><Plus className="h-3 w-3" /> Add Shift</Btn>
              )}
            </div>

            {showShiftForm && (
              <div className="border border-blue-100 bg-blue-50/30 rounded-xl p-4 space-y-3">
                <p className="text-xs font-bold text-blue-700 uppercase tracking-wide">New Shift Assignment</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label text="Day" />
                    <Select value={newShift.dayIndex} onChange={e => setNewShift({ ...newShift, dayIndex: +e.target.value })}>
                      {DAY_NAMES.map((d, i) => <option key={d} value={i}>{d}</option>)}
                    </Select>
                  </div>
                  <div>
                    <Label text="Shift Type" />
                    <Select value={newShift.type} onChange={e => setNewShift({ ...newShift, type: e.target.value })}>
                      {['Morning', 'Afternoon', 'Night', 'Community Support', 'Casual', 'On-Call'].map(t => <option key={t}>{t}</option>)}
                    </Select>
                  </div>
                  <div>
                    <Label text="Start Hour (24h)" />
                    <Input type="number" min={0} max={23} value={newShift.startH} onChange={e => setNewShift({ ...newShift, startH: +e.target.value })} />
                  </div>
                  <div>
                    <Label text="End Hour (24h)" />
                    <Input type="number" min={1} max={24} value={newShift.endH} onChange={e => setNewShift({ ...newShift, endH: +e.target.value })} />
                  </div>
                  <div>
                    <Label text="Status" />
                    <Select value={newShift.status} onChange={e => setNewShift({ ...newShift, status: e.target.value })}>
                      {SHIFT_STATUSES.map(s => <option key={s}>{s}</option>)}
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <Label text="Location" />
                    <Input value={newShift.location} onChange={e => setNewShift({ ...newShift, location: e.target.value })} placeholder="Location or client site" />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                  <button type="button" onClick={() => setNewShift(s => ({ ...s, recurring: !s.recurring }))}
                    className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${newShift.recurring ? 'bg-blue-500' : 'bg-slate-200'}`}>
                    <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${newShift.recurring ? 'translate-x-4' : 'translate-x-0'}`} />
                  </button>
                  Recurring weekly
                </label>
                {newShift.recurring && (
                  <div className="grid grid-cols-2 gap-3 border border-blue-100 bg-blue-50/40 rounded-lg p-3">
                    <div><Label text="Recurring From *" /><Input type="date" value={newShift.recurringFrom} onChange={e => setNewShift(s => ({ ...s, recurringFrom: e.target.value }))} /></div>
                    <div><Label text="Recurring To (leave blank = ongoing)" /><Input type="date" value={newShift.recurringTo} onChange={e => setNewShift(s => ({ ...s, recurringTo: e.target.value }))} /></div>
                  </div>
                )}
                <div className="flex gap-2">
                  <Btn type="button" variant="primary" disabled={shiftAddMut.isPending} onClick={() => {
                    if (newShift.recurring && !newShift.recurringFrom) { alert('Please set a Recurring From date.'); return }
                    shiftAddMut.mutate(newShift)
                  }}>{shiftAddMut.isPending ? 'Saving…' : 'Add Shift'}</Btn>
                  <Btn type="button" variant="secondary" onClick={() => setShowShiftForm(false)}>Cancel</Btn>
                </div>
              </div>
            )}

            {/* Roster entries */}
            <div className="space-y-2">
              {extraShifts.length === 0 && !showShiftForm && (
                <div className="py-6 text-center text-slate-400">
                  <p className="text-sm">No shifts rostered yet.</p>
                  <p className="text-xs mt-0.5">Click "Add Shift" above to schedule a shift.</p>
                </div>
              )}

              {extraShifts.map((s: any) => {
                const isEditingThis = editExtraShift?.id === s.id
                return (
                  <div key={s.id}>
                    {/* Inline edit form for extra shifts */}
                    {isEditingThis && (
                      <div className="border border-blue-100 bg-blue-50/30 rounded-xl p-4 space-y-3 mb-1">
                        <p className="text-xs font-bold text-blue-700 uppercase tracking-wide">Edit Shift</p>
                        <div className="grid grid-cols-2 gap-3">
                          <div><Label text="Day" /><Select value={editExtraShift.dayIndex} onChange={e => setEditExtraShift({ ...editExtraShift, dayIndex: +e.target.value })}>{DAY_NAMES.map((d, i) => <option key={d} value={i}>{d}</option>)}</Select></div>
                          <div><Label text="Type" /><Select value={editExtraShift.type} onChange={e => setEditExtraShift({ ...editExtraShift, type: e.target.value })}>{['Morning','Afternoon','Night','Community Support','Casual','On-Call'].map(t => <option key={t}>{t}</option>)}</Select></div>
                          <div><Label text="Start Hour" /><Input type="number" min={0} max={23} value={editExtraShift.startH} onChange={e => setEditExtraShift({ ...editExtraShift, startH: +e.target.value })} /></div>
                          <div><Label text="End Hour" /><Input type="number" min={1} max={24} value={editExtraShift.endH} onChange={e => setEditExtraShift({ ...editExtraShift, endH: +e.target.value })} /></div>
                          <div><Label text="Status" /><Select value={editExtraShift.status} onChange={e => setEditExtraShift({ ...editExtraShift, status: e.target.value })}>{SHIFT_STATUSES.map(s => <option key={s}>{s}</option>)}</Select></div>
                          <div className="col-span-2"><Label text="Location" /><Input value={editExtraShift.location} onChange={e => setEditExtraShift({ ...editExtraShift, location: e.target.value })} placeholder="Location or client site" /></div>
                        </div>
                        <label className="flex items-center gap-2 text-xs cursor-pointer select-none">
                          <button type="button" onClick={() => setEditExtraShift((f: any) => ({ ...f, recurring: !f.recurring }))}
                            className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${editExtraShift.recurring ? 'bg-blue-500' : 'bg-slate-200'}`}>
                            <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${editExtraShift.recurring ? 'translate-x-4' : 'translate-x-0'}`} />
                          </button>
                          Recurring weekly
                        </label>
                        {editExtraShift.recurring && (
                          <div className="grid grid-cols-2 gap-3 border border-blue-100 bg-blue-50/40 rounded-lg p-3">
                            <div><Label text="Recurring From *" /><Input type="date" value={editExtraShift.recurringFrom ?? ''} onChange={e => setEditExtraShift((f: any) => ({ ...f, recurringFrom: e.target.value }))} /></div>
                            <div><Label text="Recurring To (leave blank = ongoing)" /><Input type="date" value={editExtraShift.recurringTo ?? ''} onChange={e => setEditExtraShift((f: any) => ({ ...f, recurringTo: e.target.value }))} /></div>
                          </div>
                        )}
                        <div className="flex gap-2">
                          <Btn type="button" variant="primary" disabled={shiftUpdateMut.isPending} onClick={() => {
                            if (editExtraShift.recurring && !editExtraShift.recurringFrom) { alert('Please set a Recurring From date.'); return }
                            shiftUpdateMut.mutate({ id: editExtraShift.id, s: editExtraShift })
                          }}>{shiftUpdateMut.isPending ? 'Saving…' : 'Save'}</Btn>
                          <Btn type="button" variant="secondary" onClick={() => setEditExtraShift(null)}>Cancel</Btn>
                        </div>
                      </div>
                    )}
                    <div className={`flex items-center gap-3 rounded-lg border border-dashed px-4 py-3 ${shiftConflicts.includes(s.id) ? 'border-red-200 bg-red-50/30' : 'border-blue-200 bg-blue-50/20'}`}>
                      <div className={`h-2.5 w-2.5 rounded-full shrink-0 ${s.bg}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-slate-700">{s.type}</span>
                          <span className="text-[10px] text-slate-400">{DAY_NAMES[s.dayIndex]}</span>
                          <span className="text-[10px] text-slate-500">{s.startH}:00 – {s.endH}:00</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${s.status === 'Confirmed' ? 'bg-emerald-100 text-emerald-700' : s.status === 'Cancelled' ? 'bg-slate-100 text-slate-500' : 'bg-amber-100 text-amber-700'}`}>{s.status}</span>
                          {s.recurring && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700">↻ Recurring</span>}
                          {shiftConflicts.includes(s.id) && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 text-red-600">⚠ Conflict</span>}
                        </div>
                        {s.location && <p className="text-xs text-slate-400 mt-0.5 truncate">{s.location}</p>}
                      </div>
                      <div className="flex gap-1 shrink-0">
                        {can('schedules:edit') && (
                          <button onClick={() => setEditExtraShift(isEditingThis ? null : { ...s })} className="p-1.5 rounded hover:bg-slate-100 text-slate-300 hover:text-slate-600" title="Edit"><Pencil className="h-3.5 w-3.5" /></button>
                        )}
                        {can('schedules:delete') && (
                          <button onClick={() => { if (confirm('Delete this shift?')) shiftDeleteMut.mutate(s.id) }} className="p-1.5 rounded hover:bg-red-50 text-slate-300 hover:text-red-400" title="Delete"><Trash2 className="h-3.5 w-3.5" /></button>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Recurring patterns (4.5) */}
          {(() => {
            const recurringShifts = extraShifts.filter((s: any) => s.recurring)
            return (
              <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-3">
                <h3 className="text-sm font-bold text-slate-700">Recurring Roster Patterns</h3>
                {recurringShifts.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center py-3">
                    No recurring patterns yet — add a shift and mark it "Recurring weekly" for it to appear here.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {recurringShifts.map((s: any) => (
                      <div key={s.id} className="flex items-center gap-3 rounded-lg border border-dashed border-indigo-200 bg-indigo-50/20 px-4 py-3">
                        <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 bg-indigo-100 text-base">↻</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-semibold text-slate-700">{s.type} — {DAY_NAMES[s.dayIndex]}s</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">{s.startH}:00 – {s.endH}:00{s.location ? ` · ${s.location}` : ''}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{s.recurringFrom ? `From ${s.recurringFrom}` : ''}{s.recurringTo ? ` → ${s.recurringTo}` : s.recurringFrom ? ' · Ongoing' : ''}</p>
                        </div>
                        {can('schedules:edit') && (
                          <button
                            onClick={() => shiftUpdateMut.mutate({ id: s.id, s: { ...s, recurring: false } })}
                            className="text-xs px-2.5 py-1 rounded-lg font-medium border border-slate-200 text-slate-500 hover:bg-slate-50 transition-colors"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )
          })()}
        </div>
      )}

    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Timesheets Tab
// ══════════════════════════════════════════════════════════════════════════════

const TS_STATUSES = ['Draft', 'Submitted', 'Approved', 'Rejected']

const tsBadge = (s: string) => {
  const map: Record<string, string> = {
    Draft:     'bg-slate-100  text-slate-500',
    Submitted: 'bg-amber-100  text-amber-700',
    Approved:  'bg-emerald-100 text-emerald-700',
    Rejected:  'bg-red-100    text-red-600',
  }
  return map[s] ?? 'bg-slate-100 text-slate-500'
}

function TimesheetsTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const { can } = usePermissions()

  const { data: res, isLoading } = useQuery({
    queryKey: ['staff-timesheets', staffId],
    queryFn: () => getTimesheets(tenantId, staffId),
  })
  const timesheets: any[] = res?.data ?? []

  // Expanded timesheet for viewing lines
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const { data: linesRes } = useQuery({
    queryKey: ['timesheet-lines', expandedId],
    queryFn: () => getTimesheetLines(tenantId, staffId, expandedId!),
    enabled: !!expandedId,
  })
  const lines: any[] = linesRes?.data ?? []

  // New timesheet form
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    work_date: '',
    timesheet_status: 'Draft',
    notes: '',
    total_overtime_hours: '',
  })

  const createMut = useMutation({
    mutationFn: (d: any) => createTimesheet(tenantId, staffId, d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-timesheets', staffId] })
      setShowForm(false)
      setForm({ work_date: '', timesheet_status: 'Draft', notes: '', total_overtime_hours: '' })
    },
  })

  // Approve / reject / submit
  const approveMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateTimesheet(tenantId, staffId, id, { timesheet_status: status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-timesheets', staffId] }),
  })

  // Edit timesheet (Draft only)
  const [editTs, setEditTs] = useState<any>(null)
  const editMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      updateTimesheet(tenantId, staffId, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-timesheets', staffId] })
      setEditTs(null)
    },
  })

  // Delete timesheet
  const deleteTsMut = useMutation({
    mutationFn: (id: string) => deleteTimesheet(tenantId, staffId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-timesheets', staffId] }),
  })

  // New line form
  // The backend's optional time/int fields (scheduled/actual times,
  // break_duration_minutes) are typed time/int and reject an empty string
  // "" — only omission or null is valid "blank". Every field here starts
  // as '', so a blank one must be stripped before sending or the request
  // 422s. There was previously no onError handler either, so a failed
  // save looked like nothing happened at all — fixed below.
  const [lineForm, setLineForm] = useState<any>(null)
  const cleanTimesheetLine = (obj: Record<string, any>) => {
    const out: Record<string, any> = {}
    for (const [k, v] of Object.entries(obj)) {
      if (v === '') continue
      out[k] = k === 'break_duration_minutes' ? Number(v) : v
    }
    return out
  }
  const addLineMut = useMutation({
    mutationFn: (d: any) => addTimesheetLine(tenantId, staffId, expandedId!, cleanTimesheetLine(d)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timesheet-lines', expandedId] })
      setLineForm(null)
    },
    onError: (err: any) => alert(`Failed to add line: ${getGenericErrorMessage(err)}`),
  })

  const fmt = (dt?: string) => dt ? new Date(dt).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
  const fmtTime = (t?: string) => t?.slice(0, 5) ?? '—'

  const canManage = can('staff:timesheets')

  // Summary counts
  const counts = { Draft: 0, Submitted: 0, Approved: 0, Rejected: 0 }
  timesheets.forEach((t: any) => { if (t.timesheet_status in counts) (counts as any)[t.timesheet_status]++ })

  return (
    <div className="space-y-5">

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Draft',     value: counts.Draft,     color: 'text-slate-600'   },
          { label: 'Submitted', value: counts.Submitted, color: 'text-amber-600'   },
          { label: 'Approved',  value: counts.Approved,  color: 'text-emerald-600' },
          { label: 'Rejected',  value: counts.Rejected,  color: 'text-red-500'     },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-100 p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Timesheet list */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Timesheets</h3>
          {canManage && (
            <Btn variant="ghost" onClick={() => setShowForm(v => !v)} className="text-xs py-1">
              <Plus className="h-3 w-3" /> New Timesheet
            </Btn>
          )}
        </div>

        {/* Add form */}
        {showForm && (
          <form
            onSubmit={e => { e.preventDefault(); createMut.mutate(form) }}
            className="border border-purple-100 bg-purple-50/40 rounded-xl p-4 space-y-3"
          >
            <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">New Timesheet</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label text="Work Date *" />
                <Input type="date" value={form.work_date} onChange={e => setForm({ ...form, work_date: e.target.value })} required />
              </div>
              <div>
                <Label text="Status" />
                <Select value={form.timesheet_status} onChange={e => setForm({ ...form, timesheet_status: e.target.value })}>
                  {TS_STATUSES.map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
              <div>
                <Label text="Overtime Hours" />
                <Input type="number" step="0.25" min="0" value={form.total_overtime_hours} onChange={e => setForm({ ...form, total_overtime_hours: e.target.value })} placeholder="0.00" />
              </div>
              <div>
                <Label text="Notes" />
                <Input value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Optional notes" />
              </div>
            </div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={createMut.isPending}>
                {createMut.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving…</> : 'Create'}
              </Btn>
              <Btn type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Btn>
            </div>
          </form>
        )}

        {/* List */}
        {isLoading ? (
          <div className="py-6 flex items-center justify-center gap-2 text-slate-400 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading timesheets…
          </div>
        ) : timesheets.length === 0 && !showForm ? (
          <div className="py-8 text-center text-slate-400">
            <Clock className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No timesheets yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {timesheets.map((ts: any) => (
              <div key={ts.timesheet_id} className="border border-slate-100 rounded-lg overflow-hidden">
                {/* Inline edit form — Draft only */}
                {editTs?.timesheet_id === ts.timesheet_id && (
                  <form
                    onSubmit={e => { e.preventDefault(); editMut.mutate({ id: ts.timesheet_id, data: { work_date: editTs.work_date, total_overtime_hours: editTs.total_overtime_hours, notes: editTs.notes, timesheet_status: editTs.timesheet_status } }) }}
                    className="border-b border-purple-100 bg-purple-50/40 p-3 space-y-3"
                  >
                    <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Edit Timesheet</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label text="Work Date *" />
                        <Input type="date" value={editTs.work_date?.slice(0,10) ?? ''} onChange={e => setEditTs({ ...editTs, work_date: e.target.value })} required />
                      </div>
                      <div>
                        <Label text="Status" />
                        <Select value={editTs.timesheet_status ?? 'Draft'} onChange={e => setEditTs({ ...editTs, timesheet_status: e.target.value })}>
                          {TS_STATUSES.map(s => <option key={s}>{s}</option>)}
                        </Select>
                      </div>
                      <div>
                        <Label text="Overtime Hours" />
                        <Input type="number" step="0.25" min="0" value={editTs.total_overtime_hours ?? ''} onChange={e => setEditTs({ ...editTs, total_overtime_hours: e.target.value })} placeholder="0.00" />
                      </div>
                      <div>
                        <Label text="Notes" />
                        <Input value={editTs.notes ?? ''} onChange={e => setEditTs({ ...editTs, notes: e.target.value })} placeholder="Optional notes" />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Btn type="submit" variant="primary" disabled={editMut.isPending}>
                        {editMut.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving…</> : 'Save Changes'}
                      </Btn>
                      <Btn type="button" variant="secondary" onClick={() => setEditTs(null)}>Cancel</Btn>
                    </div>
                  </form>
                )}

                {/* Header row */}
                <div className="flex items-center gap-3 p-3">
                  <button
                    onClick={() => setExpandedId(expandedId === ts.timesheet_id ? null : ts.timesheet_id)}
                    className="flex items-center gap-3 flex-1 min-w-0 text-left"
                  >
                    <Clock className="h-4 w-4 text-slate-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700">{fmt(ts.work_date)}</p>
                      <p className="text-xs text-slate-500">
                        {ts.total_overtime_hours ? `${ts.total_overtime_hours}h OT` : 'No overtime'}
                        {ts.notes ? ` · ${ts.notes.slice(0, 40)}` : ''}
                      </p>
                    </div>
                  </button>

                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${tsBadge(ts.timesheet_status)}`}>
                    {ts.timesheet_status}
                  </span>

                  {/* Approve/Reject for submitted timesheets */}
                  {canManage && ts.timesheet_status === 'Submitted' && (
                    <div className="flex gap-1 shrink-0">
                      <button
                        onClick={() => approveMut.mutate({ id: ts.timesheet_id, status: 'Approved' })}
                        className="text-emerald-600 hover:text-emerald-700"
                        title="Approve"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => approveMut.mutate({ id: ts.timesheet_id, status: 'Rejected' })}
                        className="text-red-400 hover:text-red-600"
                        title="Reject"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  )}

                  {/* Submit draft */}
                  {canManage && ts.timesheet_status === 'Draft' && (
                    <Btn
                      variant="secondary"
                      className="text-xs py-1 shrink-0"
                      onClick={() => approveMut.mutate({ id: ts.timesheet_id, status: 'Submitted' })}
                    >
                      Submit
                    </Btn>
                  )}

                  {/* Edit (Draft only) */}
                  {canManage && ts.timesheet_status === 'Draft' && (
                    <button
                      onClick={() => setEditTs(editTs?.timesheet_id === ts.timesheet_id ? null : { ...ts })}
                      className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 shrink-0"
                      title="Edit"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  )}

                  {/* Delete */}
                  {canManage && (
                    <button
                      onClick={() => { if (confirm('Delete this timesheet?')) deleteTsMut.mutate(ts.timesheet_id) }}
                      disabled={deleteTsMut.isPending}
                      className="p-1.5 rounded hover:bg-red-50 text-slate-400 hover:text-red-500 shrink-0"
                      title="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}

                  <button
                    onClick={() => setExpandedId(expandedId === ts.timesheet_id ? null : ts.timesheet_id)}
                    className="text-slate-400"
                  >
                    <ChevronRight className={`h-4 w-4 transition-transform ${expandedId === ts.timesheet_id ? 'rotate-90' : ''}`} />
                  </button>
                </div>

                {/* Expanded: lines */}
                {expandedId === ts.timesheet_id && (
                  <div className="border-t border-slate-100 bg-slate-50/50 p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-slate-600">Shift Lines</p>
                      {canManage && (
                        <Btn variant="ghost" className="text-xs py-0.5" onClick={() => setLineForm({
                          scheduled_start_time: '', scheduled_end_time: '',
                          actual_clock_on_time: '', actual_clock_off_time: '',
                          break_taken: false, break_duration_minutes: '',
                          care_note_submitted: false, line_status: 'Pending',
                        })}>
                          <Plus className="h-3 w-3" /> Add Line
                        </Btn>
                      )}
                    </div>

                    {/* Add line form */}
                    {lineForm && (
                      <form
                        onSubmit={e => { e.preventDefault(); addLineMut.mutate(lineForm) }}
                        className="bg-white border border-slate-200 rounded-lg p-3 space-y-3"
                      >
                        <div className="grid grid-cols-2 gap-2">
                          <div><Label text="Scheduled Start" /><Input type="time" value={lineForm.scheduled_start_time} onChange={e => setLineForm({ ...lineForm, scheduled_start_time: e.target.value })} /></div>
                          <div><Label text="Scheduled End" /><Input type="time" value={lineForm.scheduled_end_time} onChange={e => setLineForm({ ...lineForm, scheduled_end_time: e.target.value })} /></div>
                          <div><Label text="Clock On" /><Input type="time" value={lineForm.actual_clock_on_time} onChange={e => setLineForm({ ...lineForm, actual_clock_on_time: e.target.value })} /></div>
                          <div><Label text="Clock Off" /><Input type="time" value={lineForm.actual_clock_off_time} onChange={e => setLineForm({ ...lineForm, actual_clock_off_time: e.target.value })} /></div>
                          <div><Label text="Break (mins)" /><Input type="number" value={lineForm.break_duration_minutes} onChange={e => setLineForm({ ...lineForm, break_duration_minutes: e.target.value, break_taken: !!e.target.value })} /></div>
                          <div><Label text="Line Status" />
                            <Select value={lineForm.line_status} onChange={e => setLineForm({ ...lineForm, line_status: e.target.value })}>
                              {['Pending','Completed','Cancelled'].map(s => <option key={s}>{s}</option>)}
                            </Select>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Btn type="submit" variant="primary" disabled={addLineMut.isPending}>{addLineMut.isPending ? 'Saving…' : 'Add Line'}</Btn>
                          <Btn type="button" variant="secondary" onClick={() => setLineForm(null)}>Cancel</Btn>
                        </div>
                      </form>
                    )}

                    {/* Lines table */}
                    {lines.length === 0 ? (
                      <p className="text-xs text-slate-400 italic text-center py-2">No shift lines recorded.</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-slate-400 border-b border-slate-100">
                              <th className="text-left pb-1 font-medium">Scheduled</th>
                              <th className="text-left pb-1 font-medium">Actual</th>
                              <th className="text-left pb-1 font-medium">Break</th>
                              <th className="text-left pb-1 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-50">
                            {lines.map((l: any) => (
                              <tr key={l.timesheet_line_id}>
                                <td className="py-1.5">{fmtTime(l.scheduled_start_time)} – {fmtTime(l.scheduled_end_time)}</td>
                                <td className="py-1.5">{fmtTime(l.actual_clock_on_time)} – {fmtTime(l.actual_clock_off_time)}</td>
                                <td className="py-1.5">{l.break_taken ? `${l.break_duration_minutes ?? 0}m` : 'None'}</td>
                                <td className="py-1.5">
                                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${l.line_status === 'Completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                                    {l.line_status ?? '—'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Documents Tab
// ══════════════════════════════════════════════════════════════════════════════

const ALLOWED_DOC_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xlsx', '.xls', '.txt']
const MAX_DOC_SIZE_MB = 10
const DOC_STATUSES = ['Active', 'Pending', 'Expired', 'Rejected', 'Archived']
const docStatusBadge = (s: string) => {
  const map: Record<string, string> = {
    Active:   'bg-emerald-100 text-emerald-700',
    Pending:  'bg-amber-100   text-amber-700',
    Expired:  'bg-red-100     text-red-700',
    Rejected: 'bg-orange-100  text-orange-700',
    Archived: 'bg-slate-100   text-slate-500',
  }
  return map[s] ?? 'bg-slate-100 text-slate-500'
}

function DocumentsTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const { can } = usePermissions()
  const canManageDocs = can('staff:documents')

  const { data: docsRes, isLoading: docsLoading } = useQuery({
    queryKey: ['staff-docs', staffId],
    queryFn: () => getStaffDocuments(tenantId, staffId),
  })
  const docs: any[] = docsRes?.data ?? []

  // ── Search & filter ──────────────────────────────────────────────────────
  const [docSearch, setDocSearch] = useState('')
  const [docTypeFilter, setDocTypeFilter] = useState('')
  const [docStatusFilter, setDocStatusFilter] = useState('')

  const filteredDocs = docs.filter((d: any) => {
    if (docTypeFilter && d.document_type !== docTypeFilter) return false
    if (docStatusFilter && d.document_status !== docStatusFilter) return false
    if (docSearch.trim()) {
      const q = docSearch.trim().toLowerCase()
      const hay = `${d.document_name ?? ''} ${d.document_description ?? ''}`.toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })

  // ── Folder grouping (by document type) ───────────────────────────────────
  const docFolders = useMemo(() => {
    const groups: Record<string, any[]> = {}
    for (const d of filteredDocs) {
      const key = d.document_type || 'Other'
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
  }, [filteredDocs])

  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({})
  const toggleFolder = (key: string) => setCollapsedFolders(prev => ({ ...prev, [key]: !prev[key] }))

  // ── Document history / audit trail ───────────────────────────────────────
  // Document audit entries are keyed by document_id (not staff_id), since
  // that's the record being changed — so we can't filter server-side by
  // staff. Instead we fetch recent entries for this table and keep only the
  // ones whose old/new values say they belong to this staff member.
  const [showDocHistory, setShowDocHistory] = useState(false)
  const { data: docAuditRes, isLoading: docAuditLoading } = useQuery({
    queryKey: ['staff-doc-audit', staffId],
    queryFn: () => getAuditLogs(tenantId, { table_name: 'staff_document_repository', limit: 200 }),
    enabled: showDocHistory,
  })
  const parseJson = (s?: string | null) => { if (!s) return null; try { return JSON.parse(s) } catch { return null } }
  const docAuditLogs: any[] = ((docAuditRes as any)?.data ?? [])
    .map((log: any) => ({ ...log, _old: parseJson(log.old_values), _new: parseJson(log.new_values) }))
    .filter((log: any) => log._new?.staff_id === staffId || log._old?.staff_id === staffId)

  // Turns a changed field into a plain-English sentence in the form
  // "<Field> <old value> changed to <new value>", so a non-technical user
  // can read exactly what happened at a glance — e.g.
  // "Document name ABC changed to ABCDE" rather than a raw field/value diff.
  const fmtDocDate = (v: any) => {
    if (!v) return null
    const d = new Date(v)
    return isNaN(d.getTime()) ? String(v) : d.toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })
  }
  const DOC_FIELD_NAMES: Record<string, string> = {
    document_name: 'Document name',
    document_type: 'Document type',
    document_status: 'Status',
    document_description: 'Description',
    expiry_date: 'Expiry date',
    file_format: 'File',
  }
  const describeDocChange = (key: string, oldVal: any, newVal: any): string => {
    const label = DOC_FIELD_NAMES[key] ?? key.replace(/_/g, ' ')

    if (key === 'expiry_date') {
      const o = fmtDocDate(oldVal), n = fmtDocDate(newVal)
      if (!n) return `${label} removed`
      return o ? `${label} ${o} changed to ${n}` : `${label} set to ${n}`
    }
    if (key === 'file_format') {
      return oldVal ? `${label} replaced — was .${oldVal}, now .${newVal}` : `${label} attached — .${newVal}`
    }
    if (key === 'document_description') {
      return oldVal ? `${label} updated` : `${label} added`
    }
    return oldVal ? `${label} ${oldVal} changed to ${newVal}` : `${label} set to ${newVal}`
  }

  const [form, setForm] = useState<null | {
    document_type: string
    document_other: string
    document_name: string
    document_description: string
    document_status: string
    expiry_date: string
  }>(null)

  // Selected File object (from file input)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string>('')
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 4000)
  }

  const addMut = useMutation({
    mutationFn: (d: any) => uploadStaffDocument(tenantId, staffId, d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-docs', staffId] })
      qc.invalidateQueries({ queryKey: ['staff-doc-audit', staffId] })
      setForm(null)
      setSelectedFile(null)
      setFileError('')
      setFormErrors({})
      showToast('success', 'Document uploaded successfully.')
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        'Failed to upload document. Please try again.'
      showToast('error', msg)
    },
  })

  const delMut = useMutation({
    mutationFn: (id: string) => deleteStaffDocument(tenantId, staffId, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-docs', staffId] })
      qc.invalidateQueries({ queryKey: ['staff-doc-audit', staffId] })
      showToast('success', 'Document removed.')
    },
    onError: () => showToast('error', 'Failed to remove document.'),
  })

  // ── Edit document ──────────────────────────────────────────────────────────
  const [editDoc, setEditDoc] = useState<any>(null)
  const [editForm, setEditForm] = useState<null | {
    document_type: string
    document_other: string
    document_name: string
    document_description: string
    document_status: string
    expiry_date: string
  }>(null)
  const [editSelectedFile, setEditSelectedFile] = useState<File | null>(null)
  const [editFileError, setEditFileError] = useState<string>('')
  const [editFormErrors, setEditFormErrors] = useState<Record<string, string>>({})

  const editMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateStaffDocument(tenantId, staffId, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff-docs', staffId] })
      qc.invalidateQueries({ queryKey: ['staff-doc-audit', staffId] })
      closeEditForm()
      showToast('success', 'Document updated successfully.')
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        'Failed to update document. Please try again.'
      showToast('error', msg)
    },
  })

  const DOC_TYPES = ['ID Document', 'Qualification', 'Certification', 'Contract', 'Insurance', 'Medical', 'Other']

  const validateFile = (file: File): string => {
    const ext = '.' + (file.name.split('.').pop() ?? '').toLowerCase()
    if (!ALLOWED_DOC_EXTENSIONS.includes(ext)) {
      return `File type '${ext}' is not allowed. Accepted: ${ALLOWED_DOC_EXTENSIONS.join(', ')}`
    }
    if (file.size > MAX_DOC_SIZE_MB * 1024 * 1024) {
      return `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum is ${MAX_DOC_SIZE_MB} MB.`
    }
    if (file.size === 0) return 'File is empty.'
    return ''
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)
    if (file) {
      setFileError(validateFile(file))
    } else {
      setFileError('')
    }
    // reset input so the same file can be re-selected if needed
    e.target.value = ''
  }

  const validateForm = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form) return false
    const finalType = form.document_type === 'Other' ? form.document_other.trim() : form.document_type
    if (!finalType) errs.document_type = 'Document Type is required.'
    if (!form.document_name.trim()) errs.document_name = 'Document Name is required.'
    if (!selectedFile) errs.file = 'Please select a file to upload.'
    else {
      const fErr = validateFile(selectedFile)
      if (fErr) errs.file = fErr
    }
    if (form.expiry_date) {
      const d = new Date(form.expiry_date)
      if (isNaN(d.getTime())) errs.expiry_date = 'Invalid date.'
    }
    setFormErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form || addMut.isPending) return
    if (!validateForm()) return

    const finalType = form.document_type === 'Other' ? (form.document_other.trim() || 'Other') : form.document_type
    addMut.mutate({
      file: selectedFile!,
      document_type: finalType,
      document_name: form.document_name.trim(),
      document_description: form.document_description.trim() || undefined,
      document_status: form.document_status,
      expiry_date: form.expiry_date || undefined,
    })
  }

  const openForm = () => {
    closeEditForm()
    setForm({ document_type: '', document_other: '', document_name: '', document_description: '', document_status: 'Active', expiry_date: '' })
    setSelectedFile(null)
    setFileError('')
    setFormErrors({})
  }

  const cancelForm = () => {
    setForm(null)
    setSelectedFile(null)
    setFileError('')
    setFormErrors({})
  }

  // ── Edit document helpers ────────────────────────────────────────────────
  const openEditForm = (doc: any) => {
    cancelForm()
    const isKnownType = DOC_TYPES.includes(doc.document_type)
    setEditDoc(doc)
    setEditForm({
      document_type: isKnownType ? doc.document_type : 'Other',
      document_other: isKnownType ? '' : (doc.document_type ?? ''),
      document_name: doc.document_name ?? '',
      document_description: doc.document_description ?? '',
      document_status: doc.document_status ?? 'Active',
      expiry_date: doc.expiry_date ? doc.expiry_date.slice(0, 10) : '',
    })
    setEditSelectedFile(null)
    setEditFileError('')
    setEditFormErrors({})
  }

  const closeEditForm = () => {
    setEditDoc(null)
    setEditForm(null)
    setEditSelectedFile(null)
    setEditFileError('')
    setEditFormErrors({})
  }

  const handleEditFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setEditSelectedFile(file)
    setEditFileError(file ? validateFile(file) : '')
    e.target.value = ''
  }

  const validateEditForm = (): boolean => {
    const errs: Record<string, string> = {}
    if (!editForm) return false
    const finalType = editForm.document_type === 'Other' ? editForm.document_other.trim() : editForm.document_type
    if (!finalType) errs.document_type = 'Document Type is required.'
    if (!editForm.document_name.trim()) errs.document_name = 'Document Name is required.'
    if (editSelectedFile) {
      const fErr = validateFile(editSelectedFile)
      if (fErr) errs.file = fErr
    }
    if (editForm.expiry_date) {
      const d = new Date(editForm.expiry_date)
      if (isNaN(d.getTime())) errs.expiry_date = 'Invalid date.'
    }
    setEditFormErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!editForm || !editDoc || editMut.isPending) return
    if (!validateEditForm()) return
    const finalType = editForm.document_type === 'Other' ? (editForm.document_other.trim() || 'Other') : editForm.document_type
    editMut.mutate({
      id: editDoc.document_id,
      data: {
        file: editSelectedFile ?? undefined,
        document_type: finalType,
        document_name: editForm.document_name.trim(),
        document_description: editForm.document_description.trim(),
        document_status: editForm.document_status,
        expiry_date: editForm.expiry_date || null,
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
            toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
          }`}
        >
          {toast.type === 'success'
            ? <CheckCircle className="h-4 w-4 shrink-0" />
            : <AlertCircle className="h-4 w-4 shrink-0" />}
          {toast.message}
        </div>
      )}

      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Documents</h3>
          {canManageDocs && !form && (
            <Btn variant="ghost" onClick={openForm} className="text-xs py-1">
              <Plus className="h-3 w-3" /> Add Document
            </Btn>
          )}
        </div>

        {/* Search & Filter */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-50 rounded-lg p-2.5">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="h-3.5 w-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              value={docSearch}
              onChange={e => setDocSearch(e.target.value)}
              placeholder="Search documents by name or description…"
              className="w-full border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
            />
          </div>
          <Select value={docTypeFilter} onChange={e => setDocTypeFilter(e.target.value)} className="!w-auto text-xs py-1.5">
            <option value="">All Types</option>
            {DOC_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </Select>
          <Select value={docStatusFilter} onChange={e => setDocStatusFilter(e.target.value)} className="!w-auto text-xs py-1.5">
            <option value="">All Statuses</option>
            {DOC_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
          {(docSearch || docTypeFilter || docStatusFilter) && (
            <button
              onClick={() => { setDocSearch(''); setDocTypeFilter(''); setDocStatusFilter('') }}
              className="text-xs text-purple-600 hover:text-purple-800 font-medium px-1"
            >
              Clear
            </button>
          )}
          <span className="text-xs text-slate-400 ml-auto shrink-0">{filteredDocs.length} of {docs.length} document{docs.length === 1 ? '' : 's'}</span>
        </div>

        {/* Add Document Form */}
        {form && (
          <form
            onSubmit={handleSubmit}
            className="border border-slate-100 rounded-lg p-4 space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              {/* Document Type */}
              <div>
                <Label text="Document Type *" />
                <Select
                  value={form.document_type}
                  onChange={e => setForm({ ...form, document_type: e.target.value, document_other: '' })}
                >
                  <option value="">Select type…</option>
                  {DOC_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </Select>
                {formErrors.document_type && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.document_type}</p>
                )}
              </div>

              {/* Document Name */}
              <div>
                <Label text="Document Name *" />
                <Input
                  value={form.document_name}
                  onChange={e => setForm({ ...form, document_name: e.target.value })}
                  placeholder="e.g. Passport, NDIS Worker Screening"
                />
                {formErrors.document_name && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.document_name}</p>
                )}
              </div>

              {/* Custom type when 'Other' */}
              {form.document_type === 'Other' && (
                <div className="col-span-2">
                  <Label text="Please specify type *" />
                  <Input
                    value={form.document_other}
                    onChange={e => setForm({ ...form, document_other: e.target.value })}
                    placeholder="e.g. Work Permit, NDIS Worker Screening…"
                  />
                </div>
              )}

              {/* Expiry Date */}
              <div>
                <Label text="Expiry Date" />
                <Input
                  type="date"
                  value={form.expiry_date}
                  onChange={e => setForm({ ...form, expiry_date: e.target.value })}
                />
                {formErrors.expiry_date && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.expiry_date}</p>
                )}
              </div>

              {/* Status */}
              <div>
                <Label text="Status" />
                <Select
                  value={form.document_status}
                  onChange={e => setForm({ ...form, document_status: e.target.value })}
                >
                  {DOC_STATUSES.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </Select>
              </div>

              {/* Description */}
              <div className="col-span-2">
                <Label text="Description" />
                <Textarea
                  value={form.document_description}
                  onChange={e => setForm({ ...form, document_description: e.target.value })}
                  placeholder="Optional notes about this document…"
                />
              </div>

              {/* File Upload */}
              <div className="col-span-2">
                <Label text="Upload File *" />
                <label
                  htmlFor="doc-file-input"
                  className={`flex flex-col items-center justify-center w-full border-2 border-dashed rounded-lg p-6 cursor-pointer transition-colors ${
                    fileError || formErrors.file
                      ? 'border-red-300 bg-red-50 hover:bg-red-50'
                      : selectedFile
                      ? 'border-emerald-300 bg-emerald-50 hover:bg-emerald-50'
                      : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                  }`}
                >
                  <input
                    id="doc-file-input"
                    type="file"
                    className="hidden"
                    accept={ALLOWED_DOC_EXTENSIONS.join(',')}
                    onChange={handleFileChange}
                  />
                  {selectedFile ? (
                    <div className="text-center">
                      <FileText className="h-6 w-6 text-emerald-500 mx-auto mb-1" />
                      <p className="text-sm font-medium text-emerald-700 truncate max-w-xs">{selectedFile.name}</p>
                      <p className="text-xs text-emerald-500">{(selectedFile.size / 1024).toFixed(1)} KB — click to change</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <Upload className="h-6 w-6 text-slate-400 mx-auto mb-2" />
                      <p className="text-sm text-slate-600 font-medium">Click to select a file</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {ALLOWED_DOC_EXTENSIONS.join(', ')} · Max {MAX_DOC_SIZE_MB} MB
                      </p>
                    </div>
                  )}
                </label>
                {(fileError || formErrors.file) && (
                  <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{fileError || formErrors.file}
                  </p>
                )}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-2 pt-1">
              <Btn
                type="submit"
                variant="primary"
                disabled={addMut.isPending}
                id="doc-submit-btn"
              >
                {addMut.isPending
                  ? <><Loader2 className="h-3 w-3 animate-spin" /> Saving…</>
                  : <><CheckCircle className="h-3 w-3" /> Save</>}
              </Btn>
              <Btn type="button" variant="secondary" onClick={cancelForm} disabled={addMut.isPending}>
                Cancel
              </Btn>
            </div>

            {/* Submission error summary */}
            {Object.keys(formErrors).length > 0 && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                <p className="text-xs font-semibold text-red-700 mb-1">Please fix the following:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {Object.values(formErrors).map((msg, i) => (
                    <li key={i} className="text-xs text-red-600">{msg}</li>
                  ))}
                </ul>
              </div>
            )}
          </form>
        )}

        {/* Document List — grouped into folders by document type */}
        <div className="space-y-3">
          {docsLoading && (
            <div className="flex items-center gap-2 py-4 text-slate-400 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading documents…
            </div>
          )}
          {!docsLoading && docs.length === 0 && !form && (
            <p className="text-sm text-slate-400 italic py-2">No documents uploaded.</p>
          )}
          {!docsLoading && docs.length > 0 && filteredDocs.length === 0 && (
            <p className="text-sm text-slate-400 italic py-2">No documents match your search / filters.</p>
          )}
          {docFolders.map(([folderName, folderDocs]) => {
            const isCollapsed = !!collapsedFolders[folderName]
            return (
              <div key={folderName} className="border border-slate-100 rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleFolder(folderName)}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
                >
                  {isCollapsed ? <ChevronRight className="h-3.5 w-3.5 text-slate-400" /> : <ChevronDown className="h-3.5 w-3.5 text-slate-400" />}
                  <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">{folderName}</span>
                  <span className="text-[10px] text-slate-400">({folderDocs.length})</span>
                </button>
                {!isCollapsed && (
                  <div className="divide-y divide-slate-50 px-3">
                    {folderDocs.map((doc: any) => {
            const expired = doc.expiry_date && new Date(doc.expiry_date) < new Date()
            const viewUrl = doc.file_url
              ? (doc.file_url.startsWith('http') ? doc.file_url : doc.file_url)
              : null
            const isEditingThis = editDoc?.document_id === doc.document_id
            return (
              <div key={doc.document_id}>
                {/* Inline edit form */}
                {isEditingThis && editForm && (
                  <form
                    onSubmit={handleEditSubmit}
                    className="border border-purple-100 bg-purple-50/40 rounded-lg p-4 space-y-4 my-2"
                  >
                    <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Edit Document</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label text="Document Type *" />
                        <Select
                          value={editForm.document_type}
                          onChange={e => setEditForm({ ...editForm, document_type: e.target.value, document_other: '' })}
                        >
                          <option value="">Select type…</option>
                          {DOC_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                        </Select>
                        {editFormErrors.document_type && (
                          <p className="text-xs text-red-500 mt-1">{editFormErrors.document_type}</p>
                        )}
                      </div>
                      <div>
                        <Label text="Document Name *" />
                        <Input
                          value={editForm.document_name}
                          onChange={e => setEditForm({ ...editForm, document_name: e.target.value })}
                          placeholder="e.g. Passport, NDIS Worker Screening"
                        />
                        {editFormErrors.document_name && (
                          <p className="text-xs text-red-500 mt-1">{editFormErrors.document_name}</p>
                        )}
                      </div>
                      {editForm.document_type === 'Other' && (
                        <div className="col-span-2">
                          <Label text="Please specify type *" />
                          <Input
                            value={editForm.document_other}
                            onChange={e => setEditForm({ ...editForm, document_other: e.target.value })}
                            placeholder="e.g. Work Permit, NDIS Worker Screening…"
                          />
                        </div>
                      )}
                      <div>
                        <Label text="Expiry Date" />
                        <Input
                          type="date"
                          value={editForm.expiry_date}
                          onChange={e => setEditForm({ ...editForm, expiry_date: e.target.value })}
                        />
                        {editFormErrors.expiry_date && (
                          <p className="text-xs text-red-500 mt-1">{editFormErrors.expiry_date}</p>
                        )}
                      </div>
                      <div>
                        <Label text="Status" />
                        <Select
                          value={editForm.document_status}
                          onChange={e => setEditForm({ ...editForm, document_status: e.target.value })}
                        >
                          {DOC_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                        </Select>
                      </div>
                      <div className="col-span-2">
                        <Label text="Description" />
                        <Textarea
                          value={editForm.document_description}
                          onChange={e => setEditForm({ ...editForm, document_description: e.target.value })}
                          placeholder="Optional notes about this document…"
                        />
                      </div>
                      <div className="col-span-2">
                        <Label text="Replace File (optional)" />
                        <label
                          htmlFor="edit-doc-file-input"
                          className={`flex flex-col items-center justify-center w-full border-2 border-dashed rounded-lg p-4 cursor-pointer transition-colors ${
                            editFileError || editFormErrors.file
                              ? 'border-red-300 bg-red-50 hover:bg-red-50'
                              : editSelectedFile
                              ? 'border-emerald-300 bg-emerald-50 hover:bg-emerald-50'
                              : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                          }`}
                        >
                          <input
                            id="edit-doc-file-input"
                            type="file"
                            className="hidden"
                            accept={ALLOWED_DOC_EXTENSIONS.join(',')}
                            onChange={handleEditFileChange}
                          />
                          {editSelectedFile ? (
                            <div className="text-center">
                              <FileText className="h-5 w-5 text-emerald-500 mx-auto mb-1" />
                              <p className="text-xs font-medium text-emerald-700 truncate max-w-xs">{editSelectedFile.name}</p>
                              <p className="text-[10px] text-emerald-500">{(editSelectedFile.size / 1024).toFixed(1)} KB — click to change</p>
                            </div>
                          ) : (
                            <div className="text-center">
                              <Upload className="h-5 w-5 text-slate-400 mx-auto mb-1" />
                              <p className="text-xs text-slate-600 font-medium">Click to replace the file</p>
                              <p className="text-[10px] text-slate-400 mt-0.5">Leave empty to keep the current file</p>
                            </div>
                          )}
                        </label>
                        {(editFileError || editFormErrors.file) && (
                          <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />{editFileError || editFormErrors.file}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 pt-1">
                      <Btn type="submit" variant="primary" disabled={editMut.isPending}>
                        {editMut.isPending
                          ? <><Loader2 className="h-3 w-3 animate-spin" /> Saving…</>
                          : <><CheckCircle className="h-3 w-3" /> Save Changes</>}
                      </Btn>
                      <Btn type="button" variant="secondary" onClick={closeEditForm} disabled={editMut.isPending}>
                        Cancel
                      </Btn>
                    </div>
                    {Object.keys(editFormErrors).length > 0 && (
                      <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                        <p className="text-xs font-semibold text-red-700 mb-1">Please fix the following:</p>
                        <ul className="list-disc list-inside space-y-0.5">
                          {Object.values(editFormErrors).map((msg, i) => (
                            <li key={i} className="text-xs text-red-600">{msg}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </form>
                )}

                <div className="py-3 flex items-center gap-3">
                  <FileText className="h-4 w-4 text-purple-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700 truncate">{doc.document_name}</p>
                    <p className="text-xs text-slate-500">
                      {doc.document_type}
                      {doc.file_format ? ` · ${doc.file_format.toUpperCase()}` : ''}
                      {doc.expiry_date ? ` · Expires ${doc.expiry_date?.slice(0, 10)}` : ''}
                      {doc.document_description ? ` · ${doc.document_description}` : ''}
                    </p>
                  </div>
                  {expired && (
                    <span className="flex items-center gap-0.5 text-[10px] text-red-500 font-medium">
                      <AlertCircle className="h-3 w-3" /> Expired
                    </span>
                  )}
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${docStatusBadge(doc.document_status)}`}>
                    {doc.document_status}
                  </span>
                  {viewUrl && (
                    <a
                      href={viewUrl}
                      target="_blank"
                      rel="noreferrer"
                      title="View / Download document"
                      className="text-slate-400 hover:text-purple-600 transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </a>
                  )}
                  {canManageDocs && (
                    <button
                      onClick={() => (isEditingThis ? closeEditForm() : openEditForm(doc))}
                      title="Edit document"
                      className="text-slate-300 hover:text-purple-500 transition-colors"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  )}
                  {canManageDocs && (
                    <button
                      onClick={() => delMut.mutate(doc.document_id)}
                      disabled={delMut.isPending}
                      title="Delete document"
                      className="text-slate-300 hover:text-red-400 disabled:opacity-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Document History / Audit Trail */}
        <div className="border-t border-slate-100 pt-3">
          <button
            type="button"
            onClick={() => setShowDocHistory(s => !s)}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-purple-600 transition-colors"
          >
            {showDocHistory ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            Document History / Audit Trail
          </button>
          {showDocHistory && (
            <div className="mt-2 space-y-2">
              {docAuditLoading ? (
                <div className="flex items-center gap-2 py-3 text-slate-400 text-xs">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading history…
                </div>
              ) : docAuditLogs.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-2">No document activity recorded yet.</p>
              ) : (
                docAuditLogs.map((log: any, idx: number) => {
                  // Which fields actually changed, for UPDATE entries —
                  // compare old vs new and skip the staff_id bookkeeping key.
                  const changedKeys = Object.keys(log._new ?? {}).filter(
                    k => k !== 'staff_id' && log._new?.[k] !== log._old?.[k]
                  )
                  const docLabel = log._new?.document_name ?? log._old?.document_name
                  return (
                    <div key={log.audit_id ?? idx} className="bg-slate-50 rounded-lg px-3 py-2 space-y-1.5">
                      <div className="flex items-start gap-2 text-xs">
                        <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide ${
                          log.action === 'CREATE' ? 'bg-emerald-100 text-emerald-700' :
                          log.action === 'DELETE' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {log.action}
                        </span>
                        {docLabel && <span className="font-medium text-slate-700 truncate">{docLabel}</span>}
                        <span className="flex-1 min-w-0 text-slate-500">
                          by <span className="font-medium text-slate-700">{log.username ?? log.user_id ?? 'System'}</span>
                        </span>
                        <span className="shrink-0 text-slate-400">
                          {new Date(log.created_at).toLocaleString('en-AU', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      {log.action === 'UPDATE' && changedKeys.length > 0 && (
                        <ul className="pl-1 space-y-0.5 list-disc list-inside">
                          {changedKeys.map(k => (
                            <li key={k} className="text-xs text-slate-600">
                              {describeDocChange(k, log._old?.[k], log._new?.[k])}
                            </li>
                          ))}
                        </ul>
                      )}
                      {log.action === 'UPDATE' && changedKeys.length === 0 && (
                        <p className="pl-1 text-xs text-slate-400 italic">No field changes recorded for this update.</p>
                      )}
                      {log.action === 'CREATE' && (
                        <p className="pl-1 text-xs text-slate-500">Document uploaded.</p>
                      )}
                      {log.action === 'DELETE' && (
                        <p className="pl-1 text-xs text-slate-500">Document removed.</p>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}


// ══════════════════════════════════════════════════════════════════════════════
// Activity Tab
// ══════════════════════════════════════════════════════════════════════════════

const ACTION_COLOURS: Record<string, string> = {
  CREATE: 'bg-emerald-100 text-emerald-700',
  UPDATE: 'bg-blue-100   text-blue-700',
  UPSERT: 'bg-blue-100   text-blue-700',
  DELETE: 'bg-red-100    text-red-600',
}

const TABLE_LABELS: Record<string, string> = {
  staff_profile:            'Profile',
  staff_personal_info:      'Personal Info',
  staff_contact_info:       'Contact Info',
  staff_identification:     'Identification',
  staff_preferences:        'Preferences',
  staff_emergency_contact:  'Emergency Contact',
  employment_information:   'Employment',
  staff_probation:          'Probation',
  staff_contract:           'Contract',
  staff_roles:              'Job Role',
  staff_exit_process:       'Exit Process',
  staff_qualification:      'Qualification',
  staff_certification:      'Certification',
  staff_availability:       'Availability',
  staff_timesheet_header:   'Timesheet',
  staff_timesheet_line:     'Timesheet Line',
  staff_leave_request:      'Leave Request',
  staff_document_repository:'Document',
}

function ActivityTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const [actionFilter, setActionFilter] = useState('')
  const [tableFilter, setTableFilter]   = useState('')
  const [limit, setLimit]               = useState(50)

  const { data: res, isLoading, isFetching } = useQuery({
    queryKey: ['staff-activity', staffId, actionFilter, tableFilter, limit],
    queryFn: () =>
      getAuditLogs(tenantId, {
        record_id:  staffId,
        ...(actionFilter ? { action: actionFilter }     : {}),
        ...(tableFilter  ? { table_name: tableFilter }  : {}),
        limit,
      }),
  })

  const logs: any[] = (res as any)?.data ?? []

  const fmtDate = (dt: string) =>
    new Date(dt).toLocaleString('en-AU', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })

  const parseJson = (s?: string | null) => {
    if (!s) return null
    try { return JSON.parse(s) } catch { return null }
  }

  return (
    <div className="space-y-4">

      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-slate-100 p-4 flex flex-wrap gap-3 items-center">
        <Filter className="h-4 w-4 text-slate-400 shrink-0" />

        <Select
          value={actionFilter}
          onChange={e => setActionFilter(e.target.value)}
          className="w-36 py-1.5 text-xs"
        >
          <option value="">All Actions</option>
          {['CREATE', 'UPDATE', 'UPSERT', 'DELETE'].map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </Select>

        <Select
          value={tableFilter}
          onChange={e => setTableFilter(e.target.value)}
          className="w-44 py-1.5 text-xs"
        >
          <option value="">All Sections</option>
          {Object.entries(TABLE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </Select>

        <span className="text-xs text-slate-400 ml-auto">
          {isFetching && !isLoading ? 'Refreshing…' : `${logs.length} entries`}
        </span>
      </div>

      {/* Timeline */}
      <section className="bg-white rounded-xl border border-slate-100 p-5">
        {isLoading ? (
          <div className="py-10 flex items-center justify-center gap-2 text-slate-400 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading activity…
          </div>
        ) : logs.length === 0 ? (
          <div className="py-10 text-center text-slate-400">
            <Activity className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No activity recorded yet.</p>
          </div>
        ) : (
          <div className="relative">
            {/* vertical line */}
            <div className="absolute left-3.5 top-0 bottom-0 w-px bg-slate-100" />

            <ul className="space-y-4">
              {logs.map((log: any, idx: number) => {
                const oldVals  = parseJson(log.old_values)
                const newVals  = parseJson(log.new_values)
                const section  = TABLE_LABELS[log.table_name] ?? log.table_name
                const actionCls = ACTION_COLOURS[log.action] ?? 'bg-slate-100 text-slate-600'

                return (
                  <li key={log.audit_id ?? idx} className="relative pl-10">
                    {/* dot */}
                    <div className={`absolute left-1 top-1 h-5 w-5 rounded-full flex items-center justify-center ${
                      log.action === 'CREATE' ? 'bg-emerald-100' :
                      log.action === 'DELETE' ? 'bg-red-100'     : 'bg-blue-100'
                    }`}>
                      <div className={`h-2 w-2 rounded-full ${
                        log.action === 'CREATE' ? 'bg-emerald-500' :
                        log.action === 'DELETE' ? 'bg-red-400'     : 'bg-blue-500'
                      }`} />
                    </div>

                    <div className="bg-slate-50 rounded-lg p-3 space-y-1.5">
                      {/* header row */}
                      <div className="flex items-start gap-2 flex-wrap">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide ${actionCls}`}>
                          {log.action}
                        </span>
                        <span className="text-xs font-semibold text-slate-700">{section}</span>
                        <span className="text-xs text-slate-400 ml-auto shrink-0">{fmtDate(log.created_at)}</span>
                      </div>

                      {/* who */}
                      <p className="text-xs text-slate-500">
                        By{' '}
                        <span className="font-medium text-slate-700">
                          {log.username ?? log.user_id ?? 'System'}
                        </span>
                      </p>

                      {/* changed fields */}
                      {newVals && Object.keys(newVals).length > 0 && (
                        <div className="mt-1.5 space-y-1">
                          {Object.entries(newVals).map(([k, nv]: [string, any]) => {
                            const ov = oldVals?.[k]
                            const label = k.replace(/_/g, ' ')
                            return (
                              <div key={k} className="text-xs flex items-start gap-1.5">
                                <span className="text-slate-400 capitalize min-w-0 shrink-0">{label}:</span>
                                {ov !== undefined && ov !== nv ? (
                                  <span className="min-w-0">
                                    <span className="line-through text-red-400">{String(ov)}</span>
                                    {' → '}
                                    <span className="text-emerald-600 font-medium">{String(nv)}</span>
                                  </span>
                                ) : (
                                  <span className="font-medium text-slate-700 truncate">{String(nv)}</span>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>

            {/* Load more */}
            {logs.length === limit && (
              <div className="mt-5 text-center">
                <Btn variant="secondary" onClick={() => setLimit(l => l + 50)} className="text-xs">
                  Load more
                </Btn>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Performance Tab
// ══════════════════════════════════════════════════════════════════════════════

function PerformanceTab({ tenantId, staffId }: { tenantId: number; staffId: string }) {
  const qc = useQueryClient()
  const { can } = usePermissions()

  const { data: reviewsRes, isLoading: rvLoading } = useQuery({
    queryKey: ['staff-perf-reviews', staffId],
    queryFn:  () => getPerformanceReviews(tenantId, staffId).then(r => r.data ?? []),
  })
  const reviews: any[] = reviewsRes ?? []

  const { data: kpisRes } = useQuery({
    queryKey: ['staff-kpis', staffId],
    queryFn:  () => getKpis(tenantId, staffId).then(r => r.data ?? []),
  })
  const kpis: any[] = kpisRes ?? []

  const { data: goalsRes } = useQuery({
    queryKey: ['staff-goals', staffId],
    queryFn:  () => getGoals(tenantId, staffId).then(r => r.data ?? []),
  })
  const goals: any[] = goalsRes ?? []

  // The backend's optional score/target/date fields are typed Decimal/date —
  // they reject an empty string "" (only omission or null is valid "blank").
  // Every form here starts those fields as '', so a blank optional field
  // must be stripped before sending, or the request 422s silently.
  const cleanPayload = (obj: Record<string, any>) => {
    const out: Record<string, any> = {}
    for (const [k, v] of Object.entries(obj)) {
      if (v === '') continue
      out[k] = v
    }
    return out
  }

  // ── Review form ──
  const emptyReview = { review_period: '', review_type: 'Quarterly', review_date: '', reviewed_by: '', overall_score: '', punctuality_score: '', care_quality_score: '', compliance_score: '', communication_score: '', teamwork_score: '', reviewer_comments: '', review_status: 'Draft' }
  const [rvForm, setRvForm] = useState<any>(null)
  const rvMut = useMutation({
    mutationFn: (d: any) => createPerformanceReview(tenantId, staffId, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-perf-reviews', staffId] }); setRvForm(null) },
    onError: (err: any) => alert(`Failed to save review: ${getGenericErrorMessage(err)}`),
  })
  // Edit — the update endpoint only accepts these fields (not review_period /
  // review_type, which are set once at creation), so the edit form only
  // exposes what can actually be changed.
  const [editReview, setEditReview] = useState<any>(null)
  const rvUpdateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: any }) => updatePerformanceReview(tenantId, staffId, id, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-perf-reviews', staffId] }); setEditReview(null) },
    onError: (err: any) => alert(`Failed to update review: ${getGenericErrorMessage(err)}`),
  })

  // ── Goal form ──
  const emptyGoal = { goal_title: '', goal_category: 'Development', goal_period: '', due_date: '', goal_status: 'Not Started', notes: '' }
  const [goalForm, setGoalForm]     = useState<any>(null)
  const [editGoal, setEditGoal]     = useState<any>(null)
  const goalMut = useMutation({
    mutationFn: (d: any) => createGoal(tenantId, staffId, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-goals', staffId] }); setGoalForm(null) },
    onError: (err: any) => alert(`Failed to add goal: ${getGenericErrorMessage(err)}`),
  })
  const goalUpdateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: any }) => updateGoal(tenantId, staffId, id, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-goals', staffId] }); setEditGoal(null) },
    onError: (err: any) => alert(`Failed to update goal: ${getGenericErrorMessage(err)}`),
  })

  // ── KPI form ──
  const emptyKpi = { kpi_name: '', kpi_category: '', period: '', target_value: '', actual_value: '', score: '', weight_percent: '', notes: '' }
  const [kpiForm, setKpiForm] = useState<any>(null)
  const kpiMut = useMutation({
    mutationFn: (d: any) => createKpi(tenantId, staffId, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-kpis', staffId] }); setKpiForm(null) },
    onError: (err: any) => alert(`Failed to add KPI: ${getGenericErrorMessage(err)}`),
  })
  // Edit — the update endpoint only accepts actual_value / score / notes
  // (kpi_name, category, period, target and weight are fixed at creation —
  // they define what's being measured, not the measured outcome).
  const [editKpi, setEditKpi] = useState<any>(null)
  const kpiUpdateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: any }) => updateKpi(tenantId, staffId, id, cleanPayload(d)),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['staff-kpis', staffId] }); setEditKpi(null) },
    onError: (err: any) => alert(`Failed to update KPI: ${getGenericErrorMessage(err)}`),
  })

  const scoreBadge = (s: number | null) => {
    if (s === null || s === undefined) return <span className="text-slate-400">—</span>
    const n = Number(s)
    const cls = n >= 4 ? 'text-emerald-700 bg-emerald-50' : n >= 3 ? 'text-amber-700 bg-amber-50' : 'text-red-700 bg-red-50'
    return <span className={`text-xs font-bold px-2 py-0.5 rounded ${cls}`}>{n.toFixed(1)}</span>
  }

  const goalStatusIcon = (s: string) => {
    if (s === 'Completed')   return <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
    if (s === 'In Progress') return <Clock className="h-3.5 w-3.5 text-purple-500" />
    return <div className="h-3.5 w-3.5 rounded-full border-2 border-slate-300" />
  }

  const goalStatusCls = (s: string) =>
    s === 'Completed' ? 'bg-emerald-100 text-emerald-700' :
    s === 'In Progress' ? 'bg-purple-100 text-purple-700' :
    'bg-slate-100 text-slate-500'

  // ── Performance History — a single chronological timeline across
  // reviews, goals and KPIs, newest first. Built from data already loaded
  // above rather than a separate endpoint.
  const historyEvents = useMemo(() => {
    const events: { date: string; type: string; title: string; detail: string }[] = []
    for (const rv of reviews) {
      events.push({
        date: rv.review_date || rv.created_at || '',
        type: 'Review',
        title: `${rv.review_period ?? 'Review'} (${rv.review_type ?? '—'})`,
        detail: `${rv.review_status ?? ''}${rv.overall_score != null ? ` · Overall score ${Number(rv.overall_score).toFixed(1)}` : ''}`,
      })
    }
    for (const g of goals) {
      events.push({
        date: g.due_date || g.created_at || '',
        type: 'Goal',
        title: g.goal_title ?? 'Goal',
        detail: `${g.goal_status ?? ''}${g.goal_category ? ` · ${g.goal_category}` : ''}`,
      })
    }
    for (const k of kpis) {
      events.push({
        date: k.period || k.created_at || '',
        type: 'KPI',
        title: k.kpi_name ?? 'KPI',
        detail: `${k.actual_value != null ? `Actual ${k.actual_value}` : ''}${k.score != null ? ` · Score ${Number(k.score).toFixed(1)}` : ''}`,
      })
    }
    return events
      .filter(e => e.date)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }, [reviews, goals, kpis])

  const [showHistory, setShowHistory] = useState(false)
  const [showReports, setShowReports] = useState(false)

  // ── Performance Reports — aggregated metrics computed client-side from
  // the same review / goal / KPI data, plus a printable summary.
  const perfReport = useMemo(() => {
    const scored = reviews.filter((r: any) => r.overall_score != null)
    const avgOverall = scored.length
      ? scored.reduce((sum: number, r: any) => sum + Number(r.overall_score), 0) / scored.length
      : null
    const completedGoals = goals.filter((g: any) => g.goal_status === 'Completed').length
    const kpiScored = kpis.filter((k: any) => k.score != null)
    const avgKpiScore = kpiScored.length
      ? kpiScored.reduce((sum: number, k: any) => sum + Number(k.score), 0) / kpiScored.length
      : null
    return {
      totalReviews: reviews.length,
      avgOverall,
      totalGoals: goals.length,
      completedGoals,
      goalCompletionRate: goals.length ? Math.round((completedGoals / goals.length) * 100) : null,
      totalKpis: kpis.length,
      avgKpiScore,
    }
  }, [reviews, goals, kpis])

  const printReport = () => {
    const win = window.open('', '_blank', 'width=700,height=900')
    if (!win) return
    win.document.write(`
      <html><head><title>Performance Report</title>
      <style>
        body { font-family: system-ui, sans-serif; padding: 32px; color: #1e293b; }
        h1 { font-size: 18px; margin-bottom: 4px; }
        p.sub { color: #64748b; margin-top: 0; margin-bottom: 24px; font-size: 13px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
        td, th { text-align: left; padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
        th { color: #64748b; text-transform: uppercase; font-size: 11px; }
      </style></head><body>
        <h1>Staff Performance Report</h1>
        <p class="sub">Generated ${new Date().toLocaleString('en-AU')}</p>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Total Reviews</td><td>${perfReport.totalReviews}</td></tr>
          <tr><td>Average Overall Score</td><td>${perfReport.avgOverall != null ? perfReport.avgOverall.toFixed(2) : '—'}</td></tr>
          <tr><td>Total Goals</td><td>${perfReport.totalGoals}</td></tr>
          <tr><td>Completed Goals</td><td>${perfReport.completedGoals}</td></tr>
          <tr><td>Goal Completion Rate</td><td>${perfReport.goalCompletionRate != null ? perfReport.goalCompletionRate + '%' : '—'}</td></tr>
          <tr><td>Total KPI Records</td><td>${perfReport.totalKpis}</td></tr>
          <tr><td>Average KPI Score</td><td>${perfReport.avgKpiScore != null ? perfReport.avgKpiScore.toFixed(2) : '—'}</td></tr>
        </table>
      </body></html>
    `)
    win.document.close()
    win.focus()
    win.print()
  }

  return (
    <div className="space-y-6">

      {/* ── Reviews ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Performance Reviews</h3>
          {can('staff:performance') && !rvForm && (
            <Btn variant="secondary" onClick={() => setRvForm({ ...emptyReview })} className="text-xs py-1">
              <Plus className="h-3 w-3" /> New Review
            </Btn>
          )}
        </div>

        {rvForm && (
          <form onSubmit={e => { e.preventDefault(); rvMut.mutate(rvForm) }} className="space-y-4 border border-slate-200 rounded-lg p-4 bg-slate-50">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">New Performance Review</p>
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="Review period *" /><Input required placeholder="e.g. Q3 2026" value={rvForm.review_period} onChange={e => setRvForm({ ...rvForm, review_period: e.target.value })} /></div>
              <div><Label text="Review type" />
                <Select value={rvForm.review_type} onChange={e => setRvForm({ ...rvForm, review_type: e.target.value })}>
                  {['Annual','Quarterly','Probation','Ad-hoc'].map(t => <option key={t}>{t}</option>)}
                </Select>
              </div>
              <div><Label text="Review date" /><Input type="date" value={rvForm.review_date} onChange={e => setRvForm({ ...rvForm, review_date: e.target.value })} /></div>
              <div><Label text="Status" />
                <Select value={rvForm.review_status} onChange={e => setRvForm({ ...rvForm, review_status: e.target.value })}>
                  {['Draft','Completed','Acknowledged'].map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
            </div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wide pt-1">Scores (0.0 – 5.0)</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                ['Overall',       'overall_score'],
                ['Punctuality',   'punctuality_score'],
                ['Care quality',  'care_quality_score'],
                ['Compliance',    'compliance_score'],
                ['Communication', 'communication_score'],
                ['Teamwork',      'teamwork_score'],
              ].map(([lbl, key]) => (
                <div key={key}>
                  <Label text={lbl} />
                  <Input type="number" step="0.1" min="0" max="5" placeholder="0.0–5.0"
                    value={rvForm[key]} onChange={e => setRvForm({ ...rvForm, [key]: e.target.value })} />
                </div>
              ))}
            </div>
            <div><Label text="Reviewer comments" /><Textarea value={rvForm.reviewer_comments} onChange={e => setRvForm({ ...rvForm, reviewer_comments: e.target.value })} placeholder="Overall feedback…" /></div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={rvMut.isPending}>{rvMut.isPending ? 'Saving…' : 'Save Review'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setRvForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}

        {rvLoading ? (
          <p className="text-sm text-slate-400">Loading reviews…</p>
        ) : reviews.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No performance reviews yet.</p>
        ) : (
          <div className="space-y-3">
            {reviews.map((rv: any) => {
              const isEditingThis = editReview?.review_id === rv.review_id
              return (
              <div key={rv.review_id} className="border border-slate-100 rounded-lg p-4">
                {isEditingThis ? (
                  <form
                    onSubmit={e => { e.preventDefault(); rvUpdateMut.mutate({ id: rv.review_id, d: editReview }) }}
                    className="space-y-3 border border-purple-100 bg-purple-50/40 rounded-lg p-3 -m-1 mb-3"
                  >
                    <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Edit Review — {rv.review_period} ({rv.review_type})</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div><Label text="Review date" /><Input type="date" value={editReview.review_date} onChange={e => setEditReview({ ...editReview, review_date: e.target.value })} /></div>
                      <div><Label text="Status" />
                        <Select value={editReview.review_status} onChange={e => setEditReview({ ...editReview, review_status: e.target.value })}>
                          {['Draft','Completed','Acknowledged'].map(s => <option key={s}>{s}</option>)}
                        </Select>
                      </div>
                    </div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wide pt-1">Scores (0.0 – 5.0)</p>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        ['Overall',       'overall_score'],
                        ['Punctuality',   'punctuality_score'],
                        ['Care quality',  'care_quality_score'],
                        ['Compliance',    'compliance_score'],
                        ['Communication', 'communication_score'],
                        ['Teamwork',      'teamwork_score'],
                      ].map(([lbl, key]) => (
                        <div key={key}>
                          <Label text={lbl} />
                          <Input type="number" step="0.1" min="0" max="5" placeholder="0.0–5.0"
                            value={editReview[key]} onChange={e => setEditReview({ ...editReview, [key]: e.target.value })} />
                        </div>
                      ))}
                    </div>
                    <div><Label text="Reviewer comments" /><Textarea value={editReview.reviewer_comments} onChange={e => setEditReview({ ...editReview, reviewer_comments: e.target.value })} placeholder="Overall feedback…" /></div>
                    <div className="flex gap-2">
                      <Btn type="submit" variant="primary" disabled={rvUpdateMut.isPending}>{rvUpdateMut.isPending ? 'Saving…' : 'Save Changes'}</Btn>
                      <Btn type="button" variant="secondary" onClick={() => setEditReview(null)}>Cancel</Btn>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <span className="text-sm font-bold text-slate-700">{rv.review_period}</span>
                        <span className="ml-2 text-xs text-slate-400">{rv.review_type}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${rv.review_status === 'Completed' ? 'bg-emerald-100 text-emerald-700' : rv.review_status === 'Acknowledged' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}`}>
                          {rv.review_status}
                        </span>
                        {can('staff:performance') && (
                          <button
                            onClick={() => setEditReview({
                              review_id: rv.review_id,
                              review_date: rv.review_date?.slice(0, 10) ?? '',
                              review_status: rv.review_status ?? 'Draft',
                              overall_score: rv.overall_score ?? '',
                              punctuality_score: rv.punctuality_score ?? '',
                              care_quality_score: rv.care_quality_score ?? '',
                              compliance_score: rv.compliance_score ?? '',
                              communication_score: rv.communication_score ?? '',
                              teamwork_score: rv.teamwork_score ?? '',
                              reviewer_comments: rv.reviewer_comments ?? '',
                            })}
                            title="Edit review"
                            className="text-slate-300 hover:text-purple-500 transition-colors"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      {[
                        ['Overall',       rv.overall_score],
                        ['Punctuality',   rv.punctuality_score],
                        ['Care quality',  rv.care_quality_score],
                        ['Compliance',    rv.compliance_score],
                        ['Communication', rv.communication_score],
                        ['Teamwork',      rv.teamwork_score],
                      ].map(([lbl, val]) => (
                        <div key={lbl} className="flex items-center justify-between bg-slate-50 rounded px-2 py-1.5">
                          <span className="text-slate-500">{lbl}</span>
                          {scoreBadge(val as number)}
                        </div>
                      ))}
                    </div>
                    {rv.reviewer_comments && (
                      <p className="text-xs text-slate-500 mt-3 border-t border-slate-100 pt-2 italic">{rv.reviewer_comments}</p>
                    )}
                  </>
                )}
              </div>
              )
            })}
          </div>
        )}
      </section>

      {/* ── Goals ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">Goals</h3>
          {can('staff:performance') && !goalForm && (
            <Btn variant="secondary" onClick={() => setGoalForm({ ...emptyGoal })} className="text-xs py-1">
              <Plus className="h-3 w-3" /> Add Goal
            </Btn>
          )}
        </div>

        {goalForm && (
          <form onSubmit={e => { e.preventDefault(); goalMut.mutate(goalForm) }} className="space-y-3 border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><Label text="Goal title *" /><Input required value={goalForm.goal_title} onChange={e => setGoalForm({ ...goalForm, goal_title: e.target.value })} placeholder="e.g. Complete First Aid renewal" /></div>
              <div><Label text="Category" />
                <Select value={goalForm.goal_category} onChange={e => setGoalForm({ ...goalForm, goal_category: e.target.value })}>
                  {['Development','Training','Compliance','Leadership','Other'].map(c => <option key={c}>{c}</option>)}
                </Select>
              </div>
              <div><Label text="Period" /><Input value={goalForm.goal_period} onChange={e => setGoalForm({ ...goalForm, goal_period: e.target.value })} placeholder="e.g. Q4 2026" /></div>
              <div><Label text="Due date" /><Input type="date" value={goalForm.due_date} onChange={e => setGoalForm({ ...goalForm, due_date: e.target.value })} /></div>
              <div><Label text="Status" />
                <Select value={goalForm.goal_status} onChange={e => setGoalForm({ ...goalForm, goal_status: e.target.value })}>
                  {['Not Started','In Progress','Completed'].map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
              <div className="col-span-2"><Label text="Notes" /><Textarea value={goalForm.notes} onChange={e => setGoalForm({ ...goalForm, notes: e.target.value })} /></div>
            </div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={goalMut.isPending}>{goalMut.isPending ? 'Saving…' : 'Add Goal'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setGoalForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}

        {goals.length === 0 && !goalForm ? (
          <p className="text-sm text-slate-400 italic">No goals set yet.</p>
        ) : (
          <div className="space-y-2">
            {goals.map((g: any) => (
              <div key={g.goal_id} className="flex items-start gap-3 p-3 border border-slate-100 rounded-lg hover:bg-slate-50 transition-colors">
                <div className="mt-0.5 shrink-0">{goalStatusIcon(g.goal_status)}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700">{g.goal_title}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className={`text-[11px] px-1.5 py-0.5 rounded font-medium ${goalStatusCls(g.goal_status)}`}>{g.goal_status}</span>
                    {g.goal_category && <span className="text-[11px] text-slate-400">{g.goal_category}</span>}
                    {g.due_date && <span className="text-[11px] text-slate-400">Due {g.due_date?.slice(0, 10)}</span>}
                  </div>
                  {g.notes && <p className="text-xs text-slate-400 mt-1">{g.notes}</p>}
                </div>
                {can('staff:performance') && editGoal?.goal_id !== g.goal_id && (
                  <Btn variant="ghost" onClick={() => setEditGoal({ goal_id: g.goal_id, goal_status: g.goal_status, due_date: g.due_date?.slice(0,10) ?? '', notes: g.notes ?? '' })} className="text-xs py-0.5 px-2 shrink-0">Edit</Btn>
                )}
                {editGoal?.goal_id === g.goal_id && (
                  <div className="flex gap-1 shrink-0">
                    <Select value={editGoal.goal_status} onChange={e => setEditGoal({ ...editGoal, goal_status: e.target.value })} className="!w-auto text-xs h-7 py-0">
                      {['Not Started','In Progress','Completed'].map(s => <option key={s}>{s}</option>)}
                    </Select>
                    <Btn variant="primary" disabled={goalUpdateMut.isPending} onClick={() => goalUpdateMut.mutate({ id: g.goal_id, d: editGoal })} className="text-xs py-0.5 px-2">Save</Btn>
                    <Btn variant="ghost" onClick={() => setEditGoal(null)} className="text-xs py-0.5 px-2">✕</Btn>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── KPIs ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">KPI Records</h3>
          {can('staff:performance') && !kpiForm && (
            <Btn variant="secondary" onClick={() => setKpiForm({ ...emptyKpi })} className="text-xs py-1">
              <Plus className="h-3 w-3" /> Add KPI
            </Btn>
          )}
        </div>

        {kpiForm && (
          <form onSubmit={e => { e.preventDefault(); kpiMut.mutate(kpiForm) }} className="space-y-3 border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="grid grid-cols-2 gap-3">
              <div><Label text="KPI name *" /><Input required value={kpiForm.kpi_name} onChange={e => setKpiForm({ ...kpiForm, kpi_name: e.target.value })} placeholder="e.g. Punctuality" /></div>
              <div><Label text="Category" /><Input value={kpiForm.kpi_category} onChange={e => setKpiForm({ ...kpiForm, kpi_category: e.target.value })} placeholder="e.g. Attendance" /></div>
              <div><Label text="Period" /><Input value={kpiForm.period} onChange={e => setKpiForm({ ...kpiForm, period: e.target.value })} placeholder="e.g. Q3 2026" /></div>
              <div><Label text="Weight (%)" /><Input type="number" value={kpiForm.weight_percent} onChange={e => setKpiForm({ ...kpiForm, weight_percent: e.target.value })} placeholder="e.g. 20" /></div>
              <div><Label text="Target" /><Input type="number" step="0.1" value={kpiForm.target_value} onChange={e => setKpiForm({ ...kpiForm, target_value: e.target.value })} placeholder="0.0–5.0" /></div>
              <div><Label text="Actual" /><Input type="number" step="0.1" value={kpiForm.actual_value} onChange={e => setKpiForm({ ...kpiForm, actual_value: e.target.value })} placeholder="0.0–5.0" /></div>
              <div><Label text="Score (0–5)" /><Input type="number" step="0.1" min="0" max="5" value={kpiForm.score} onChange={e => setKpiForm({ ...kpiForm, score: e.target.value })} /></div>
              <div className="col-span-2"><Label text="Notes" /><Textarea value={kpiForm.notes} onChange={e => setKpiForm({ ...kpiForm, notes: e.target.value })} /></div>
            </div>
            <div className="flex gap-2">
              <Btn type="submit" variant="primary" disabled={kpiMut.isPending}>{kpiMut.isPending ? 'Saving…' : 'Add KPI'}</Btn>
              <Btn type="button" variant="secondary" onClick={() => setKpiForm(null)}>Cancel</Btn>
            </div>
          </form>
        )}

        {kpis.length === 0 && !kpiForm ? (
          <p className="text-sm text-slate-400 italic">No KPI records yet.</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-1.5 text-slate-500 font-semibold">KPI</th>
                <th className="text-left py-1.5 text-slate-500 font-semibold">Category</th>
                <th className="text-left py-1.5 text-slate-500 font-semibold">Period</th>
                <th className="text-center py-1.5 text-slate-500 font-semibold">Target</th>
                <th className="text-center py-1.5 text-slate-500 font-semibold">Actual</th>
                <th className="text-center py-1.5 text-slate-500 font-semibold">Score</th>
                {can('staff:performance') && <th className="text-right py-1.5 text-slate-500 font-semibold">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {kpis.map((k: any) => {
                const isEditingThis = editKpi?.kpi_id === k.kpi_id
                return (
                <Fragment key={k.kpi_id}>
                  <tr className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 font-medium text-slate-700">{k.kpi_name}</td>
                    <td className="py-2 text-slate-500">{k.kpi_category || '—'}</td>
                    <td className="py-2 text-slate-500">{k.period || '—'}</td>
                    <td className="py-2 text-center text-slate-500">{k.target_value ?? '—'}</td>
                    <td className="py-2 text-center">
                      {isEditingThis
                        ? <Input type="number" step="0.1" className="!h-7 text-center" value={editKpi.actual_value} onChange={e => setEditKpi({ ...editKpi, actual_value: e.target.value })} />
                        : (k.actual_value ?? '—')}
                    </td>
                    <td className="py-2 text-center">
                      {isEditingThis
                        ? <Input type="number" step="0.1" min="0" max="5" className="!h-7 text-center" value={editKpi.score} onChange={e => setEditKpi({ ...editKpi, score: e.target.value })} />
                        : scoreBadge(k.score)}
                    </td>
                    {can('staff:performance') && (
                      <td className="py-2 text-right">
                        {isEditingThis ? (
                          <div className="flex gap-1 justify-end">
                            <Btn variant="primary" disabled={kpiUpdateMut.isPending} onClick={() => kpiUpdateMut.mutate({ id: k.kpi_id, d: editKpi })} className="text-xs py-0.5 px-2">
                              {kpiUpdateMut.isPending ? 'Saving…' : 'Save'}
                            </Btn>
                            <Btn variant="ghost" onClick={() => setEditKpi(null)} className="text-xs py-0.5 px-2">✕</Btn>
                          </div>
                        ) : (
                          <button
                            onClick={() => setEditKpi({ kpi_id: k.kpi_id, actual_value: k.actual_value ?? '', score: k.score ?? '', notes: k.notes ?? '' })}
                            title="Edit KPI"
                            className="text-slate-300 hover:text-purple-500 transition-colors"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                  {isEditingThis && (
                    <tr className="border-b border-slate-100 bg-purple-50/40">
                      <td colSpan={7} className="py-2">
                        <Label text="Notes" />
                        <Textarea value={editKpi.notes} onChange={e => setEditKpi({ ...editKpi, notes: e.target.value })} placeholder="Notes about this KPI result…" />
                      </td>
                    </tr>
                  )}
                </Fragment>
                )
              })}
            </tbody>
          </table>
        )}
      </section>

      {/* ── Performance History ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-3">
        <button
          type="button"
          onClick={() => setShowHistory(s => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <h3 className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-slate-400" /> Performance History
          </h3>
          {showHistory ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
        </button>
        {showHistory && (
          historyEvents.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No history to show yet.</p>
          ) : (
            <div className="relative pl-4 border-l border-slate-100 space-y-3">
              {historyEvents.map((ev, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-purple-300" />
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{ev.type}</span>
                    <span className="text-xs font-medium text-slate-700">{ev.title}</span>
                    <span className="text-xs text-slate-400 ml-auto">{new Date(ev.date).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                  </div>
                  {ev.detail && <p className="text-xs text-slate-500 mt-0.5">{ev.detail}</p>}
                </div>
              ))}
            </div>
          )
        )}
      </section>

      {/* ── Performance Reports ── */}
      <section className="bg-white rounded-xl border border-slate-100 p-5 space-y-3">
        <button
          type="button"
          onClick={() => setShowReports(s => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <h3 className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
            <FileText className="h-4 w-4 text-slate-400" /> Performance Reports
          </h3>
          {showReports ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
        </button>
        {showReports && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ['Avg. Overall Score', perfReport.avgOverall != null ? perfReport.avgOverall.toFixed(2) : '—'],
                ['Goal Completion', perfReport.goalCompletionRate != null ? `${perfReport.goalCompletionRate}%` : '—'],
                ['Avg. KPI Score', perfReport.avgKpiScore != null ? perfReport.avgKpiScore.toFixed(2) : '—'],
                ['Total Records', perfReport.totalReviews + perfReport.totalGoals + perfReport.totalKpis],
              ].map(([lbl, val]) => (
                <div key={lbl as string} className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-slate-700">{val}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">{lbl}</p>
                </div>
              ))}
            </div>
            <Btn variant="secondary" onClick={printReport} className="text-xs py-1.5">
              <Download className="h-3 w-3" /> Print / Export Report
            </Btn>
          </div>
        )}
      </section>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Edit Staff Profile SlideOver
// ══════════════════════════════════════════════════════════════════════════════

function EditStaffSlideOver({ open, tenantId, staff, onClose, onSaved }: {
  open: boolean; tenantId: number; staff: any; onClose: () => void; onSaved: (updated: any) => void
}) {
  const [form, setForm] = useState({
    first_name:  staff?.first_name  ?? '',
    middle_name: staff?.middle_name ?? '',
    last_name:   staff?.last_name   ?? '',
    work_email:  staff?.work_email  ?? '',
    photo:       staff?.photo       ?? '',
    status:      staff?.status      ?? 'Active',
  })

  // Re-populate form whenever the slide-over opens or the staff record changes
  useEffect(() => {
    if (open && staff) {
      setForm({
        first_name:  staff.first_name  ?? '',
        middle_name: staff.middle_name ?? '',
        last_name:   staff.last_name   ?? '',
        work_email:  staff.work_email  ?? '',
        photo:       staff.photo       ?? '',
        status:      staff.status      ?? 'Active',
      })
    }
  }, [open, staff])

  const mut = useMutation({
    mutationFn: () => updateStaff(tenantId, staff.staff_id, form),
    onSuccess: () => { onSaved({ ...staff, ...form }); onClose() },
  })

  if (!staff) return null

  return (
    <SlideOver
      open={open}
      onClose={onClose}
      title="Edit Staff Profile"
      subtitle={`${staff.first_name} ${staff.last_name}`}
    >
      <form onSubmit={e => { e.preventDefault(); mut.mutate() }} className="space-y-4">

        {/* Avatar preview */}
        <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl">
          <div className="h-14 w-14 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center text-xl font-bold shrink-0">
            {form.first_name?.[0]}{form.last_name?.[0]}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-700 truncate">
              {[form.first_name, form.middle_name, form.last_name].filter(Boolean).join(' ') || 'New Staff'}
            </p>
            <p className="text-xs text-slate-400 truncate">{form.work_email || 'No work email'}</p>
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Name</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label text="First Name *" />
              <Input required value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} />
            </div>
            <div>
              <Label text="Middle Name" />
              <Input value={form.middle_name} onChange={e => setForm({ ...form, middle_name: e.target.value })} />
            </div>
            <div className="col-span-2">
              <Label text="Last Name *" />
              <Input required value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} />
            </div>
          </div>
        </div>

        <div className="space-y-3 border-t border-slate-100 pt-4">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Work Details</p>
          <div>
            <Label text="Work Email" />
            <Input type="email" value={form.work_email} onChange={e => setForm({ ...form, work_email: e.target.value })} placeholder="jane.smith@organisation.com.au" />
          </div>
          <div>
            <Label text="Status" />
            <Select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
              {['Active', 'Inactive', 'On Leave', 'Terminated'].map(s => <option key={s}>{s}</option>)}
            </Select>
          </div>
          <div>
            <Label text="Photo URL" />
            <Input value={form.photo} onChange={e => setForm({ ...form, photo: e.target.value })} placeholder="https://…" />
            <p className="text-xs text-slate-400 mt-1">Paste a URL to a profile photo</p>
          </div>
        </div>

        {mut.isError && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600">
            <AlertCircle className="h-4 w-4 shrink-0" />
            Failed to save changes. Please try again.
          </div>
        )}

        <div className="flex gap-3 pt-2 border-t border-slate-100">
          <button
            type="submit"
            disabled={mut.isPending || !form.first_name || !form.last_name}
            className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-700 hover:bg-purple-800 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {mut.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            {mut.isPending ? 'Saving…' : 'Save Changes'}
          </button>
          <button type="button" onClick={onClose} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
            Cancel
          </button>
        </div>
      </form>
    </SlideOver>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// Main Page
// ══════════════════════════════════════════════════════════════════════════════

export default function StaffPage() {
  const { user } = useAuth()
  const { can } = usePermissions()
  const tenantId: number = user?.tenant_id

  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedStaff, setSelectedStaff] = useState<any>(null)
  const [activeTab, setActiveTab]   = useState<Tab>('profile')
  const [showEdit, setShowEdit]     = useState(false)

  const handleSelect = (id: string, s: any) => {
    setSelectedId(id)
    setSelectedStaff(s)
    setActiveTab('profile')
  }

  const handleSaved = (updated: any) => {
    setSelectedStaff(updated)
    qc.invalidateQueries({ queryKey: ['staff', tenantId] })
  }

  const handleBack = () => {
    setSelectedId(null)
    setSelectedStaff(null)
    setActiveTab('profile')
  }

  return (
    <Layout
      title="Staff Management"
      breadcrumbs={[{ label: 'Staff Management' }]}
    >
      {!selectedId ? (
        /* ── SCREEN 1: Full-width staff list ─────────────────────────────── */
        <StaffListPage
          tenantId={tenantId}
          onSelect={handleSelect}
        />
      ) : (
        /* ── SCREEN 2: Staff detail with chip nav ─────────────────────────── */
        <div className="flex flex-col gap-5">

          {/* Back link */}
          <button
            onClick={handleBack}
            className="flex items-center gap-1.5 text-xs text-purple-600 hover:text-purple-800 font-medium transition-colors w-fit"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to staff list
          </button>

          {/* Chip / tag navigation */}
          <div className="flex flex-wrap gap-2">
            {CHIPS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  activeTab === key
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-white text-slate-500 border-slate-200 hover:border-purple-400 hover:text-purple-600'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {activeTab === 'profile' && (
              <ProfileTab
                tenantId={tenantId}
                staffId={selectedId}
                staff={selectedStaff}
                onEditProfile={can('staff:edit') ? () => setShowEdit(true) : undefined}
              />
            )}
            {activeTab === 'employment' && (
              <EmploymentTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'compliance' && (
              <ComplianceTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'compliance_tracking' && (
              <ComplianceTrackingTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'availability' && (
              <AvailabilityTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'timesheets' && (
              <TimesheetsTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'leave' && (
              <LeaveTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'documents' && (
              <DocumentsTab tenantId={tenantId} staffId={selectedId} />
            )}
            {activeTab === 'performance' && (
              <PerformanceTab tenantId={tenantId} staffId={selectedId} />
            )}
          </div>
        </div>
      )}

      <EditStaffSlideOver
        open={showEdit}
        tenantId={tenantId}
        staff={selectedStaff}
        onClose={() => setShowEdit(false)}
        onSaved={handleSaved}
      />
    </Layout>
  )
}
