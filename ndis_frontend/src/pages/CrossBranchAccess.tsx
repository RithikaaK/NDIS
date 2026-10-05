import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { useAuth } from '@/context/AuthContext'
import { getBranches } from '@/api/branches'
import { getUsers } from '@/api/users'
import {
  listCrossbranchAccess,
  createAccessRequest,
  createEmergencyAccess,
  approveAccess,
  rejectAccess,
  revokeAccess,
  reviewEmergencyAccess,
  getCrossbranchAudit,
} from '@/api/crossBranchAccess'
import {
  Plus, Search, Shield, Clock, CheckCircle2, XCircle,
  AlertTriangle, Eye, Ban, RotateCcw, Activity, ChevronDown,
  Zap, Users, ArrowRightLeft,
} from 'lucide-react'

// ── Style constants ───────────────────────────────────────────────────────────
const inputCls   = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls  = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls   = "text-xs font-semibold text-slate-600 uppercase tracking-wide"
const textareaCls = "w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all resize-none"

type Tab = 'pending' | 'active' | 'emergency' | 'all' | 'audit'

// ── Status helpers ────────────────────────────────────────────────────────────
const STATUS_META: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  pending:  { label: 'Pending',  bg: 'bg-amber-50',   text: 'text-amber-700',  dot: 'bg-amber-400'  },
  approved: { label: 'Approved', bg: 'bg-blue-50',    text: 'text-blue-700',   dot: 'bg-blue-500'   },
  active:   { label: 'Active',   bg: 'bg-emerald-50', text: 'text-emerald-700',dot: 'bg-emerald-500'},
  expired:  { label: 'Expired',  bg: 'bg-slate-100',  text: 'text-slate-500',  dot: 'bg-slate-400'  },
  rejected: { label: 'Rejected', bg: 'bg-red-50',     text: 'text-red-700',    dot: 'bg-red-500'    },
  revoked:  { label: 'Revoked',  bg: 'bg-slate-100',  text: 'text-slate-500',  dot: 'bg-slate-400'  },
}

const StatusPill = ({ status }: { status: string }) => {
  const m = STATUS_META[status] ?? { label: status, bg: 'bg-slate-100', text: 'text-slate-600', dot: 'bg-slate-400' }
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full ${m.bg} ${m.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />{m.label}
    </span>
  )
}

const fmt = (dt?: string | null) => dt
  ? new Date(dt).toLocaleString('en-AU', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true })
  : '—'

const fmtDate = (dt?: string | null) => dt
  ? new Date(dt).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })
  : '—'

// ── SaveBar ───────────────────────────────────────────────────────────────────
const SaveBar = ({ onSave, onCancel, isPending, label = 'Submit' }: any) => (
  <div className="flex gap-3 pt-4 border-t border-slate-100 mt-2">
    <button
      onClick={onSave}
      disabled={isPending}
      className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
    >
      {isPending && <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
      {isPending ? 'Saving…' : label}
    </button>
    <button onClick={onCancel} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
  </div>
)

// ── Record card ───────────────────────────────────────────────────────────────
function AccessCard({
  rec,
  branches,
  users,
  onApprove,
  onReject,
  onRevoke,
  onReview,
}: {
  rec: any
  branches: any[]
  users: any[]
  onApprove: (id: number) => void
  onReject:  (id: number) => void
  onRevoke:  (id: number) => void
  onReview:  (id: number) => void
}) {
  const [exp, setExp] = useState(false)
  const homeBranch   = branches.find(b => b.branch_id === rec.home_branch_id)?.branch_name ?? `Branch #${rec.home_branch_id}`
  const targetBranch = branches.find(b => b.branch_id === rec.target_branch_id)?.branch_name ?? `Branch #${rec.target_branch_id}`
  const staffUser    = users.find(u => u.user_id === rec.staff_user_id)
  const staffName    = staffUser ? `${staffUser.first_name} ${staffUser.last_name}` : (rec.staff_user_id ?? '—')
  const resolveUser  = (uid: string | null | undefined) => {
    if (!uid) return null
    const u = users.find((x: any) => x.user_id === uid)
    return u ? `${u.first_name} ${u.last_name}` : uid
  }

  return (
    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden">
      {/* Header row */}
      <div className="flex items-center gap-4 px-5 py-4">
        <div className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${rec.is_emergency ? 'bg-red-50' : 'bg-purple-50'}`}>
          {rec.is_emergency ? <Zap className="h-5 w-5 text-red-500" /> : <ArrowRightLeft className="h-5 w-5 text-purple-500" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-slate-900">{staffName}</span>
            {rec.is_emergency && (
              <span className="text-xs bg-red-50 text-red-600 border border-red-200 rounded px-2 py-0.5 font-medium">Emergency</span>
            )}
            {rec.requires_review && (
              <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded px-2 py-0.5 font-medium flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" /> Needs review
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {homeBranch} → {targetBranch}
            {rec.participant_name && <> · <span className="font-medium">{rec.participant_name}</span></>}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <StatusPill status={rec.status} />
          <button onClick={() => setExp(e => !e)} className="h-7 w-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-400 hover:bg-slate-50 transition-colors">
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${exp ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {exp && (
        <div className="border-t border-slate-100 px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Access type</p>
              <p className="text-slate-800 capitalize">{rec.access_type}</p>
            </div>
            <div>
              <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Requested</p>
              <p className="text-slate-800">{fmt(rec.requested_at)}</p>
            </div>
            <div>
              <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Access period</p>
              <p className="text-slate-800">
                {rec.access_start || rec.access_end
                  ? `${fmtDate(rec.access_start)} – ${fmtDate(rec.access_end)}`
                  : 'Not specified'}
              </p>
            </div>
            {rec.participant_name && (
              <div>
                <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Participant</p>
                <p className="text-slate-800">{rec.participant_name}</p>
              </div>
            )}
            {rec.approved_by && (
              <div>
                <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Approved by</p>
                <p className="text-slate-800">{resolveUser(rec.approved_by) ?? rec.approved_by}</p>
              </div>
            )}
            {rec.rejected_by && (
              <div>
                <p className="text-slate-400 uppercase tracking-wide font-medium mb-0.5">Rejected by</p>
                <p className="text-slate-800">{resolveUser(rec.rejected_by) ?? rec.rejected_by}</p>
              </div>
            )}
          </div>

          <div>
            <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Reason</p>
            <p className="text-sm text-slate-800">{rec.access_reason}</p>
          </div>

          {rec.services_description && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Services</p>
              <p className="text-sm text-slate-800">{rec.services_description}</p>
            </div>
          )}

          {rec.permitted_activities && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Permitted activities</p>
              <p className="text-sm text-slate-800">{rec.permitted_activities}</p>
            </div>
          )}

          {rec.approval_comments && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Approval notes</p>
              <p className="text-sm text-slate-800">{rec.approval_comments}</p>
            </div>
          )}
          {rec.rejection_reason && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Rejection reason</p>
              <p className="text-sm text-slate-800">{rec.rejection_reason}</p>
            </div>
          )}
          {rec.review_notes && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium mb-0.5">Review notes</p>
              <p className="text-sm text-slate-800">{rec.review_notes}</p>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 flex-wrap pt-1">
            {rec.status === 'pending' && (
              <>
                <button
                  onClick={() => onApprove(rec.access_id)}
                  className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" /> Approve
                </button>
                <button
                  onClick={() => onReject(rec.access_id)}
                  className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  <XCircle className="h-3.5 w-3.5" /> Reject
                </button>
              </>
            )}
            {(rec.status === 'active' || rec.status === 'approved') && (
              <button
                onClick={() => onRevoke(rec.access_id)}
                className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium bg-slate-700 hover:bg-slate-800 text-white rounded-lg transition-colors"
              >
                <Ban className="h-3.5 w-3.5" /> Revoke
              </button>
            )}
            {rec.is_emergency && rec.requires_review && (
              <button
                onClick={() => onReview(rec.access_id)}
                className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
              >
                <Eye className="h-3.5 w-3.5" /> Mark reviewed
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function CrossBranchAccessPage() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const qc = useQueryClient()

  const [tab, setTab]           = useState<Tab>('pending')
  const [search, setSearch]     = useState('')
  const [slideMode, setSlideMode] = useState<'request' | 'emergency' | 'approve' | 'reject' | 'revoke' | 'review' | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [toast, setToast]       = useState('')

  // Form states
  const [reqForm, setReqForm]   = useState<any>({ staff_user_id: '', home_branch_id: '', target_branch_id: '', access_reason: '', services_description: '', access_start: '', access_end: '', participant_id: '', participant_name: '', permitted_activities: '' })
  const [emergForm, setEmergForm] = useState<any>({ staff_user_id: '', home_branch_id: '', target_branch_id: '', emergency_reason: '', services_description: '', access_end: '', participant_name: '', permitted_activities: '' })
  const [approveForm, setApproveForm] = useState<any>({ approval_comments: '', access_end: '' })
  const [rejectForm, setRejectForm]   = useState<any>({ rejection_reason: '' })
  const [revokeForm, setRevokeForm]   = useState<any>({ revoke_reason: '' })
  const [reviewForm, setReviewForm]   = useState<any>({ review_notes: '' })

  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3500) }
  const invalidate = () => qc.invalidateQueries({ queryKey: ['cross-branch-access', tenantId] })

  // ── Queries ──────────────────────────────────────────────────────────────────
  const { data: allAccess = [], isLoading } = useQuery({
    queryKey: ['cross-branch-access', tenantId],
    queryFn: () => listCrossbranchAccess(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  const { data: audit = [] } = useQuery({
    queryKey: ['cross-branch-audit', tenantId],
    queryFn: () => getCrossbranchAudit(tenantId).then(r => r.data || []),
    enabled: !!tenantId && tab === 'audit',
  })

  const { data: branches = [] } = useQuery({
    queryKey: ['branches', tenantId],
    queryFn: () => getBranches(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users', tenantId],
    queryFn: () => getUsers(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  // ── Mutations ─────────────────────────────────────────────────────────────
  const createMut  = useMutation({ mutationFn: (d: any) => createAccessRequest(tenantId, d),   onSuccess: () => { invalidate(); setSlideMode(null); flash('Access request submitted.') } })
  const emergMut   = useMutation({ mutationFn: (d: any) => createEmergencyAccess(tenantId, d), onSuccess: () => { invalidate(); setSlideMode(null); flash('Emergency access granted — flagged for review.') } })
  const approveMut = useMutation({ mutationFn: ({ id, d }: any) => approveAccess(tenantId, id, d), onSuccess: () => { invalidate(); setSlideMode(null); flash('Access approved.') } })
  const rejectMut  = useMutation({ mutationFn: ({ id, d }: any) => rejectAccess(tenantId, id, d),  onSuccess: () => { invalidate(); setSlideMode(null); flash('Access rejected.') } })
  const revokeMut  = useMutation({ mutationFn: ({ id, d }: any) => revokeAccess(tenantId, id, d),  onSuccess: () => { invalidate(); setSlideMode(null); flash('Access revoked.') } })
  const reviewMut  = useMutation({ mutationFn: ({ id, d }: any) => reviewEmergencyAccess(tenantId, id, d), onSuccess: () => { invalidate(); setSlideMode(null); flash('Emergency access marked as reviewed.') } })

  // ── Tab filtering ─────────────────────────────────────────────────────────
  const tabData = (allAccess as any[]).filter((r: any) => {
    const matchSearch = search
      ? `${r.staff_user_id} ${r.access_reason} ${r.participant_name || ''}`.toLowerCase().includes(search.toLowerCase())
      : true
    if (!matchSearch) return false
    if (tab === 'pending')   return r.status === 'pending'
    if (tab === 'active')    return r.status === 'active' || r.status === 'approved'
    if (tab === 'emergency') return r.is_emergency
    return true
  })

  const pendingCnt   = (allAccess as any[]).filter((r: any) => r.status === 'pending').length
  const activeCnt    = (allAccess as any[]).filter((r: any) => r.status === 'active' || r.status === 'approved').length
  const emergencyCnt = (allAccess as any[]).filter((r: any) => r.is_emergency).length
  const reviewCnt    = (allAccess as any[]).filter((r: any) => r.requires_review).length

  // ── Handlers ──────────────────────────────────────────────────────────────
  const openApprove = (id: number) => { setSelectedId(id); setApproveForm({ approval_comments: '', access_end: '' }); setSlideMode('approve') }
  const openReject  = (id: number) => { setSelectedId(id); setRejectForm({ rejection_reason: '' }); setSlideMode('reject') }
  const openRevoke  = (id: number) => { setSelectedId(id); setRevokeForm({ revoke_reason: '' }); setSlideMode('revoke') }
  const openReview  = (id: number) => { setSelectedId(id); setReviewForm({ review_notes: '' }); setSlideMode('review') }

  const TABS: { id: Tab; label: string; count?: number }[] = [
    { id: 'pending',   label: 'Pending',   count: pendingCnt },
    { id: 'active',    label: 'Active',    count: activeCnt },
    { id: 'emergency', label: 'Emergency', count: emergencyCnt },
    { id: 'all',       label: 'All' },
    { id: 'audit',     label: 'Audit Trail' },
  ]

  return (
    <Layout title="Cross-Branch Access">
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
            <h1 className="text-xl font-semibold text-slate-900">Cross-Branch Access</h1>
            <p className="text-sm text-slate-400 mt-0.5">Manage staff access across branch locations</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => { setEmergForm({ staff_user_id: '', home_branch_id: '', target_branch_id: '', emergency_reason: '', services_description: '', access_end: '', participant_name: '', permitted_activities: '' }); setSlideMode('emergency') }}
              className="flex items-center gap-1.5 border border-red-200 text-red-600 hover:bg-red-50 text-sm font-medium px-3 h-9 rounded-lg transition-colors"
            >
              <Zap className="h-4 w-4" /> Emergency
            </button>
            <button
              onClick={() => { setReqForm({ staff_user_id: '', home_branch_id: '', target_branch_id: '', access_reason: '', services_description: '', access_start: '', access_end: '', participant_id: '', participant_name: '', permitted_activities: '' }); setSlideMode('request') }}
              className="flex items-center gap-1.5 bg-purple-800 hover:bg-purple-900 text-white text-sm font-medium px-4 h-9 rounded-lg transition-colors"
            >
              <Plus className="h-4 w-4" /> Request access
            </button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Pending Requests', value: pendingCnt,   icon: Clock,         color: 'text-amber-600',  bg: 'bg-amber-50'  },
            { label: 'Active Access',    value: activeCnt,    icon: CheckCircle2,  color: 'text-emerald-600',bg: 'bg-emerald-50'},
            { label: 'Emergency',        value: emergencyCnt, icon: Zap,           color: 'text-red-600',    bg: 'bg-red-50'    },
            { label: 'Needs Review',     value: reviewCnt,    icon: AlertTriangle, color: 'text-purple-600', bg: 'bg-purple-50' },
          ].map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="bg-white border border-slate-100 rounded-2xl p-4 flex items-center gap-3">
              <div className={`h-10 w-10 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
              <div>
                <p className="text-xl font-bold text-slate-900">{value}</p>
                <p className="text-xs text-slate-400">{label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Tabs + search */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex border border-slate-200 rounded-lg overflow-hidden text-sm shrink-0">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-3 h-9 font-medium border-r border-slate-200 last:border-r-0 transition-colors whitespace-nowrap ${
                  tab === t.id ? 'bg-purple-800 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'
                }`}
              >
                {t.label}{t.count !== undefined ? ` (${t.count})` : ''}
              </button>
            ))}
          </div>
          {tab !== 'audit' && (
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by staff, reason, participant…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full h-9 pl-8 pr-3 rounded-lg border border-slate-200 bg-white text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all"
              />
            </div>
          )}
        </div>

        {/* ── AUDIT TRAIL TAB ─────────────────────────────────────────────── */}
        {tab === 'audit' && (
          <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-purple-500" />
              <h2 className="text-sm font-semibold text-slate-700">Access Audit Trail</h2>
              <span className="ml-auto text-xs text-slate-400">{(audit as any[]).length} records</span>
            </div>
            {(audit as any[]).length === 0 ? (
              <div className="py-16 text-center text-slate-400 text-sm">No audit records yet.</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {(audit as any[]).map((r: any) => {
                  const homeBranch   = branches.find((b: any) => b.branch_id === r.home_branch_id)?.branch_name ?? `Branch #${r.home_branch_id}`
                  const targetBranch = branches.find((b: any) => b.branch_id === r.target_branch_id)?.branch_name ?? `Branch #${r.target_branch_id}`
                  const auditStaff   = (users as any[]).find(u => u.user_id === r.staff_user_id)
                  const auditStaffName = auditStaff ? `${auditStaff.first_name} ${auditStaff.last_name}` : (r.staff_user_id ?? '—')
                  return (
                    <div key={r.access_id} className="px-5 py-3 flex items-start gap-4 text-xs hover:bg-slate-50">
                      <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${r.is_emergency ? 'bg-red-50' : 'bg-purple-50'}`}>
                        {r.is_emergency ? <Zap className="h-3.5 w-3.5 text-red-500" /> : <ArrowRightLeft className="h-3.5 w-3.5 text-purple-500" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-0.5">
                          <span className="font-semibold text-slate-800">{auditStaffName}</span>
                          <span className="text-slate-400">{homeBranch} → {targetBranch}</span>
                          {r.participant_name && <span className="text-slate-600">· {r.participant_name}</span>}
                          <StatusPill status={r.status} />
                          {r.is_emergency && <span className="bg-red-50 text-red-600 rounded px-1.5 py-0.5 font-medium">Emergency</span>}
                          {r.requires_review && <span className="bg-amber-50 text-amber-600 rounded px-1.5 py-0.5 font-medium">Needs review</span>}
                        </div>
                        <p className="text-slate-500">{r.access_reason}</p>
                        <div className="flex gap-4 mt-1 text-slate-400">
                          <span>Requested {fmt(r.requested_at)}</span>
                          {r.approved_at && <span>Approved {fmt(r.approved_at)}</span>}
                          {r.rejected_at && <span>Rejected {fmt(r.rejected_at)}</span>}
                          {r.revoked_at  && <span>Revoked {fmt(r.revoked_at)}</span>}
                          {r.access_end  && <span>Expires {fmtDate(r.access_end)}</span>}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ── ALL OTHER TABS ────────────────────────────────────────────────── */}
        {tab !== 'audit' && (
          isLoading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="h-20 rounded-2xl bg-slate-100 animate-pulse" />)}
            </div>
          ) : tabData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 border border-slate-200 rounded-2xl bg-white text-center">
              <div className="h-14 w-14 rounded-2xl bg-purple-50 flex items-center justify-center mb-4">
                <Shield className="h-7 w-7 text-purple-400" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">No records found</h3>
              <p className="text-sm text-slate-400 max-w-xs">
                {tab === 'pending' ? 'No pending access requests.' :
                 tab === 'active'  ? 'No active cross-branch access.' :
                 tab === 'emergency' ? 'No emergency access records.' :
                 'No cross-branch access records yet.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {tabData.map((r: any) => (
                <AccessCard
                  key={r.access_id}
                  rec={r}
                  branches={branches}
                  users={users}
                  onApprove={openApprove}
                  onReject={openReject}
                  onRevoke={openRevoke}
                  onReview={openReview}
                />
              ))}
            </div>
          )
        )}
      </div>

      {/* ── Request Access slide-over ───────────────────────────────────────── */}
      <SlideOver open={slideMode === 'request'} onClose={() => setSlideMode(null)} title="Request Cross-Branch Access" subtitle="4.2 — Submit a planned access request">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Staff member *</label>
            <select className={selectCls} value={reqForm.staff_user_id} onChange={e => setReqForm({ ...reqForm, staff_user_id: e.target.value })}>
              <option value="">Select staff member</option>
              {(users as any[]).map((u: any) => <option key={u.user_id} value={u.user_id}>{u.first_name} {u.last_name} — {u.email}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Home branch *</label>
              <select className={selectCls} value={reqForm.home_branch_id} onChange={e => setReqForm({ ...reqForm, home_branch_id: Number(e.target.value) })}>
                <option value="">Select branch</option>
                {(branches as any[]).map((b: any) => <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Target branch *</label>
              <select className={selectCls} value={reqForm.target_branch_id} onChange={e => setReqForm({ ...reqForm, target_branch_id: Number(e.target.value) })}>
                <option value="">Select branch</option>
                {(branches as any[]).filter((b: any) => b.branch_id !== reqForm.home_branch_id).map((b: any) => <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>)}
              </select>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Reason for access *</label>
            <textarea className={textareaCls} rows={3} value={reqForm.access_reason} onChange={e => setReqForm({ ...reqForm, access_reason: e.target.value })} placeholder="Describe why cross-branch access is required…" />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Services to be provided</label>
            <textarea className={textareaCls} rows={2} value={reqForm.services_description} onChange={e => setReqForm({ ...reqForm, services_description: e.target.value })} placeholder="List specific services or activities…" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Access start</label>
              <input type="datetime-local" className={inputCls} value={reqForm.access_start} onChange={e => setReqForm({ ...reqForm, access_start: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Access end</label>
              <input type="datetime-local" className={inputCls} value={reqForm.access_end} onChange={e => setReqForm({ ...reqForm, access_end: e.target.value })} />
            </div>
          </div>
          <div className="border-t border-slate-100 pt-3 space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Participant-level access (4.6)</p>
            <div className="space-y-1.5">
              <label className={labelCls}>Participant name</label>
              <input className={inputCls} value={reqForm.participant_name} onChange={e => setReqForm({ ...reqForm, participant_name: e.target.value })} placeholder="Leave blank for all participants in branch" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Permitted activities</label>
              <input className={inputCls} value={reqForm.permitted_activities} onChange={e => setReqForm({ ...reqForm, permitted_activities: e.target.value })} placeholder="e.g. Support coordination, Plan management" />
            </div>
          </div>
          <SaveBar
            label="Submit Request"
            isPending={createMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => createMut.mutate({
              ...reqForm,
              access_start: reqForm.access_start || null,
              access_end:   reqForm.access_end   || null,
              participant_id: reqForm.participant_id || null,
              participant_name: reqForm.participant_name || null,
              permitted_activities: reqForm.permitted_activities || null,
              services_description: reqForm.services_description || null,
            })}
          />
        </div>
      </SlideOver>

      {/* ── Emergency Access slide-over ─────────────────────────────────────── */}
      <SlideOver open={slideMode === 'emergency'} onClose={() => setSlideMode(null)} title="Emergency Cross-Branch Access" subtitle="4.5 — Immediate access, flagged for admin review">
        <div className="space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex gap-3">
            <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
            <p className="text-xs text-red-700">Emergency access is granted <strong>immediately</strong> without prior approval. The record will be flagged for mandatory admin review.</p>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Staff member *</label>
            <select className={selectCls} value={emergForm.staff_user_id} onChange={e => setEmergForm({ ...emergForm, staff_user_id: e.target.value })}>
              <option value="">Select staff member</option>
              {(users as any[]).map((u: any) => <option key={u.user_id} value={u.user_id}>{u.first_name} {u.last_name} — {u.email}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Staff's branch *</label>
              <select className={selectCls} value={emergForm.home_branch_id} onChange={e => setEmergForm({ ...emergForm, home_branch_id: Number(e.target.value) })}>
                <option value="">Select branch</option>
                {(branches as any[]).map((b: any) => <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Target branch *</label>
              <select className={selectCls} value={emergForm.target_branch_id} onChange={e => setEmergForm({ ...emergForm, target_branch_id: Number(e.target.value) })}>
                <option value="">Select branch</option>
                {(branches as any[]).filter((b: any) => b.branch_id !== emergForm.home_branch_id).map((b: any) => <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>)}
              </select>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Emergency reason *</label>
            <textarea className={textareaCls} rows={3} value={emergForm.emergency_reason} onChange={e => setEmergForm({ ...emergForm, emergency_reason: e.target.value })} placeholder="Describe the emergency situation — why are normal approval steps being bypassed…" />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Services to be provided</label>
            <textarea className={textareaCls} rows={2} value={emergForm.services_description} onChange={e => setEmergForm({ ...emergForm, services_description: e.target.value })} placeholder="What services will be delivered during this emergency access?" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Participant</label>
              <input className={inputCls} value={emergForm.participant_name} onChange={e => setEmergForm({ ...emergForm, participant_name: e.target.value })} placeholder="Participant name (optional)" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Access expires</label>
              <input type="datetime-local" className={inputCls} value={emergForm.access_end} onChange={e => setEmergForm({ ...emergForm, access_end: e.target.value })} />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Permitted activities</label>
            <input className={inputCls} value={emergForm.permitted_activities} onChange={e => setEmergForm({ ...emergForm, permitted_activities: e.target.value })} placeholder="e.g. Support coordination, medication administration" />
          </div>
          <SaveBar
            label="Grant Emergency Access"
            isPending={emergMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => emergMut.mutate({
              ...emergForm,
              home_branch_id: emergForm.home_branch_id || null,
              target_branch_id: emergForm.target_branch_id || null,
              access_end: emergForm.access_end || null,
              participant_name: emergForm.participant_name || null,
              permitted_activities: emergForm.permitted_activities || null,
              services_description: emergForm.services_description || null,
            })}
          />
        </div>
      </SlideOver>

      {/* ── Approve slide-over ──────────────────────────────────────────────── */}
      <SlideOver open={slideMode === 'approve'} onClose={() => setSlideMode(null)} title="Approve Access Request" subtitle="4.3 — Review and approve">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Approval notes</label>
            <textarea className={textareaCls} rows={3} value={approveForm.approval_comments} onChange={e => setApproveForm({ ...approveForm, approval_comments: e.target.value })} placeholder="Optional notes about this approval…" />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Override access end date</label>
            <input type="datetime-local" className={inputCls} value={approveForm.access_end} onChange={e => setApproveForm({ ...approveForm, access_end: e.target.value })} />
          </div>
          <SaveBar
            label="Approve Access"
            isPending={approveMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => approveMut.mutate({ id: selectedId, d: { approval_comments: approveForm.approval_comments || null, access_end: approveForm.access_end || null } })}
          />
        </div>
      </SlideOver>

      {/* ── Reject slide-over ───────────────────────────────────────────────── */}
      <SlideOver open={slideMode === 'reject'} onClose={() => setSlideMode(null)} title="Reject Access Request" subtitle="4.3 — Decline with reason">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Rejection reason</label>
            <textarea className={textareaCls} rows={3} value={rejectForm.rejection_reason} onChange={e => setRejectForm({ ...rejectForm, rejection_reason: e.target.value })} placeholder="Explain why this request is being declined…" />
          </div>
          <SaveBar
            label="Reject Request"
            isPending={rejectMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => rejectMut.mutate({ id: selectedId, d: { rejection_reason: rejectForm.rejection_reason || null } })}
          />
        </div>
      </SlideOver>

      {/* ── Revoke slide-over ───────────────────────────────────────────────── */}
      <SlideOver open={slideMode === 'revoke'} onClose={() => setSlideMode(null)} title="Revoke Access" subtitle="Remove an active grant">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Reason for revocation</label>
            <textarea className={textareaCls} rows={3} value={revokeForm.revoke_reason} onChange={e => setRevokeForm({ ...revokeForm, revoke_reason: e.target.value })} placeholder="Why is this access being revoked?" />
          </div>
          <SaveBar
            label="Revoke Access"
            isPending={revokeMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => revokeMut.mutate({ id: selectedId, d: { revoke_reason: revokeForm.revoke_reason || null } })}
          />
        </div>
      </SlideOver>

      {/* ── Review slide-over ───────────────────────────────────────────────── */}
      <SlideOver open={slideMode === 'review'} onClose={() => setSlideMode(null)} title="Review Emergency Access" subtitle="4.5 — Mark emergency access as reviewed">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Review notes</label>
            <textarea className={textareaCls} rows={3} value={reviewForm.review_notes} onChange={e => setReviewForm({ ...reviewForm, review_notes: e.target.value })} placeholder="Document your review findings and any follow-up actions…" />
          </div>
          <SaveBar
            label="Mark as Reviewed"
            isPending={reviewMut.isPending}
            onCancel={() => setSlideMode(null)}
            onSave={() => reviewMut.mutate({ id: selectedId, d: { review_notes: reviewForm.review_notes || null } })}
          />
        </div>
      </SlideOver>

    </Layout>
  )
}
