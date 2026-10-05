import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { useAuth } from '@/context/AuthContext'
import { usePermissions } from '@/hooks/usePermissions'
import {
  getUsers, createUser, updateUser, deleteUser,
  getUserRoles, activateUser, deactivateUser,
  resendInvitation, getUserActivity, getUserPermissions,
} from '@/api/users'
import { getBranches } from '@/api/branches'
import { getRoles } from '@/api/roles'
import {
  Plus, Edit2, Trash2, Power, PowerOff, Send,
  User, Shield, Activity, ChevronRight, Mail,
  Building2, ExternalLink,
} from 'lucide-react'

// ── Style helpers ─────────────────────────────────────────────────────────────
const inputCls  = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls  = "text-xs font-semibold text-slate-600 uppercase tracking-wide"
const secLbl    = "text-[10px] font-semibold text-slate-400 uppercase tracking-widest pb-2 border-b border-slate-100 mb-3"

const AVATAR_COLORS = [
  { bg: '#ede9fe', text: '#5b21b6' }, { bg: '#e0f2fe', text: '#075985' },
  { bg: '#fef9c3', text: '#854d0e' }, { bg: '#fce7f3', text: '#9d174d' },
  { bg: '#dcfce7', text: '#166534' }, { bg: '#ffedd5', text: '#9a3412' },
  { bg: '#e0e7ff', text: '#3730a3' }, { bg: '#fef3c7', text: '#92400e' },
]
const getColor = (name: string) => AVATAR_COLORS[(name || 'A').charCodeAt(0) % AVATAR_COLORS.length]

const fmtDate = (iso?: string | null) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const ACTION_LABELS: Record<string, string> = {
  CREATE_USER: 'Account created', UPDATE_USER: 'Profile updated',
  ACTIVATE_USER: 'Account activated', DEACTIVATE_USER: 'Account deactivated',
  ASSIGN_ROLE: 'Role assigned', REMOVE_ROLE: 'Role removed',
  CHANGE_PASSWORD: 'Password changed', RESEND_INVITATION: 'Invitation resent',
  DELETE_USER: 'Account deleted',
}

const emptyForm = {
  first_name: '', last_name: '', email: '', phone: '', job_title: '',
  branch_id: '', selected_role_ids: [] as number[],
  is_active: true, is_tenant_admin: false,
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Users() {
  const { user: currentUser } = useAuth()
  const tenantId    = currentUser?.tenant_id
  const queryClient = useQueryClient()
  const navigate    = useNavigate()
  const { can }     = usePermissions()

  const [search, setSearch]           = useState('')
  const [roleFilter, setRoleFilter]   = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [slideOpen, setSlideOpen]     = useState(false)
  const [editing, setEditing]         = useState<any>(null)
  const [form, setForm]               = useState<any>(emptyForm)
  const [toast, setToast]             = useState('')
  const [detailUser, setDetailUser]   = useState<any>(null)
  const [detailTab, setDetailTab]     = useState<'profile' | 'access' | 'activity'>('profile')
  const [editingDetail, setEditingDetail] = useState(false)

  const flash    = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3500) }
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users', tenantId] })

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users', tenantId],
    queryFn:  () => getUsers(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: branches = [] } = useQuery({
    queryKey: ['branches', tenantId],
    queryFn:  () => getBranches(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: roles = [] } = useQuery({
    queryKey: ['roles', tenantId],
    queryFn:  () => getRoles(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
    staleTime: 0,            // always refetch — roles must reflect any additions from Roles & Permissions
    refetchOnWindowFocus: true,
  })

  // Per-user detail queries (only when detail panel is open)
  const { data: userActivity = [], isFetching: activityLoading } = useQuery({
    queryKey: ['user-activity', tenantId, detailUser?.id],
    queryFn:  () => getUserActivity(tenantId, detailUser.id).then(r => r.data || []),
    enabled:  !!tenantId && !!detailUser && detailTab === 'activity',
  })
  const { data: userPermissions = [], isFetching: permLoading } = useQuery({
    queryKey: ['user-permissions', tenantId, detailUser?.id],
    queryFn:  () => getUserPermissions(tenantId, detailUser.id).then(r => r.data || []),
    enabled:  !!tenantId && !!detailUser && detailTab === 'access',
  })

  // ── Mutations ──────────────────────────────────────────────────────────────
  const saveMut = useMutation({
    mutationFn: (payload: any) =>
      editing ? updateUser(tenantId, editing.id, payload) : createUser(tenantId, payload),
    onSuccess: (res) => {
      invalidate()
      setSlideOpen(false)
      flash(editing ? 'User updated.' : 'User created — credentials email sent.')
      // Refresh detail panel if editing the currently viewed user
      if (editing && detailUser?.id === editing.id) setDetailUser(res.data)
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to save user.'),
  })

  const deleteMut = useMutation({
    mutationFn: (id: any) => deleteUser(tenantId, id),
    onSuccess: () => { invalidate(); setDetailUser(null); flash('User deleted.') },
    onError: ()    => flash('Cannot delete this user.'),
  })

  const activateMut = useMutation({
    mutationFn: (id: string) => activateUser(tenantId, id),
    onSuccess: (res) => {
      invalidate()
      if (detailUser?.id === res.data?.id) setDetailUser(res.data)
      flash('User activated.')
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to activate user.'),
  })

  const deactivateMut = useMutation({
    mutationFn: (id: string) => deactivateUser(tenantId, id),
    onSuccess: (res) => {
      invalidate()
      if (detailUser?.id === res.data?.id) setDetailUser(res.data)
      flash('User deactivated.')
    },
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to deactivate user.'),
  })

  const resendMut = useMutation({
    mutationFn: (id: string) => resendInvitation(tenantId, id),
    onSuccess: () => flash('Invitation email resent.'),
    onError: (err: any) => flash(err?.response?.data?.detail || 'Failed to resend invitation.'),
  })

  // ── Open add/edit slide-over ───────────────────────────────────────────────
  const openNew  = () => { setEditing(null); setForm(emptyForm); setSlideOpen(true) }
  const openEdit = async (u: any) => {
    const preselected: number[] = (u.role_ids && u.role_ids.length > 0)
      ? u.role_ids
      : (() => {
          const m = roles.find((r: any) => r.role_name?.trim().toLowerCase() === (u.job_title || '').trim().toLowerCase())
          return m ? [m.role_id] : []
        })()
    setEditing(u)
    setForm({
      ...emptyForm, ...u, password: '', branch_id: u.branch_id || '',
      phone: u.mobile || u.phone || '',
      job_title: u.job_title || '',
      selected_role_ids: preselected,
    })
    setSlideOpen(true)
    if (!u.role_ids || u.role_ids.length === 0) {
      try {
        const res = await getUserRoles(tenantId, u.id)
        const roleIds = (res.data || []).map((r: any) => r.role_id)
        if (roleIds.length > 0) setForm((prev: any) => ({ ...prev, selected_role_ids: roleIds }))
      } catch { /* fallback already set */ }
    }
  }

  // ── Open user detail panel ─────────────────────────────────────────────────
  const openDetail = (u: any, tab: 'profile' | 'access' | 'activity' = 'profile') => {
    setDetailUser(u)
    setDetailTab(tab)
    setEditingDetail(false)
  }

  // ── Filtered stats ─────────────────────────────────────────────────────────
  const totalUsers    = users.length
  const activeUsers   = users.filter((u: any) => u.is_active !== false).length
  const inactiveUsers = totalUsers - activeUsers
  const roleOptions   = roles.length > 0
    ? roles.map((r: any) => r.role_name)
    : [...new Set(users.map((u: any) => u.job_title).filter(Boolean))] as string[]

  const filtered = users.filter((u: any) => {
    const name = `${u.first_name} ${u.last_name}`.toLowerCase()
    const matchSearch = !search || name.includes(search.toLowerCase()) || (u.email || '').toLowerCase().includes(search.toLowerCase())
    const matchRole   = !roleFilter || (u.role_names || []).includes(roleFilter) || (u.job_title || '') === roleFilter
    const matchStatus = !statusFilter || (statusFilter === 'active' ? u.is_active !== false : u.is_active === false)
    return matchSearch && matchRole && matchStatus
  })

  // ── Permission groups for access tab ──────────────────────────────────────
  const permByCategory = (perms: any[]) => {
    const map: Record<string, string[]> = {}
    for (const p of perms) {
      const cat = p.category || p.resource || 'General'
      if (!map[cat]) map[cat] = []
      map[cat].push(p.permission_name || p.action || p)
    }
    return map
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <Layout title="Users">
      <div className="space-y-5 animate-fade-in">

        {/* Toast */}
        {toast && (
          <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />{toast}
          </div>
        )}

        {/* Page header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Users</h1>
            <p className="text-sm text-slate-400 mt-0.5">Manage staff and users in your organisation</p>
          </div>
          {can('users:create') && (
            <button
              onClick={openNew}
              className="flex items-center gap-1.5 h-9 px-4 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg transition-colors"
            >
              <Plus className="h-3.5 w-3.5" /> Add user
            </button>
          )}
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total Users',  value: totalUsers,    sub: 'In your organisation', color: 'text-slate-800' },
            { label: 'Active',       value: activeUsers,   sub: 'Currently active',     color: 'text-emerald-600' },
            { label: 'Inactive',     value: inactiveUsers, sub: 'Deactivated',           color: 'text-slate-400' },
          ].map(c => (
            <div key={c.label} className="border border-slate-200 rounded-xl p-4 bg-white">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">{c.label}</p>
              <p className={`text-2xl font-bold leading-none ${c.color}`}>{c.value}</p>
              <p className="text-xs text-slate-400 mt-1.5">{c.sub}</p>
            </div>
          ))}
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 border border-slate-200 rounded-lg px-3 h-9 bg-white">
            <svg width="13" height="13" fill="none" stroke="#94a3b8" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              type="text"
              placeholder="Search users…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="border-none outline-none text-xs bg-transparent text-slate-700 w-36 placeholder:text-slate-400"
            />
          </div>
          <select
            value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
            className="h-9 px-3 pr-7 border border-slate-200 rounded-lg bg-white text-xs text-slate-600 outline-none appearance-none"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
          >
            <option value="">All roles</option>
            {roleOptions.map(r => <option key={r}>{r}</option>)}
          </select>
          <select
            value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="h-9 px-3 pr-7 border border-slate-200 rounded-lg bg-white text-xs text-slate-600 outline-none appearance-none"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {/* Table */}
        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
          <table className="w-full text-sm border-collapse" style={{ tableLayout: 'fixed' }}>
            <colgroup>
              <col style={{ width: '25%' }} /><col style={{ width: '17%' }} />
              <col style={{ width: '20%' }} /><col style={{ width: '13%' }} />
              <col style={{ width: '11%' }} /><col style={{ width: '14%' }} />
            </colgroup>
            <thead className="bg-slate-50">
              <tr>
                {['Name', 'Role', 'Email', 'Phone', 'Status', 'Actions'].map((h, i) => (
                  <th key={i} className={`text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 py-3 border-b border-slate-200 ${i === 5 ? 'text-center' : ''}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="py-8 text-center text-slate-400 text-sm">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center">
                    <p className="text-slate-400 text-sm mb-1">{search || roleFilter || statusFilter ? 'No users match your filters.' : 'No users yet.'}</p>
                    {!search && !roleFilter && !statusFilter && can('users:create') && (
                      <button onClick={openNew} className="text-purple-700 text-xs font-medium hover:underline">Add your first user</button>
                    )}
                  </td>
                </tr>
              ) : filtered.map((u: any) => {
                const initials = `${(u.first_name || '')[0] || ''}${(u.last_name || '')[0] || ''}`.toUpperCase()
                const col      = getColor(u.first_name || 'A')
                const isActive = u.is_active !== false
                const branch   = branches.find((b: any) => b.id === u.branch_id)
                const isSelf   = currentUser?.user_id === u.id
                return (
                  <tr key={u.id} className="hover:bg-slate-50 border-t border-slate-100 first:border-t-0">
                    <td className="px-4 py-3">
                      <button
                        onClick={() => openDetail(u)}
                        className="flex items-center gap-2.5 text-left hover:opacity-80 transition-opacity"
                      >
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0" style={{ background: col.bg, color: col.text }}>{initials}</div>
                        <div>
                          <p className="text-sm font-medium text-slate-800 leading-none flex items-center gap-1">
                            {u.first_name} {u.last_name}
                            {u.is_tenant_admin && <span className="text-[9px] px-1.5 py-0.5 rounded-sm bg-purple-100 text-purple-700 font-bold uppercase">Admin</span>}
                            {u.staff_id && <span className="text-[9px] px-1.5 py-0.5 rounded-sm bg-emerald-100 text-emerald-700 font-bold uppercase">Staff</span>}
                          </p>
                          <p className="text-[11px] text-slate-400 mt-0.5">{u.job_title || branch?.branch_name || ''}</p>
                        </div>
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      {(u.role_names && u.role_names.length > 0) ? (
                        <div className="flex flex-wrap gap-1">
                          {u.role_names.slice(0, 2).map((rn: string) => (
                            <span key={rn} className="inline-block text-[11px] px-2.5 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-500 font-medium">{rn}</span>
                          ))}
                          {u.role_names.length > 2 && <span className="text-[11px] text-slate-400">+{u.role_names.length - 2}</span>}
                        </div>
                      ) : u.job_title ? (
                        <span className="inline-block text-[11px] px-2.5 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-500 font-medium">{u.job_title}</span>
                      ) : <span className="text-slate-300 text-xs">—</span>}
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
                        {/* Edit */}
                        {can('users:edit') && (
                          <button
                            onClick={() => openEdit(u)}
                            className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-purple-700 hover:border-purple-200 hover:bg-purple-50 transition-colors"
                            title="Edit profile"
                          >
                            <Edit2 className="h-3 w-3" />
                          </button>
                        )}
                        {/* Activate / Deactivate */}
                        {can('users:edit') && !isSelf && (isActive ? (
                          <button
                            onClick={() => { if (confirm(`Deactivate ${u.first_name} ${u.last_name}? They will no longer be able to log in.`)) deactivateMut.mutate(u.id) }}
                            className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-amber-600 hover:border-amber-200 hover:bg-amber-50 transition-colors"
                            title="Deactivate"
                            disabled={deactivateMut.isPending}
                          >
                            <PowerOff className="h-3 w-3" />
                          </button>
                        ) : (
                          <button
                            onClick={() => activateMut.mutate(u.id)}
                            className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-emerald-600 hover:border-emerald-200 hover:bg-emerald-50 transition-colors"
                            title="Activate"
                            disabled={activateMut.isPending}
                          >
                            <Power className="h-3 w-3" />
                          </button>
                        ))}
                        {/* Resend invitation */}
                        {can('users:create') && (
                          <button
                            onClick={() => { if (confirm(`Resend credentials to ${u.email}? A new temporary password will be generated.`)) resendMut.mutate(u.id) }}
                            className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50 transition-colors"
                            title="Resend credentials"
                            disabled={resendMut.isPending}
                          >
                            <Send className="h-3 w-3" />
                          </button>
                        )}
                        {/* Delete */}
                        {can('users:delete') && !isSelf && (
                          <button
                            onClick={() => { if (confirm(`Delete ${u.first_name} ${u.last_name}? This action cannot be undone.`)) deleteMut.mutate(u.id) }}
                            className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

      </div>

      {/* ── USER DETAIL PANEL ────────────────────────────────────────────────── */}
      <SlideOver
        open={!!detailUser}
        onClose={() => { setDetailUser(null); setEditingDetail(false) }}
        title={detailUser ? `${detailUser.first_name} ${detailUser.last_name}` : ''}
        subtitle={detailUser?.email || ''}
      >
        {detailUser && (() => {
          const col      = getColor(detailUser.first_name || 'A')
          const initials = `${(detailUser.first_name || '')[0] || ''}${(detailUser.last_name || '')[0] || ''}`.toUpperCase()
          const isActive = detailUser.is_active !== false
          const branch   = branches.find((b: any) => b.id === detailUser.branch_id)
          const isSelf   = currentUser?.user_id === detailUser.id

          return (
            <div className="space-y-5">
              {/* Avatar + status header */}
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold flex-shrink-0" style={{ background: col.bg, color: col.text }}>{initials}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-800">{detailUser.first_name} {detailUser.last_name}</h3>
                    {detailUser.is_tenant_admin && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-bold uppercase">Admin</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{detailUser.job_title || 'No job title'}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${isActive ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                      {isActive ? 'Active' : 'Inactive'}
                    </span>
                    {detailUser.must_change_password && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border bg-amber-50 text-amber-700 border-amber-200">
                        Must change password
                      </span>
                    )}
                  </div>
                </div>
                {/* Quick actions */}
                <div className="flex flex-col gap-1.5">
                  {can('users:edit') && (
                    <button
                      onClick={() => openEdit(detailUser)}
                      className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-purple-700 transition-colors"
                    >
                      <Edit2 className="h-3 w-3" /> Edit
                    </button>
                  )}
                  {can('users:edit') && !isSelf && (isActive ? (
                    <button
                      onClick={() => { if (confirm(`Deactivate ${detailUser.first_name}?`)) deactivateMut.mutate(detailUser.id) }}
                      className="flex items-center gap-1 text-[11px] font-medium text-amber-600 hover:text-amber-800 transition-colors"
                    >
                      <PowerOff className="h-3 w-3" /> Deactivate
                    </button>
                  ) : (
                    <button
                      onClick={() => activateMut.mutate(detailUser.id)}
                      className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 hover:text-emerald-800 transition-colors"
                    >
                      <Power className="h-3 w-3" /> Activate
                    </button>
                  ))}
                  {can('users:create') && (
                    <button
                      onClick={() => { if (confirm(`Resend credentials to ${detailUser.email}?`)) resendMut.mutate(detailUser.id) }}
                      className="flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <Mail className="h-3 w-3" /> Resend invite
                    </button>
                  )}
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b border-slate-200">
                <div className="flex gap-0">
                  {(['profile', 'access', 'activity'] as const).map(tab => {
                    const icons = { profile: User, access: Shield, activity: Activity }
                    const Icon = icons[tab]
                    return (
                      <button
                        key={tab}
                        onClick={() => setDetailTab(tab)}
                        className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold border-b-2 capitalize transition-colors ${
                          detailTab === tab
                            ? 'border-purple-700 text-purple-700'
                            : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        <Icon className="h-3.5 w-3.5" />
                        {tab}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* ── Profile Tab ──────────────────────────────────────────── */}
              {detailTab === 'profile' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="First name"  value={detailUser.first_name} />
                    <Field label="Last name"   value={detailUser.last_name} />
                    <Field label="Email"       value={detailUser.email} />
                    <Field label="Phone"       value={detailUser.mobile || detailUser.phone} />
                    <Field label="Job title"   value={detailUser.job_title} />
                    <Field label="Branch"      value={branch?.branch_name} />
                  </div>
                  <div className="border-t border-slate-100 pt-3 grid grid-cols-2 gap-3">
                    <Field label="Created"       value={fmtDate(detailUser.created_at)} />
                    <Field label="Last login"    value={fmtDate(detailUser.last_login_at)} />
                    <Field label="Password set"  value={fmtDate(detailUser.password_changed_at)} />
                    <Field label="Account ID"    value={detailUser.id?.slice(0, 8) + '…'} />
                  </div>
                  {/* Staff record link */}
                  {detailUser.staff_id && (
                    <div className="border border-purple-100 bg-purple-50 rounded-lg p-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-purple-200 flex items-center justify-center">
                          <User className="h-3 w-3 text-purple-700" />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-purple-800">Staff member</p>
                          <p className="text-[11px] text-purple-600">Linked to a staff profile</p>
                        </div>
                      </div>
                      <a
                        href={`/staff?id=${detailUser.staff_id}`}
                        className="flex items-center gap-1 text-[11px] text-purple-700 font-medium hover:underline"
                      >
                        View staff record <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  )}
                  {can('users:edit') && (
                    <div className="pt-1">
                      <button
                        onClick={() => openEdit(detailUser)}
                        className="flex items-center gap-1.5 h-8 px-3 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                      >
                        <Edit2 className="h-3 w-3" /> Edit profile
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* ── Access Tab ───────────────────────────────────────────── */}
              {detailTab === 'access' && (
                <div className="space-y-4">
                  {/* Roles */}
                  <div>
                    <p className={secLbl}>Assigned roles</p>
                    {detailUser.role_names && detailUser.role_names.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {detailUser.role_names.map((rn: string) => (
                          <span key={rn} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-purple-200 bg-purple-50 text-purple-700 font-medium">
                            <Shield className="h-3 w-3" />{rn}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No roles assigned</p>
                    )}
                    {detailUser.is_tenant_admin && (
                      <p className="text-xs text-purple-700 font-medium mt-2 flex items-center gap-1">
                        <Shield className="h-3.5 w-3.5" /> Tenant Administrator — full platform access
                      </p>
                    )}
                  </div>

                  {/* Branch */}
                  <div>
                    <p className={secLbl}>Home branch</p>
                    {branch ? (
                      <div className="flex items-center gap-2 p-2 border border-slate-200 rounded-lg bg-slate-50">
                        <Building2 className="h-4 w-4 text-slate-400 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-slate-700">{branch.branch_name}</p>
                          {branch.suburb && <p className="text-xs text-slate-400">{branch.suburb}{branch.state ? `, ${branch.state}` : ''}</p>}
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No branch assigned</p>
                    )}
                  </div>

                  {/* Effective permissions */}
                  <div>
                    <p className={secLbl}>Effective permissions</p>
                    {permLoading ? (
                      <p className="text-xs text-slate-400">Loading permissions…</p>
                    ) : userPermissions.length === 0 ? (
                      <p className="text-xs text-slate-400">No permissions via assigned roles</p>
                    ) : (
                      <div className="space-y-2">
                        {Object.entries(permByCategory(userPermissions)).map(([cat, perms]) => (
                          <div key={cat}>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">{cat}</p>
                            <div className="flex flex-wrap gap-1">
                              {(perms as string[]).map(p => (
                                <span key={p} className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600">{p}</span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Cross-branch access link */}
                  <div>
                    <p className={secLbl}>Cross-branch access</p>
                    <button
                      onClick={() => navigate('/cross-branch-access')}
                      className="flex items-center gap-1.5 text-xs text-purple-700 hover:text-purple-900 font-medium"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      View cross-branch access records
                    </button>
                  </div>

                  {/* Manage roles button */}
                  {can('users:edit') && (
                    <div className="pt-1">
                      <button
                        onClick={() => openEdit(detailUser)}
                        className="flex items-center gap-1.5 h-8 px-3 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                      >
                        <Shield className="h-3 w-3" /> Manage roles & access
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* ── Activity Tab ─────────────────────────────────────────── */}
              {detailTab === 'activity' && (
                <div className="space-y-3">
                  {activityLoading ? (
                    <p className="text-xs text-slate-400">Loading activity…</p>
                  ) : userActivity.length === 0 ? (
                    <p className="text-xs text-slate-400">No activity recorded for this user.</p>
                  ) : (
                    <div className="space-y-2">
                      {(userActivity as any[]).map((entry: any) => (
                        <div key={entry.audit_id} className="flex items-start gap-3 p-3 border border-slate-100 rounded-lg bg-slate-50">
                          <div className="w-1.5 h-1.5 mt-1.5 rounded-full bg-purple-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-slate-700">
                              {ACTION_LABELS[entry.action] || entry.action}
                            </p>
                            <p className="text-[11px] text-slate-400 mt-0.5">{fmtDate(entry.created_at)}</p>
                            {entry.ip_address && <p className="text-[10px] text-slate-300 mt-0.5">IP: {entry.ip_address}</p>}
                          </div>
                          <ChevronRight className="h-3.5 w-3.5 text-slate-300 flex-shrink-0 mt-0.5" />
                        </div>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => navigate('/activity')}
                    className="flex items-center gap-1.5 text-xs text-purple-700 hover:text-purple-900 font-medium"
                  >
                    <ExternalLink className="h-3.5 w-3.5" /> View full activity log
                  </button>
                </div>
              )}

            </div>
          )
        })()}
      </SlideOver>

      {/* ── ADD / EDIT USER FORM ─────────────────────────────────────────────── */}
      <SlideOver
        open={slideOpen}
        onClose={() => setSlideOpen(false)}
        title={editing ? 'Edit user' : 'Add user'}
        subtitle={editing ? `${editing.first_name} ${editing.last_name}` : 'Fill in the details below'}
      >
        <div className="space-y-5">

          {/* Personal details */}
          <div>
            <p className={secLbl}>Personal details</p>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className={labelCls}>First name <span className="text-red-500">*</span></label>
                  <input className={inputCls} value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} placeholder="First name" />
                </div>
                <div className="space-y-1.5">
                  <label className={labelCls}>Last name</label>
                  <input className={inputCls} value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} placeholder="Last name" />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className={labelCls}>Email <span className="text-red-500">*</span></label>
                <input className={inputCls} type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="e.g. john@organisation.com.au" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className={labelCls}>Phone</label>
                  <input className={inputCls} value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="e.g. 0412 345 678" />
                </div>
                <div className="space-y-1.5">
                  <label className={labelCls}>Job title</label>
                  <input className={inputCls} value={form.job_title} onChange={e => setForm({ ...form, job_title: e.target.value })} placeholder="e.g. Support Worker" />
                </div>
              </div>
            </div>
          </div>

          {/* Access & role */}
          <div>
            <p className={secLbl}>Access &amp; role</p>
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label className={labelCls}>Branch {!editing && <span className="text-red-500">*</span>}</label>
                <select className={selectCls} value={form.branch_id} onChange={e => setForm({ ...form, branch_id: e.target.value })}>
                  <option value="">Select a branch…</option>
                  {branches.map((b: any) => <option key={b.id} value={b.id}>{b.branch_name}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={labelCls}>
                  Roles {form.selected_role_ids.length > 0 && <span className="text-purple-600 font-semibold">({form.selected_role_ids.length} selected)</span>}
                </label>
                <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-44 overflow-y-auto">
                  {roles.length === 0 && <p className="px-3 py-2 text-xs text-slate-400">No roles found</p>}
                  {roles.map((r: any) => (
                    <label key={r.role_id} className="flex items-center gap-2.5 px-3 py-2 cursor-pointer hover:bg-slate-50">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300 accent-purple-700"
                        checked={form.selected_role_ids.includes(r.role_id)}
                        onChange={e => {
                          const ids = e.target.checked
                            ? [...form.selected_role_ids, r.role_id]
                            : form.selected_role_ids.filter((id: number) => id !== r.role_id)
                          setForm({ ...form, selected_role_ids: ids })
                        }}
                      />
                      <div>
                        <span className="text-sm text-slate-700">{r.role_name}</span>
                        {r.description && <p className="text-[11px] text-slate-400 leading-tight">{r.description}</p>}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2 pt-0.5">
                <input
                  type="checkbox" id="admin-chk"
                  checked={form.is_tenant_admin}
                  onChange={e => setForm({ ...form, is_tenant_admin: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-300 text-purple-600"
                />
                <label htmlFor="admin-chk" className="text-sm text-slate-700">Tenant administrator</label>
              </div>
            </div>
          </div>

          {/* Status (edit mode only) */}
          {editing && (
            <div>
              <p className={secLbl}>Status</p>
              <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5">
                <div>
                  <span className="text-sm text-slate-700">Active</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">Inactive users cannot log in</p>
                </div>
                <button
                  type="button"
                  onClick={() => setForm({ ...form, is_active: !form.is_active })}
                  className={`relative w-9 h-5 rounded-full transition-colors flex-shrink-0 ${form.is_active ? 'bg-purple-700' : 'bg-slate-300'}`}
                >
                  <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${form.is_active ? 'right-0.5' : 'left-0.5'}`} />
                </button>
              </div>
            </div>
          )}

          {/* Info banner for new users */}
          {!editing && (
            <div className="flex items-start gap-2.5 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2.5">
              <Mail className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-700">A temporary password will be generated and emailed to the user. They will be asked to set a new password on first login.</p>
            </div>
          )}

          {/* Footer */}
          <div className="flex gap-3 pt-2 border-t border-slate-100">
            <button onClick={() => setSlideOpen(false)} className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
              Cancel
            </button>
            <button
              disabled={!form.first_name || !form.email || (!editing && !form.branch_id) || saveMut.isPending}
              onClick={() => saveMut.mutate({
                first_name: form.first_name,
                last_name:  form.last_name,
                email:      form.email,
                phone:      form.phone || undefined,
                job_title:  form.job_title || undefined,
                role_ids:   form.selected_role_ids.length > 0 ? form.selected_role_ids : undefined,
                branch_id:  form.branch_id ? parseInt(form.branch_id) : undefined,
                is_tenant_admin: form.is_tenant_admin,
                is_active:  form.is_active,
              })}
              className="flex-1 flex items-center justify-center gap-2 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {saveMut.isPending && <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
              {saveMut.isPending ? 'Saving…' : editing ? 'Save changes' : 'Add user'}
            </button>
          </div>

        </div>
      </SlideOver>

    </Layout>
  )
}

// ── Inline field display helper ───────────────────────────────────────────────
function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">{label}</p>
      <p className="text-sm text-slate-700">{value || <span className="text-slate-300">—</span>}</p>
    </div>
  )
}
