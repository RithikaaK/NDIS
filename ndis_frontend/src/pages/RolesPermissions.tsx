import React, { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { SlideOver } from '@/components/ui/SlideOver'
import { useAuth } from '@/context/AuthContext'
import { usePermissions } from '@/hooks/usePermissions'
import {
  getRoles, createRole, updateRole, deleteRole,
  activateRole, deactivateRole, getRoleUsers,
  getPermissions, getRolePermissions, assignPermissions, revokePermission,
} from '@/api/roles'
import { getUsers, assignRole, removeRole } from '@/api/users'
import {
  Shield, Plus, Edit2, Trash2, Power, PowerOff,
  Users, Grid3X3, ChevronRight, Building2, ExternalLink,
  CheckCircle2, XCircle, Minus, Info,
} from 'lucide-react'

// ── Style helpers ─────────────────────────────────────────────────────────────
const inputCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls = "text-xs font-semibold text-slate-600 uppercase tracking-wide"
const secLbl   = "text-[10px] font-semibold text-slate-400 uppercase tracking-widest pb-2 border-b border-slate-100 mb-3"

const AVATAR_COLORS = [
  { bg: '#f3e8ff', text: '#6b21a8' }, { bg: '#e0f2fe', text: '#075985' },
  { bg: '#fef9c3', text: '#854d0e' }, { bg: '#fce7f3', text: '#9d174d' },
  { bg: '#ffedd5', text: '#9a3412' }, { bg: '#dcfce7', text: '#166534' },
  { bg: '#ffe4e6', text: '#9f1239' },
]

// ── Role icon helper ───────────────────────────────────────────────────────────
function roleIconConfig(name: string, idx: number) {
  const lc = name.toLowerCase()
  if (lc.includes('admin') || lc.includes('system'))
    return { bg: '#f3e8ff', stroke: '#7c3aed', icon: 'shield' }
  if (lc.includes('manager') || lc.includes('branch'))
    return { bg: '#ede9fe', stroke: '#7c3aed', icon: 'building' }
  if (lc.includes('coordinator') || lc.includes('coord'))
    return { bg: '#e0f2fe', stroke: '#075985', icon: 'users' }
  if (lc.includes('finance') || lc.includes('claims'))
    return { bg: '#fef9c3', stroke: '#854d0e', icon: 'briefcase' }
  if (lc.includes('compliance') || lc.includes('audit'))
    return { bg: '#ffedd5', stroke: '#9a3412', icon: 'star' }
  if (lc.includes('support') || lc.includes('worker') || lc.includes('health'))
    return { bg: '#dcfce7', stroke: '#166534', icon: 'user' }
  const palettes = [
    { bg: '#fef9c3', stroke: '#854d0e', icon: 'star' },
    { bg: '#ffedd5', stroke: '#9a3412', icon: 'briefcase' },
    { bg: '#ffe4e6', stroke: '#9f1239', icon: 'user' },
  ]
  return palettes[idx % palettes.length]
}

function RoleIcon({ type, bg, stroke, size = 36 }: { type: string; bg: string; stroke: string; size?: number }) {
  const paths: Record<string, React.ReactElement> = {
    shield:    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
    building:  <><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></>,
    users:     <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
    user:      <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    star:      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>,
    briefcase: <><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></>,
  }
  const s = Math.round(size * 0.5)
  return (
    <div style={{ background: bg, width: size, height: size, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <svg width={s} height={s} fill="none" stroke={stroke} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
        {paths[type] || paths.user}
      </svg>
    </div>
  )
}

// ── Module normalisation ──────────────────────────────────────────────────────
// Map every variant (singular, plural, snake_case) → canonical plural key
const MODULE_ALIAS: Record<string, string> = {
  branch: 'branches', program: 'programs', user: 'users',
  role: 'roles', permission: 'permissions', participant: 'participants',
  schedule: 'schedules', progress_note: 'progress_notes',
  incident: 'incidents', document: 'documents',
  plan: 'plans', report: 'reports',
  invoice: 'invoices', setting: 'settings',
  // already-canonical forms map to themselves (handled by the fallback below)
}

/** Normalise a raw module/resource string to a canonical key. */
function normaliseModule(raw: string | undefined | null): string {
  if (!raw) return 'general'
  const key = raw.toLowerCase().trim()
  return MODULE_ALIAS[key] ?? key
}

const MODULE_LABELS: Record<string, string> = {
  branches: 'Branches', programs: 'Programs', users: 'Users',
  roles: 'Roles', permissions: 'Permissions', participants: 'Participants',
  schedules: 'Schedules', progress_notes: 'Progress Notes',
  incidents: 'Incidents', documents: 'Documents',
  plans: 'Support Plans', reports: 'Reports',
  invoices: 'Invoices', settings: 'Settings', audit: 'Audit',
  general: 'General',
}
const ACTION_ORDER = ['view', 'create', 'edit', 'delete', 'assign', 'approve', 'export', 'submit']
const ACTION_SHORT: Record<string, string> = {
  view: 'V', create: 'C', edit: 'E', delete: 'D',
  assign: 'A', approve: 'AP', export: 'EX', submit: 'SB',
}

// ── Main component ─────────────────────────────────────────────────────────────
const emptyRole = { role_name: '', description: '' }

export default function RolesPermissions() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { can } = usePermissions()

  const [tab, setTab]                       = useState<'roles' | 'matrix' | 'assignment'>('roles')
  const [slideOpen, setSlideOpen]           = useState(false)
  const [permSlideOpen, setPermSlideOpen]   = useState(false)
  const [editing, setEditing]               = useState<any>(null)
  const [selectedRole, setSelectedRole]     = useState<any>(null)
  const [selectedPerms, setSelectedPerms]   = useState<any[]>([])
  const [form, setForm]                     = useState(emptyRole)
  const [toast, setToast]                   = useState('')
  const [deleteConfirm, setDeleteConfirm]   = useState<any>(null)
  const [matrixRole, setMatrixRole]         = useState<any>(null)   // role clicked in matrix → open perm slide-over
  const [assignTab, setAssignTab]           = useState<any>(null)   // selected role in User-Assignment tab

  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3500) }
  const inv   = () => qc.invalidateQueries({ queryKey: ['roles', tenantId] })

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: roles = [], isLoading } = useQuery({
    queryKey: ['roles', tenantId],
    queryFn:  () => getRoles(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: permissions = [] } = useQuery({
    queryKey: ['permissions', tenantId],
    queryFn:  () => getPermissions(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: users = [] } = useQuery({
    queryKey: ['users', tenantId],
    queryFn:  () => getUsers(tenantId).then((r: any) => r.data || []),
    enabled:  !!tenantId,
  })

  // Permission map: {roleId: Permission[]}
  const roleIds = roles.map((r: any) => r.id).join(',')
  const { data: rolePermsMap = {} } = useQuery({
    queryKey: ['role-perms-map', tenantId, roleIds],
    queryFn:  async () => {
      if (!roles.length) return {}
      const results = await Promise.all(
        roles.map((r: any) => getRolePermissions(tenantId, r.id).then((res: any) => [r.id, res.data || []]))
      )
      return Object.fromEntries(results) as Record<number, any[]>
    },
    enabled: !!tenantId && roles.length > 0,
  })

  // Users for the assignment tab's selected role
  const { data: assignRoleUsers = [], isFetching: assignLoading } = useQuery({
    queryKey: ['role-users', tenantId, assignTab?.id],
    queryFn:  () => getRoleUsers(tenantId, assignTab.id).then(r => r.data || []),
    enabled:  !!tenantId && !!assignTab && tab === 'assignment',
  })

  // ── Derived ────────────────────────────────────────────────────────────────
  const permGroups = useMemo<Record<string, any[]>>(() => {
    // Step 1: group by normalised module
    const raw: Record<string, any[]> = {}
    for (const p of permissions) {
      const key = normaliseModule(p.resource)
      if (!raw[key]) raw[key] = []
      raw[key].push(p)
    }
    // Step 2: per module, prefer new-style (contains ':') over old-style (ALL_CAPS_UNDERSCORE).
    // If a module has any colon-style perm, drop the underscore-only ones.
    const deduped: Record<string, any[]> = {}
    for (const [mod, perms] of Object.entries(raw)) {
      const hasNewStyle = perms.some((p: any) => (p.permission_name || '').includes(':'))
      deduped[mod] = hasNewStyle
        ? perms.filter((p: any) => (p.permission_name || '').includes(':'))
        : perms
    }
    return deduped
  }, [permissions])

  const groupNames  = Object.keys(permGroups)
  const activeRoles = roles.filter((r: any) => r.is_active !== false)
  const inactiveRoles = roles.filter((r: any) => r.is_active === false)

  function usersForRole(r: any) {
    const rn = r.role_name.trim().toLowerCase()
    return users.filter((u: any) => {
      if (u.role_names && u.role_names.length > 0)
        return u.role_names.some((n: string) => n.trim().toLowerCase() === rn)
      return u.job_title && u.job_title.trim().toLowerCase() === rn
    })
  }

  // ── Mutations ──────────────────────────────────────────────────────────────
  const saveMut = useMutation({
    mutationFn: (payload: any) => editing ? updateRole(tenantId, editing.id, payload) : createRole(tenantId, payload),
    onSuccess: () => { inv(); setSlideOpen(false); flash(editing ? 'Role updated.' : 'Role created.') },
    onError: () => flash('Failed to save role.'),
  })

  const deleteMut = useMutation({
    mutationFn: (rid: number) => deleteRole(tenantId, rid),
    onSuccess: () => { inv(); setDeleteConfirm(null); flash('Role deleted.') },
    onError: (e: any) => { setDeleteConfirm(null); flash(e?.response?.data?.detail || 'Failed to delete role.') },
  })

  const activateMut = useMutation({
    mutationFn: (rid: number) => activateRole(tenantId, rid),
    onSuccess: () => { inv(); flash('Role activated.') },
    onError: () => flash('Failed to activate role.'),
  })

  const deactivateMut = useMutation({
    mutationFn: (rid: number) => deactivateRole(tenantId, rid),
    onSuccess: () => { inv(); flash('Role deactivated.') },
    onError: (e: any) => flash(e?.response?.data?.detail || 'Failed to deactivate role.'),
  })

  const permMut = useMutation({
    mutationFn: async () => {
      if (!selectedRole) return
      const rid      = selectedRole.id
      const current  = rolePermsMap[rid] || []
      const currIds  = current.map((p: any) => p.id)
      const toAdd    = selectedPerms.filter(id => !currIds.includes(id))
      const toRemove = currIds.filter((id: any) => !selectedPerms.includes(id))
      await Promise.all([
        ...toAdd.map(pid => assignPermissions(tenantId, rid, [pid])),
        ...toRemove.map((pid: any) => revokePermission(tenantId, rid, pid)),
      ])
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['role-perms-map', tenantId, roleIds] })
      setPermSlideOpen(false)
      flash('Permissions updated.')
    },
    onError: () => flash('Failed to update permissions.'),
  })

  const removeRoleMut = useMutation({
    mutationFn: ({ uid, rid }: { uid: string; rid: number }) => removeRole(tenantId, uid, rid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users', tenantId] })
      qc.invalidateQueries({ queryKey: ['role-users', tenantId, assignTab?.id] })
      flash('Role removed from user.')
    },
    onError: () => flash('Failed to remove role.'),
  })

  // ── Handlers ───────────────────────────────────────────────────────────────
  const openNew  = () => { setEditing(null); setForm(emptyRole); setSlideOpen(true) }
  const openEdit = (r: any) => { setEditing(r); setForm({ role_name: r.role_name, description: r.description || '' }); setSlideOpen(true) }
  const openPerms = (r: any) => {
    setSelectedRole(r)
    setSelectedPerms((rolePermsMap[r.id] || []).map((p: any) => p.id))
    setPermSlideOpen(true)
  }
  const togglePerm = (id: any) =>
    setSelectedPerms(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])

  const initials = (u: any) => `${(u.first_name || '')[0] || ''}${(u.last_name || '')[0] || ''}`.toUpperCase()

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <Layout title="Roles & Permissions">
      {toast && (
        <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0" />{toast}
        </div>
      )}

      <div className="space-y-5 animate-fade-in">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Roles &amp; Permissions</h1>
            <p className="text-sm text-slate-400 mt-0.5">Define what each role can access and do in the system</p>
          </div>
          {can('roles:create') && (
            <button onClick={openNew}
              className="flex items-center gap-1.5 h-9 px-4 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg transition-colors">
              <Plus className="h-3.5 w-3.5" /> Add role
            </button>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Total Roles',       value: roles.length,                color: 'text-slate-800' },
            { label: 'Active Roles',      value: activeRoles.length,          color: 'text-emerald-600' },
            { label: 'Inactive Roles',    value: inactiveRoles.length,        color: 'text-slate-400' },
            { label: 'Permission Groups', value: groupNames.length || '—',    color: 'text-purple-700' },
          ].map(s => (
            <div key={s.label} className="border border-slate-200 rounded-xl p-4 bg-white">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">{s.label}</p>
              <p className={`text-2xl font-bold leading-none ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Tab bar */}
        <div className="border-b border-slate-200">
          <div className="flex">
            {([
              { id: 'roles',      label: 'Roles',              Icon: Shield },
              { id: 'matrix',     label: 'Permission Matrix',  Icon: Grid3X3 },
              { id: 'assignment', label: 'User Assignment',     Icon: Users },
            ] as const).map(({ id, label, Icon }) => (
              <button key={id} onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
                  tab === id ? 'border-purple-700 text-purple-700' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}>
                <Icon className="h-4 w-4" />{label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Tab: Roles ──────────────────────────────────────────────────── */}
        {tab === 'roles' && (
          <div>
            {isLoading ? (
              <div className="border border-slate-200 rounded-xl p-12 text-center text-slate-400 text-sm">Loading roles…</div>
            ) : roles.length === 0 ? (
              <div className="border border-slate-200 rounded-xl p-16 text-center">
                <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Shield className="h-6 w-6 text-purple-400" />
                </div>
                <p className="font-semibold text-slate-800 mb-1">No roles defined</p>
                <p className="text-sm text-slate-400 mb-4">Create roles to control what each team member can access.</p>
                {can('roles:create') && (
                  <button onClick={openNew} className="h-9 px-4 bg-purple-800 text-white text-sm font-medium rounded-lg hover:bg-purple-900">
                    Add first role
                  </button>
                )}
              </div>
            ) : (
              <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                <table className="w-full text-sm border-collapse" style={{ tableLayout: 'fixed' }}>
                  <colgroup>
                    <col style={{ width: '22%' }} /><col style={{ width: '28%' }} />
                    <col style={{ width: '20%' }} /><col style={{ width: '14%' }} />
                    <col style={{ width: '16%' }} />
                  </colgroup>
                  <thead className="bg-slate-50">
                    <tr>
                      {['Role', 'Permissions', 'Users', 'Status', 'Actions'].map((h, i) => (
                        <th key={h} className={`text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 py-3 border-b border-slate-200 ${i >= 3 ? 'text-center' : 'text-left'}`}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {roles.map((r: any, idx: number) => {
                      const cfg      = roleIconConfig(r.role_name, idx)
                      const rolePerms = rolePermsMap[r.id] || []
                      const modules  = [...new Set(rolePerms.map((p: any) => p.resource).filter(Boolean))]
                      const roleUsers = usersForRole(r)
                      const isActive = r.is_active !== false

                      return (
                        <tr key={r.id} className={`border-t border-slate-100 first:border-t-0 hover:bg-slate-50 ${!isActive ? 'opacity-60' : ''}`}>
                          {/* Role */}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2.5">
                              <RoleIcon type={cfg.icon} bg={cfg.bg} stroke={cfg.stroke} />
                              <div>
                                <p className="text-sm font-semibold text-slate-800">{r.role_name}</p>
                                <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{r.description || (r.is_system_role ? 'System role' : 'Custom role')}</p>
                              </div>
                            </div>
                          </td>
                          {/* Permissions summary */}
                          <td className="px-4 py-3">
                            {modules.length === 0 ? (
                              can('permissions:assign')
                                ? <button onClick={() => openPerms(r)} className="text-xs text-purple-700 underline">Assign permissions</button>
                                : <span className="text-xs text-slate-300">No permissions</span>
                            ) : (
                              <div className="flex flex-wrap gap-1">
                                {modules.slice(0, 4).map(m => (
                                  <span key={m} className="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-100 font-medium">
                                    {MODULE_LABELS[m] || m}
                                  </span>
                                ))}
                                {modules.length > 4 && <span className="text-[10px] text-slate-400">+{modules.length - 4}</span>}
                              </div>
                            )}
                          </td>
                          {/* Users */}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              {roleUsers.slice(0, 5).map((u: any, ai: number) => {
                                const c = AVATAR_COLORS[ai % AVATAR_COLORS.length]
                                return (
                                  <div key={u.user_id || u.id} title={`${u.first_name} ${u.last_name}`}
                                    style={{ width: 24, height: 24, background: c.bg, color: c.text, marginLeft: ai > 0 ? -6 : 0, zIndex: 5 - ai }}
                                    className="rounded-full flex items-center justify-center text-[9px] font-bold border-2 border-white flex-shrink-0">
                                    {initials(u)}
                                  </div>
                                )
                              })}
                              {roleUsers.length > 5 && <span className="text-[11px] text-slate-400">+{roleUsers.length - 5}</span>}
                              {roleUsers.length > 0 && <span className="text-[11px] text-slate-500 ml-1">{roleUsers.length}</span>}
                              {roleUsers.length === 0 && <span className="text-slate-300 text-xs">—</span>}
                            </div>
                          </td>
                          {/* Status */}
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${isActive ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                              {isActive ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {/* Actions */}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 justify-center">
                              {/* Manage permissions */}
                              {can('permissions:assign') && (
                                <button onClick={() => openPerms(r)} title="Manage permissions"
                                  className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-purple-700 hover:border-purple-200 hover:bg-purple-50 transition-colors">
                                  <Shield className="h-3 w-3" />
                                </button>
                              )}
                              {/* Edit */}
                              {can('roles:edit') && (
                                <button onClick={() => openEdit(r)} title="Edit role"
                                  className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-purple-700 hover:border-purple-200 hover:bg-purple-50 transition-colors">
                                  <Edit2 className="h-3 w-3" />
                                </button>
                              )}
                              {/* Activate / Deactivate */}
                              {can('roles:edit') && !r.is_system_role && (isActive ? (
                                <button onClick={() => { if (confirm(`Deactivate role "${r.role_name}"?`)) deactivateMut.mutate(r.id) }}
                                  title="Deactivate" className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-amber-600 hover:border-amber-200 hover:bg-amber-50 transition-colors">
                                  <PowerOff className="h-3 w-3" />
                                </button>
                              ) : (
                                <button onClick={() => activateMut.mutate(r.id)}
                                  title="Activate" className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-emerald-600 hover:border-emerald-200 hover:bg-emerald-50 transition-colors">
                                  <Power className="h-3 w-3" />
                                </button>
                              ))}
                              {/* Delete */}
                              {can('roles:delete') && !r.is_system_role && (
                                <button onClick={() => setDeleteConfirm(r)} title="Delete role"
                                  className="w-7 h-7 flex items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors">
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
            )}

            {/* Location-based access info card */}
            <div className="border border-blue-200 rounded-xl p-4 bg-blue-50 flex items-start gap-3">
              <Info className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <span className="font-semibold">Location-Based Access Control</span> is managed through each user's assigned home branch and the Cross-Branch Access system.
                {' '}Users can only access data from their assigned branch unless explicitly granted cross-branch access.
                <button onClick={() => navigate('/cross-branch-access')} className="ml-1.5 underline font-medium text-blue-700 hover:text-blue-900">
                  Manage cross-branch access →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Tab: Permission Matrix ───────────────────────────────────────── */}
        {tab === 'matrix' && (
          <PermissionMatrix
            roles={roles}
            permissions={permissions}
            rolePermsMap={rolePermsMap}
            onEditPerms={openPerms}
          />
        )}

        {/* ── Tab: User Assignment ─────────────────────────────────────────── */}
        {tab === 'assignment' && (
          <div className="grid grid-cols-5 gap-4">
            {/* Role list sidebar */}
            <div className="col-span-2 border border-slate-200 rounded-xl overflow-hidden bg-white">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select a role</p>
              </div>
              <div className="divide-y divide-slate-100">
                {roles.map((r: any, idx: number) => {
                  const cfg = roleIconConfig(r.role_name, idx)
                  const cnt = usersForRole(r).length
                  return (
                    <button key={r.id} onClick={() => setAssignTab(r)}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                        assignTab?.id === r.id ? 'bg-purple-50' : 'hover:bg-slate-50'
                      }`}>
                      <RoleIcon type={cfg.icon} bg={cfg.bg} stroke={cfg.stroke} size={30} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${assignTab?.id === r.id ? 'text-purple-800' : 'text-slate-700'}`}>{r.role_name}</p>
                        <p className="text-[11px] text-slate-400">{cnt} user{cnt !== 1 ? 's' : ''}</p>
                      </div>
                      {assignTab?.id === r.id && <ChevronRight className="h-3.5 w-3.5 text-purple-500 flex-shrink-0" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Users panel */}
            <div className="col-span-3 border border-slate-200 rounded-xl overflow-hidden bg-white">
              {!assignTab ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                  <Users className="h-8 w-8 mb-2 opacity-30" />
                  <p className="text-sm">Select a role to view its users</p>
                </div>
              ) : (
                <>
                  <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{assignTab.role_name}</p>
                      <p className="text-[11px] text-slate-400">
                        {assignLoading ? 'Loading…' : `${assignRoleUsers.length} user${assignRoleUsers.length !== 1 ? 's' : ''} with this role`}
                      </p>
                    </div>
                    <button onClick={() => navigate('/users')}
                      className="flex items-center gap-1 text-xs text-purple-700 hover:text-purple-900 font-medium">
                      <ExternalLink className="h-3.5 w-3.5" /> Manage in Users
                    </button>
                  </div>

                  {assignLoading ? (
                    <div className="py-12 text-center text-slate-400 text-sm">Loading…</div>
                  ) : assignRoleUsers.length === 0 ? (
                    <div className="py-16 text-center">
                      <Users className="h-7 w-7 text-slate-300 mx-auto mb-2" />
                      <p className="text-sm text-slate-400">No users have this role yet.</p>
                      <button onClick={() => navigate('/users')} className="mt-2 text-xs text-purple-700 underline font-medium">
                        Assign from Users page →
                      </button>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {(assignRoleUsers as any[]).map((u: any) => {
                        const col = AVATAR_COLORS[(u.first_name || 'A').charCodeAt(0) % AVATAR_COLORS.length]
                        const inis = `${(u.first_name || '')[0] || ''}${(u.last_name || '')[0] || ''}`.toUpperCase()
                        return (
                          <div key={u.user_id} className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50">
                            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                              style={{ background: col.bg, color: col.text }}>{inis}</div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-800">{u.first_name} {u.last_name}</p>
                              <p className="text-[11px] text-slate-400 truncate">{u.email}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${u.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                              {can('roles:edit') && (
                                <button
                                  onClick={() => { if (confirm(`Remove ${u.first_name} ${u.last_name} from ${assignTab.role_name}?`)) removeRoleMut.mutate({ uid: u.user_id, rid: assignTab.id }) }}
                                  className="w-6 h-6 flex items-center justify-center rounded border border-slate-200 text-slate-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors"
                                  title="Remove from role">
                                  <XCircle className="h-3 w-3" />
                                </button>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

      </div>

      {/* ── Delete Confirm ───────────────────────────────────────────────────── */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-7 max-w-sm w-full shadow-2xl">
            <div className="w-11 h-11 bg-red-50 rounded-xl flex items-center justify-center mb-4">
              <Trash2 className="h-5 w-5 text-red-600" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1.5">Delete role?</h3>
            <p className="text-sm text-slate-500 mb-6">
              <strong>{deleteConfirm.role_name}</strong> will be permanently removed. Users with this role will lose the associated permissions.
            </p>
            <div className="flex gap-3">
              <button onClick={() => deleteMut.mutate(deleteConfirm.id)} disabled={deleteMut.isPending}
                className="flex-1 h-9 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors">
                {deleteMut.isPending ? 'Deleting…' : 'Delete'}
              </button>
              <button onClick={() => setDeleteConfirm(null)}
                className="flex-1 h-9 border border-slate-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Add / Edit Role ────────────────────────────────────────────────── */}
      <SlideOver open={slideOpen} onClose={() => setSlideOpen(false)}
        title={editing ? 'Edit Role' : 'Add Role'}
        subtitle={editing ? `Editing ${editing.role_name}` : 'Define a new access role'}>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Role name <span className="text-red-500">*</span></label>
            <input className={inputCls} value={form.role_name}
              onChange={e => setForm({ ...form, role_name: e.target.value })}
              placeholder="e.g. Support Worker" />
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Description</label>
            <textarea value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              rows={3} placeholder="Brief description of this role's responsibilities…"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white resize-none transition-all" />
          </div>
          {!editing && (
            <div className="flex items-start gap-2.5 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5">
              <Info className="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-slate-500">After creating the role, use the <strong>Manage Permissions</strong> button to assign what actions this role can perform.</p>
            </div>
          )}
          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <button onClick={() => setSlideOpen(false)}
              className="px-4 h-9 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
            <button onClick={() => saveMut.mutate(form)} disabled={saveMut.isPending || !form.role_name}
              className="flex-1 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {saveMut.isPending ? 'Saving…' : editing ? 'Update Role' : 'Add Role'}
            </button>
          </div>
        </div>
      </SlideOver>

      {/* ── Manage Permissions ────────────────────────────────────────────── */}
      <SlideOver open={permSlideOpen} onClose={() => setPermSlideOpen(false)}
        title="Manage Permissions"
        subtitle={`Role: ${selectedRole?.role_name}`}>
        <PermissionEditor
          permGroups={permGroups}
          selectedPerms={selectedPerms}
          onToggle={togglePerm}
          onGroupToggle={(ids, allOn) =>
            setSelectedPerms(prev =>
              allOn ? prev.filter(id => !ids.includes(id))
                    : [...new Set([...prev, ...ids])]
            )
          }
          onSelectAll={() => setSelectedPerms(Object.values(permGroups).flat().map((p: any) => p.id))}
          onClearAll={() => setSelectedPerms([])}
          onSave={() => permMut.mutate()}
          onCancel={() => setPermSlideOpen(false)}
          saving={permMut.isPending}
        />
      </SlideOver>
    </Layout>
  )
}

// ── Action chip styling ────────────────────────────────────────────────────────
const ACTION_CHIP: Record<string, { bg: string; border: string; text: string; activeBg: string; activeBorder: string; activeText: string; label: string }> = {
  view:    { bg: '#f0f9ff', border: '#bae6fd', text: '#0369a1', activeBg: '#0369a1', activeBorder: '#0369a1', activeText: '#fff', label: 'View'    },
  create:  { bg: '#f0fdf4', border: '#bbf7d0', text: '#15803d', activeBg: '#15803d', activeBorder: '#15803d', activeText: '#fff', label: 'Create'  },
  edit:    { bg: '#fffbeb', border: '#fde68a', text: '#b45309', activeBg: '#b45309', activeBorder: '#b45309', activeText: '#fff', label: 'Edit'    },
  delete:  { bg: '#fff1f2', border: '#fecdd3', text: '#be123c', activeBg: '#be123c', activeBorder: '#be123c', activeText: '#fff', label: 'Delete'  },
  assign:  { bg: '#faf5ff', border: '#e9d5ff', text: '#7c3aed', activeBg: '#7c3aed', activeBorder: '#7c3aed', activeText: '#fff', label: 'Assign'  },
  approve: { bg: '#fff7ed', border: '#fed7aa', text: '#c2410c', activeBg: '#c2410c', activeBorder: '#c2410c', activeText: '#fff', label: 'Approve' },
  export:  { bg: '#f0fdfa', border: '#99f6e4', text: '#0f766e', activeBg: '#0f766e', activeBorder: '#0f766e', activeText: '#fff', label: 'Export'  },
  submit:  { bg: '#fdf4ff', border: '#f0abfc', text: '#a21caf', activeBg: '#a21caf', activeBorder: '#a21caf', activeText: '#fff', label: 'Submit'  },
}
const DEFAULT_CHIP = { bg: '#f8fafc', border: '#e2e8f0', text: '#64748b', activeBg: '#475569', activeBorder: '#475569', activeText: '#fff', label: '' }

function getActionFromPerm(permName: string): string {
  if (!permName) return ''
  if (permName.includes(':')) return permName.split(':')[1].toLowerCase()
  // Handle RESOURCE_ACTION style — take the last segment
  const parts = permName.split('_')
  return parts[parts.length - 1].toLowerCase()
}

function getHumanLabel(permName: string, description?: string): string {
  if (description) return description
  const action = getActionFromPerm(permName)
  return action.charAt(0).toUpperCase() + action.slice(1)
}

// ── PermissionEditor ───────────────────────────────────────────────────────────
function PermissionEditor({
  permGroups, selectedPerms, onToggle, onGroupToggle,
  onSelectAll, onClearAll, onSave, onCancel, saving,
}: {
  permGroups: Record<string, any[]>
  selectedPerms: any[]
  onToggle: (id: any) => void
  onGroupToggle: (ids: any[], allOn: boolean) => void
  onSelectAll: () => void
  onClearAll: () => void
  onSave: () => void
  onCancel: () => void
  saving: boolean
}) {
  const groups   = Object.entries(permGroups)
  const totalAll = groups.reduce((n, [, p]) => n + p.length, 0)
  const totalSel = selectedPerms.length

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-400">
        <Shield className="h-8 w-8 opacity-30 mb-2" />
        <p className="text-sm">No permissions available yet.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header summary + global controls */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 flex-shrink-0">
        <p className="text-xs text-slate-500">
          <span className="font-bold text-slate-800">{totalSel}</span> of{' '}
          <span className="font-semibold">{totalAll}</span> permissions selected
        </p>
        <div className="flex items-center gap-3">
          <button onClick={onSelectAll} className="text-xs text-purple-700 hover:text-purple-900 font-semibold">
            Grant all
          </button>
          <span className="text-slate-200">|</span>
          <button onClick={onClearAll} className="text-xs text-slate-500 hover:text-slate-700 font-medium">
            Clear all
          </button>
        </div>
      </div>

      {/* Module cards */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-0.5">
        {groups.map(([group, perms]) => {
          const ids        = perms.map((p: any) => p.id)
          const selCount   = perms.filter((p: any) => selectedPerms.includes(p.id)).length
          const allOn      = selCount === perms.length
          const someOn     = selCount > 0 && selCount < perms.length

          return (
            <div key={group} className={`rounded-xl border transition-colors ${allOn ? 'border-purple-200 bg-purple-50/30' : someOn ? 'border-amber-200 bg-amber-50/20' : 'border-slate-200 bg-white'}`}>
              {/* Module header */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-inherit">
                <div className="flex items-center gap-2">
                  {/* Module checkbox */}
                  <button
                    onClick={() => onGroupToggle(ids, allOn)}
                    className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      allOn   ? 'bg-purple-700 border-purple-700' :
                      someOn  ? 'bg-amber-400 border-amber-400'   :
                                'bg-white border-slate-300'
                    }`}>
                    {allOn && (
                      <svg width={9} height={9} fill="none" stroke="#fff" strokeWidth={2.5} viewBox="0 0 12 12">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
                      </svg>
                    )}
                    {someOn && !allOn && <span className="w-1.5 h-0.5 bg-white rounded" />}
                  </button>
                  <p className="text-sm font-bold text-slate-700">
                    {MODULE_LABELS[group] || group.charAt(0).toUpperCase() + group.slice(1)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[11px] font-medium ${allOn ? 'text-purple-600' : someOn ? 'text-amber-600' : 'text-slate-400'}`}>
                    {selCount}/{perms.length}
                  </span>
                  <button
                    onClick={() => onGroupToggle(ids, allOn)}
                    className="text-[11px] text-purple-600 hover:text-purple-800 font-semibold underline-offset-2 hover:underline">
                    {allOn ? 'Remove all' : 'Grant all'}
                  </button>
                </div>
              </div>

              {/* Action chips */}
              <div className="px-4 py-3 flex flex-wrap gap-2">
                {perms.map((p: any) => {
                  const action  = getActionFromPerm(p.permission_name || '')
                  const chip    = ACTION_CHIP[action] || { ...DEFAULT_CHIP, label: action.charAt(0).toUpperCase() + action.slice(1) }
                  const on      = selectedPerms.includes(p.id)
                  const desc    = p.description || ''

                  return (
                    <button
                      key={p.id}
                      onClick={() => onToggle(p.id)}
                      title={desc}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all select-none"
                      style={on
                        ? { background: chip.activeBg, borderColor: chip.activeBorder, color: chip.activeText }
                        : { background: chip.bg, borderColor: chip.border, color: chip.text }
                      }>
                      {on && (
                        <svg width={10} height={10} fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 12 12">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
                        </svg>
                      )}
                      {chip.label || action}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 pt-3 mt-3 border-t border-slate-100 flex gap-3">
        <button onClick={onSave} disabled={saving}
          className="flex-1 h-9 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5">
          {saving ? 'Saving…' : `Save permissions (${totalSel} granted)`}
        </button>
        <button onClick={onCancel}
          className="px-4 h-9 border border-slate-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors">
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Permission Matrix component ────────────────────────────────────────────────
function PermissionMatrix({
  roles, permissions, rolePermsMap, onEditPerms,
}: {
  roles: any[]; permissions: any[]; rolePermsMap: Record<number, any[]>; onEditPerms: (r: any) => void;
}) {
  // Group permissions by module (normalised to prevent duplicates)
  const modules = useMemo(() => {
    const map: Record<string, { actions: string[]; perms: any[] }> = {}
    for (const p of permissions) {
      const mod = normaliseModule(p.resource)
      if (!map[mod]) map[mod] = { actions: [], perms: [] }
      const action = p.permission_name?.split(':')[1] || ''
      if (!map[mod].actions.includes(action)) map[mod].actions.push(action)
      map[mod].perms.push(p)
    }
    return map
  }, [permissions])

  const moduleList = Object.keys(modules)

  if (roles.length === 0 || moduleList.length === 0) {
    return (
      <div className="border border-slate-200 rounded-xl p-12 text-center text-slate-400 text-sm">
        No roles or permissions defined yet. Add roles and assign permissions first.
      </div>
    )
  }

  // Which permissions does each role have?
  const hasPermission = (roleId: number, permId: number) => {
    return (rolePermsMap[roleId] || []).some((p: any) => p.id === permId)
  }

  const cellStatus = (roleId: number, modPerms: any[]) => {
    const granted = modPerms.filter(p => hasPermission(roleId, p.id))
    if (granted.length === 0) return 'none'
    if (granted.length >= modPerms.length) return 'full'
    return 'partial'
  }

  const CELL_STYLE: Record<string, { bg: string; text: string; border: string }> = {
    full:    { bg: '#f0fdf4', text: '#15803d', border: '#bbf7d0' },
    partial: { bg: '#fefce8', text: '#a16207', border: '#fde68a' },
    none:    { bg: '#f8fafc', text: '#94a3b8', border: '#e2e8f0' },
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <p className="text-sm text-slate-500">A visual overview of which roles can access each module. Click a role header to manage its permissions.</p>
        <div className="flex items-center gap-3 ml-auto text-[11px]">
          {(['full', 'partial', 'none'] as const).map(s => (
            <span key={s} className="flex items-center gap-1">
              <span className="w-3 h-3 rounded border" style={{ background: CELL_STYLE[s].bg, borderColor: CELL_STYLE[s].border }} />
              <span className="text-slate-500 capitalize">{s === 'full' ? 'Full access' : s === 'partial' ? 'Partial' : 'No access'}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-auto bg-white">
        <table className="text-xs border-collapse min-w-full">
          <thead>
            <tr className="bg-slate-50">
              <th className="text-left px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-r border-slate-200 sticky left-0 bg-slate-50 z-10 min-w-[160px]">
                Module
              </th>
              {roles.map((r: any) => {
                const cfg = roleIconConfig(r.role_name, 0)
                return (
                  <th key={r.id} className="px-3 py-3 border-b border-l border-slate-200 min-w-[110px]">
                    <button onClick={() => onEditPerms(r)} className="flex flex-col items-center gap-1 w-full hover:opacity-70 transition-opacity" title={`Edit ${r.role_name} permissions`}>
                      <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: cfg.bg }}>
                        <Shield className="h-3.5 w-3.5" style={{ color: cfg.stroke }} />
                      </div>
                      <span className="text-[10px] font-semibold text-slate-700 text-center leading-tight line-clamp-2">{r.role_name}</span>
                      {!r.is_active && <span className="text-[9px] text-slate-400">(inactive)</span>}
                    </button>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {moduleList.map((mod, mi) => {
              const { perms } = modules[mod]
              return (
                <tr key={mod} className={mi % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                  <td className="px-4 py-3 border-r border-slate-200 sticky left-0 z-10 font-semibold text-slate-700"
                    style={{ background: mi % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                    <div className="flex flex-col">
                      <span>{MODULE_LABELS[mod] || mod}</span>
                      <div className="flex gap-0.5 mt-1 flex-wrap">
                        {perms.map(p => {
                          const action = p.permission_name?.split(':')[1]
                          return action ? (
                            <span key={p.id} className="text-[9px] px-1 rounded bg-slate-200 text-slate-500 font-mono uppercase">
                              {ACTION_SHORT[action] || action.slice(0, 2).toUpperCase()}
                            </span>
                          ) : null
                        })}
                      </div>
                    </div>
                  </td>
                  {roles.map((r: any) => {
                    const granted = perms.filter(p => hasPermission(r.id, p.id))
                    const status  = cellStatus(r.id, perms)
                    const s       = CELL_STYLE[status]
                    return (
                      <td key={r.id} className="px-2 py-2 border-l border-slate-200 text-center">
                        <button onClick={() => onEditPerms(r)}
                          className="w-full rounded-md py-1.5 px-1 transition-opacity hover:opacity-80"
                          style={{ background: s.bg, border: `1px solid ${s.border}` }}
                          title={`${r.role_name}: ${granted.length}/${perms.length} permissions in ${mod}`}>
                          {status === 'full' ? (
                            <CheckCircle2 className="h-3.5 w-3.5 mx-auto" style={{ color: s.text }} />
                          ) : status === 'partial' ? (
                            <span style={{ color: s.text, fontWeight: 600, fontSize: 10 }}>{granted.length}/{perms.length}</span>
                          ) : (
                            <Minus className="h-3.5 w-3.5 mx-auto" style={{ color: s.text }} />
                          )}
                        </button>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
