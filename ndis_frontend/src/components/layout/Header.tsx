import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Search, Bell, User, LogOut, ChevronDown, Calendar, ChevronRight, Home } from 'lucide-react'

const ROUTE_LABELS: Record<string, string> = {
  '/dashboard':    'Dashboard',
  '/organisation': 'Organisation',
  '/branches':     'Branches',
  '/programs':     'Programs',
  '/users':        'Users',
  '/roles':        'Roles & Permissions',
  '/profile':      'Profile',
  '/activity':     'Activity',
}

function getBreadcrumbs(pathname: string) {
  const label = ROUTE_LABELS[pathname]
  if (!label || pathname === '/dashboard') return []
  return [{ label, path: pathname }]
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function formatDate() {
  return new Date().toLocaleDateString('en-AU', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
}

interface BreadcrumbItem {
  label: string
  path?: string
}

interface HeaderProps {
  title?: string
  breadcrumbs?: BreadcrumbItem[]
}

export function Header({ title: _title, breadcrumbs: propBreadcrumbs }: HeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const isDashboard = pathname === '/dashboard'
  const autoBreadcrumbs = getBreadcrumbs(pathname)
  const breadcrumbs = propBreadcrumbs ?? autoBreadcrumbs

  const [searchFocused, setSearchFocused] = useState(false)
  const [dropdownOpen, setDropdownOpen]   = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Prefer full_name; fall back to email username when name is blank or a generic default
  const genericNames = ['admin', 'admin user', 'user']
  const fullName = user?.full_name?.trim()
  const emailUser = user?.email?.split('@')[0] || ''
  const isGeneric = !fullName || genericNames.includes(fullName.toLowerCase())

  const displayName = isGeneric ? emailUser : fullName
  const firstName   = displayName.split(' ')[0] || 'there'
  const initials    = displayName
    .split(' ').map((n: string) => n[0]?.toUpperCase()).slice(0, 2).join('') || '?'

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node))
        setDropdownOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-16 border-b border-slate-100 bg-white flex items-center justify-between px-6 shrink-0 sticky top-0 z-20">
      {/* Left: greeting (dashboard only) */}
      {isDashboard ? (
        <div className="flex items-center gap-4">
          <div
            className="h-11 w-11 rounded-xl flex items-center justify-center text-2xl shrink-0"
            style={{ background: 'linear-gradient(135deg, #EDE8FF 0%, #C4B5F7 100%)' }}
          >
            👋
          </div>
          <div>
            <h2 className="text-lg font-bold leading-tight" style={{ color: '#2D1B6B' }}>
              {getGreeting()}, {firstName}
            </h2>
            <p className="text-[12px] font-medium mt-1 flex items-center gap-1.5" style={{ color: '#9B85D0' }}>
              <Calendar className="h-3.5 w-3.5" />
              {formatDate()}
            </p>
          </div>
        </div>
      ) : (
        /* Breadcrumb navigation for all other screens */
        <nav className="flex items-center gap-1.5" aria-label="Breadcrumb">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1 text-xs font-medium transition-colors hover:opacity-80"
            style={{ color: '#9B85D0' }}
          >
            <Home className="h-3.5 w-3.5" />
            Home
          </button>
          {breadcrumbs.map(({ label, path }, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
              {path ? (
                <button
                  onClick={() => navigate(path)}
                  className="text-xs font-medium transition-colors hover:opacity-80"
                  style={{ color: '#9B85D0' }}
                >
                  {label}
                </button>
              ) : (
                <span className="text-xs font-semibold" style={{ color: '#2D1B6B' }}>
                  {label}
                </span>
              )}
            </span>
          ))}
        </nav>
      )}

      {/* Right: search + notifications + user */}
      <div className="flex items-center gap-2 shrink-0">

        {/* Search */}
        <div className={`relative hidden sm:flex items-center transition-all duration-200 ${searchFocused ? 'w-64' : 'w-44'}`}>
          <Search className="absolute left-3 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search…"
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className="w-full h-8 pl-8 pr-3 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"
          />
        </div>

        {/* Notifications */}
        <button
          className="relative h-8 w-8 rounded-lg border border-slate-200 bg-white flex items-center justify-center text-slate-400 hover:text-slate-600 hover:border-slate-300 transition-colors"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
        </button>

        {/* Divider */}
        <div className="h-5 w-px bg-slate-200" />

        {/* User dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(v => !v)}
            className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <div
              className="h-7 w-7 rounded-full flex items-center justify-center text-white text-[11px] font-bold shrink-0"
              style={{ background: 'linear-gradient(135deg, #B39DDB 0%, #7C5CBF 100%)' }}
            >
              {initials}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-xs font-semibold text-slate-800 leading-none">{user?.full_name?.split(' ')[0]}</p>
              <p className="text-[10px] mt-0.5" style={{ color: '#7C5CBF' }}>
                {user?.is_tenant_admin ? 'Administrator' : 'Member'}
              </p>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400 hidden md:block" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-lg border border-slate-100 py-1.5 z-50 animate-fade-in">
              {/* User info */}
              <div className="px-4 py-2.5 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-900 truncate">{displayName}</p>
                <p className="text-[11px] text-slate-500 truncate mt-0.5">{user?.email}</p>
                <span
                  className="inline-block mt-1 text-[10px] font-medium px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(124,92,191,0.1)', color: '#7C5CBF' }}
                >
                  {user?.is_tenant_admin ? 'Administrator' : 'Member'}
                </span>
              </div>

              <button
                onClick={() => { setDropdownOpen(false); navigate('/profile') }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <User className="h-4 w-4 text-slate-400" />
                My Profile
              </button>

              <div className="border-t border-slate-100 mt-1 pt-1">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
