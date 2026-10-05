import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { useAuth } from '@/context/AuthContext'
import { getAuditLogs } from '@/api/tenant'
import { Activity as ActivityIcon } from 'lucide-react'

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-AU', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true,
  })
}

function getTitle(action: string, table: string) {
  const entity = table.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  if (action === 'CREATE') return `${entity} Created`
  if (action === 'DELETE') return `${entity} Deleted`
  return `${entity} Updated`
}

function getDescription(log: any): string {
  try {
    const oldV = log.old_values ? JSON.parse(log.old_values) : null
    const newV = log.new_values ? JSON.parse(log.new_values) : null
    const skip = ['updated_at', 'updated_by', 'created_at', 'created_by']

    if (log.action === 'CREATE' && newV) {
      const fields = Object.keys(newV).filter(k => !skip.includes(k) && newV[k] != null)
      if (fields.length) return `Created with ${fields.map(k => k.replace(/_/g, ' ')).join(', ')}.`
    }
    if (log.action === 'DELETE') return 'Record was permanently deleted.'
    if (newV && oldV) {
      const changed = Object.keys(newV).filter(k =>
        !skip.includes(k) && String(newV[k]) !== String(oldV[k])
      )
      if (changed.length) {
        return changed.map(k =>
          `${k.replace(/_/g, ' ')} changed from "${oldV[k] ?? '(empty)'}" to "${newV[k] ?? '(empty)'}"`
        ).join('; ') + '.'
      }
    }
  } catch { /* ignore */ }
  return 'Record was modified.'
}

const ACTION_BADGE: Record<string, string> = {
  CREATE: 'bg-emerald-100 text-emerald-700',
  UPDATE: 'bg-purple-100 text-purple-700',
  DELETE: 'bg-red-100 text-red-600',
}

function resolveUsername(logUserId: string | null | undefined, currentUser: any): string {
  if (!logUserId) return 'System'
  if (currentUser?.user_id && logUserId === currentUser.user_id) {
    // Same person as the logged-in user — use the name shown in the top-right header
    const genericNames = ['admin', 'admin user', 'user']
    const fullName = currentUser.full_name?.trim()
    const emailUser = currentUser.email?.split('@')[0] || ''
    const isGeneric = !fullName || genericNames.includes(fullName.toLowerCase())
    return isGeneric ? emailUser : fullName
  }
  return logUserId  // fallback for other users (will be replaced by backend username when available)
}

export default function ActivityPage() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['audit-logs', tenantId],
    queryFn: () => getAuditLogs(tenantId, { limit: 500 }).then(r => r.data || []),
    enabled: !!tenantId,
  })

  return (
    <Layout title="Activity">
      <div className="space-y-4">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold" style={{ color: '#2D1B6B' }}>Activity Log</h2>
            <p className="text-xs mt-0.5" style={{ color: '#9B85D0' }}>All changes across your organisation</p>
          </div>
          {logs.length > 0 && (
            <span className="text-xs font-medium px-3 py-1 rounded-full" style={{ background: 'rgba(124,92,191,0.1)', color: '#7C5CBF' }}>
              {logs.length} {logs.length === 1 ? 'record' : 'records'}
            </span>
          )}
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="bg-white border border-slate-100 rounded-xl overflow-hidden animate-pulse">
            <div className="h-10 bg-slate-50 border-b border-slate-100" />
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex gap-4 px-4 py-3 border-b border-slate-50 last:border-0">
                <div className="h-3 bg-slate-100 rounded w-1/5" />
                <div className="h-3 bg-slate-100 rounded w-2/5" />
                <div className="h-3 bg-slate-100 rounded w-1/5" />
                <div className="h-3 bg-slate-100 rounded w-1/5" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && logs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="h-14 w-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'rgba(124,92,191,0.1)' }}>
              <ActivityIcon className="h-7 w-7" style={{ color: '#7C5CBF' }} />
            </div>
            <p className="text-sm font-semibold text-slate-700">No activity yet</p>
            <p className="text-xs text-slate-400 mt-1">Changes to your organisation will appear here.</p>
          </div>
        )}

        {/* Table */}
        {!isLoading && logs.length > 0 && (
          <div className="bg-white border border-slate-100 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-1/5">Title</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-2/5">Description</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-1/5">Created At</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-1/5">Created By</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log: any, idx: number) => {
                  const badgeCls = ACTION_BADGE[log.action] ?? ACTION_BADGE.UPDATE
                  return (
                    <tr
                      key={log.audit_id}
                      className={`border-b border-slate-50 last:border-0 transition-colors hover:bg-slate-50/60 ${idx % 2 === 0 ? '' : 'bg-slate-50/30'}`}
                    >
                      {/* Title */}
                      <td className="px-4 py-3 align-top">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs font-semibold text-slate-800 leading-snug">
                            {getTitle(log.action, log.table_name)}
                          </span>
                          <span className={`self-start text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${badgeCls}`}>
                            {log.action}
                          </span>
                        </div>
                      </td>

                      {/* Description */}
                      <td className="px-4 py-3 align-top">
                        <p className="text-xs text-slate-500 leading-relaxed">{getDescription(log)}</p>
                      </td>

                      {/* Created At */}
                      <td className="px-4 py-3 align-top">
                        <span className="text-xs text-slate-500 whitespace-nowrap">{formatDateTime(log.created_at)}</span>
                      </td>

                      {/* Created By */}
                      <td className="px-4 py-3 align-top">
                        <span className="text-xs font-medium text-slate-700">
                          {log.username || resolveUsername(log.user_id, user)}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
