import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Building2, GitBranch, BookOpen,
  Users, Shield, ChevronRight, Activity, ArrowRightLeft, Settings2, UserCheck,
} from 'lucide-react'

const NAV_GROUPS = [
  {
    label: 'Dashboard',
    items: [
      { to: '/dashboard',    label: 'Dashboard',           icon: LayoutDashboard },
    ],
  },
  {
    label: 'Organisation',
    items: [
      { to: '/organisation', label: 'Organisation',        icon: Building2 },
      { to: '/branches',     label: 'Branches',            icon: GitBranch },
      { to: '/programs',     label: 'Programs',            icon: BookOpen },
    ],
  },
  {
    label: 'People',
    items: [
      { to: '/users',                label: 'Users',               icon: Users },
      { to: '/staff',                label: 'Staff Management',    icon: UserCheck },
      { to: '/roles',                label: 'Roles & Permissions', icon: Shield },
      { to: '/cross-branch-access',  label: 'Cross-Branch Access', icon: ArrowRightLeft },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/activity',  label: 'Activity', icon: Activity  },
      { to: '/settings',  label: 'Settings', icon: Settings2 },
    ],
  },
]

export function Sidebar() {

  return (
    <aside
      className="flex flex-col w-64 shrink-0 sticky top-0 h-screen overflow-hidden"
      style={{ background: 'linear-gradient(180deg, #EDE8FF 0%, #DDD5F7 100%)' }}
    >
      {/* ── Logo ── */}
      <div className="px-5 py-5" style={{ borderBottom: '1px solid rgba(124,92,191,0.15)' }}>
        <div className="flex items-center gap-3">
          <div
            className="h-9 w-9 rounded-xl flex items-center justify-center"
            style={{ background: '#7C5CBF' }}
          >
            <svg viewBox="0 0 24 24" className="fill-white" style={{ width: 18, height: 18 }}>
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <p className="font-bold text-sm leading-none tracking-tight" style={{ color: '#2D1B6B' }}>NDIS Manager</p>
            <p className="text-xs mt-0.5" style={{ color: '#9B85D0' }}>Enterprise Platform</p>
          </div>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 py-4 space-y-6">
        {NAV_GROUPS.map(({ label, items }) => (
          <div key={label}>
            <p className="px-3 text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#9B85D0' }}>{label}</p>
            <div className="space-y-0.5">
              {items.map(({ to, label: lbl, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => `nav-item group ${isActive ? 'active' : ''}`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="flex-1">{lbl}</span>
                  <ChevronRight className="h-3 w-3 opacity-0 group-hover:opacity-50 transition-opacity" />
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

    </aside>
  )
}
