import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { useAuth } from '@/context/AuthContext'
import { getTenant } from '@/api/tenant'
import { getBranches } from '@/api/branches'
import { getPrograms } from '@/api/programs'
import { getUsers } from '@/api/users'
import { SkeletonDashboard } from '@/components/ui/Skeleton'
import {
  Building2, GitBranch, BookOpen, Users, ArrowUpRight,
  ArrowRight, TrendingUp, CheckCircle2, AlertCircle, Clock, Shield, AlertTriangle,
} from 'lucide-react'

function daysUntil(dateStr: string | null | undefined): number | null {
  if (!dateStr) return null
  const diff = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

const QUICK_ACTIONS = [
  { label: 'Add Branch',   icon: GitBranch, route: '/branches',     color: 'bg-purple-50 text-purple-600   border-purple-100' },
  { label: 'Add Program',  icon: BookOpen,  route: '/programs',     color: 'bg-purple-50 text-purple-600 border-purple-100' },
  { label: 'Add User',     icon: Users,     route: '/users',        color: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
  { label: 'View Org',     icon: Building2, route: '/organisation', color: 'bg-amber-50 text-amber-600  border-amber-100' },
]

const ACTIVITY = [
  { type: 'success', msg: 'New branch "Melbourne CBD" created',  time: '2 hours ago', icon: CheckCircle2 },
  { type: 'info',    msg: 'Program "Daily Activities" updated',   time: '5 hours ago', icon: BookOpen },
  { type: 'warning', msg: 'User licence limit at 80%',            time: '1 day ago',   icon: AlertCircle },
  { type: 'success', msg: 'Monthly compliance report generated',  time: '2 days ago',  icon: Shield },
  { type: 'info',    msg: 'Support worker John D. onboarded',     time: '3 days ago',  icon: Users },
]

const activityColor = {
  success: 'bg-emerald-100 text-emerald-600',
  info:    'bg-purple-100 text-purple-600',
  warning: 'bg-amber-100 text-amber-600',
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate  = useNavigate()
  const tenantId  = user?.tenant_id

  const { data: tenant }              = useQuery({ queryKey: ['tenant', tenantId],   queryFn: () => getTenant(tenantId).then(r => r.data),        enabled: !!tenantId })

  const expiryDays = daysUntil((tenant as any)?.registration_expiry_date)
  const { data: branches = [] }       = useQuery({ queryKey: ['branches', tenantId], queryFn: () => getBranches(tenantId).then(r => r.data || []), enabled: !!tenantId })
  const { data: programs = [] }       = useQuery({ queryKey: ['programs', tenantId], queryFn: () => getPrograms(tenantId).then(r => r.data || []), enabled: !!tenantId })
  const { data: users = [], isLoading } = useQuery({ queryKey: ['users', tenantId],  queryFn: () => getUsers(tenantId).then(r => r.data || []),    enabled: !!tenantId })

  const KPIs = [
    { label: 'Total Branches',  value: branches.length, icon: GitBranch, trend: '+2 this month', trendUp: true, gradient: 'from-purple-500 to-purple-700',    bg: 'bg-purple-50',   text: 'text-purple-600',   route: '/branches' },
    { label: 'Active Programs', value: programs.length, icon: BookOpen,  trend: '+1 this month', trendUp: true, gradient: 'from-purple-500 to-purple-700', bg: 'bg-purple-50', text: 'text-purple-600', route: '/programs' },
    { label: 'Total Users',     value: users.length,   icon: Users,     trend: '+3 this month', trendUp: true, gradient: 'from-emerald-500 to-emerald-700', bg: 'bg-emerald-50', text: 'text-emerald-600', route: '/users' },
    { label: 'Compliance Score',value: '98%',          icon: Shield,    trend: 'Above threshold',trendUp: true, gradient: 'from-amber-500 to-amber-600',   bg: 'bg-amber-50',  text: 'text-amber-600',  route: '/organisation' },
  ]

  return (
    <Layout title="Dashboard">
      <div className="space-y-6 animate-fade-in">
        {isLoading ? <SkeletonDashboard /> : (
          <>
            {/* ── Registration expiry alert ── */}
            {expiryDays !== null && expiryDays <= 30 && (
              <div className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${
                expiryDays <= 7
                  ? 'bg-red-50 border-red-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <AlertTriangle className={`h-4 w-4 shrink-0 mt-0.5 ${expiryDays <= 7 ? 'text-red-500' : 'text-amber-500'}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${expiryDays <= 7 ? 'text-red-700' : 'text-amber-800'}`}>
                    NDIS registration {expiryDays <= 0 ? 'has expired' : 'expiring soon'}
                  </p>
                  <p className={`text-xs mt-0.5 ${expiryDays <= 7 ? 'text-red-600' : 'text-amber-700'}`}>
                    {expiryDays <= 0
                      ? 'Your registration has expired — renew immediately to continue delivering services.'
                      : `Your registration expires in ${expiryDays} day${expiryDays === 1 ? '' : 's'} — renew now to avoid service interruption.`}
                  </p>
                </div>
                <button
                  onClick={() => navigate('/organisation')}
                  className={`shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                    expiryDays <= 7
                      ? 'bg-red-100 border-red-300 text-red-700 hover:bg-red-200'
                      : 'bg-amber-100 border-amber-300 text-amber-800 hover:bg-amber-200'
                  }`}
                >
                  Renew now
                </button>
              </div>
            )}

            {/* ── KPI Cards ── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {KPIs.map(({ label, value, icon: Icon, trend, trendUp, bg, text, route }) => (
                <div key={label} onClick={() => navigate(route)} className="bg-white rounded-2xl border border-slate-100 p-5 cursor-pointer card-hover shadow-sm">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`h-11 w-11 rounded-xl ${bg} flex items-center justify-center`}>
                      <Icon className={`h-5 w-5 ${text}`} />
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-slate-300" />
                  </div>
                  <div>
                    <p className="kpi-value text-slate-900">{value}</p>
                    <p className="text-sm text-slate-500 mt-1">{label}</p>
                  </div>
                  <div className={`flex items-center gap-1 mt-3 text-xs font-medium ${trendUp ? 'text-emerald-600' : 'text-red-500'}`}>
                    <TrendingUp className="h-3 w-3" />{trend}
                  </div>
                </div>
              ))}
            </div>

            {/* ── Main grid ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Activity feed */}
              <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center justify-between p-5 border-b border-slate-100">
                  <div>
                    <h3 className="font-bold text-slate-900">Recent Activity</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Latest updates across your organisation</p>
                  </div>
                  <button className="text-xs text-purple-600 font-semibold hover:underline flex items-center gap-1">
                    View all <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
                <div className="divide-y divide-slate-50">
                  {ACTIVITY.map((a, i) => {
                    const Icon = a.icon
                    return (
                      <div key={i} className="flex items-start gap-4 p-4 hover:bg-slate-50/50 transition-colors">
                        <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${activityColor[a.type]}`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-800 font-medium">{a.msg}</p>
                          <div className="flex items-center gap-1.5 mt-1">
                            <Clock className="h-3 w-3 text-slate-400" />
                            <p className="text-xs text-slate-400">{a.time}</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Right column */}
              <div className="space-y-5">
                {/* Quick actions */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <h3 className="font-bold text-slate-900 mb-4">Quick Actions</h3>
                  <div className="grid grid-cols-2 gap-2.5">
                    {QUICK_ACTIONS.map(({ label, icon: Icon, route, color }) => (
                      <button key={label} onClick={() => navigate(route)}
                        className={`flex flex-col items-center justify-center gap-2 p-3.5 rounded-xl border text-xs font-semibold transition-all hover:shadow-md hover:-translate-y-0.5 ${color}`}>
                        <Icon className="h-5 w-5" />{label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Organisation summary */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <h3 className="font-bold text-slate-900 mb-4">Organisation</h3>
                  {tenant ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-purple-800 flex items-center justify-center shrink-0 shadow-md shadow-purple-200">
                          <Building2 className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-900 text-sm leading-tight">{tenant.organisation_name}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{tenant.tenant_code}</p>
                        </div>
                      </div>
                      {[
                        { label: 'ABN',   value: tenant.abn },
                        { label: 'Email', value: tenant.email },
                        { label: 'Phone', value: tenant.phone },
                        { label: 'Plan',  value: tenant.plan_name },
                      ].filter(i => i.value).map(({ label, value }) => (
                        <div key={label} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                          <span className="text-xs text-slate-400 font-medium">{label}</span>
                          <span className="text-xs text-slate-700 font-medium">{value}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                      <Building2 className="h-8 w-8 text-slate-300 mb-2" />
                      <p className="text-xs text-slate-400">Loading organisation...</p>
                    </div>
                  )}
                  <button onClick={() => navigate('/organisation')}
                    className="mt-4 w-full h-9 text-xs font-semibold text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50 transition-colors flex items-center justify-center gap-1.5">
                    View full profile <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* System health */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <h3 className="font-bold text-slate-900 mb-4">System Health</h3>
                  <div className="space-y-3">
                    {[
                      { label: 'API Response', value: 99.9, color: 'bg-emerald-500' },
                      { label: 'Database',     value: 100,  color: 'bg-emerald-500' },
                      { label: 'Storage Used', value: 34,   color: 'bg-purple-500' },
                      { label: 'User Licences',value: 80,   color: 'bg-amber-500' },
                    ].map(({ label, value, color }) => (
                      <div key={label}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-slate-500 font-medium">{label}</span>
                          <span className="text-xs font-bold text-slate-800">{value}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
