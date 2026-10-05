import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { login as loginApi } from '@/api/auth'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPwd, setShowPwd] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await loginApi(form)
      login(data)
      navigate('/dashboard')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Invalid credentials. Please check your details and try again.'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12"
        style={{ background: 'linear-gradient(160deg, #EDE8FF 0%, #DDD5F7 100%)' }}>
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl flex items-center justify-center"
            style={{ background: '#7C5CBF' }}>
            <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <p className="font-bold text-lg leading-none" style={{ color: '#2D1B6B' }}>NDIS Manager</p>
            <p className="text-xs" style={{ color: '#9B85D0' }}>Management System</p>
          </div>
        </div>

        {/* Main message + features */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold leading-tight" style={{ color: '#2D1B6B' }}>
              Welcome back.<br />
              <span style={{ color: '#7C5CBF' }}>Your team is waiting.</span>
            </h1>
            <p className="mt-4 text-sm leading-relaxed max-w-sm" style={{ color: 'rgba(61,43,122,0.65)' }}>
              Sign in to manage your participants, staff, schedules and organisation — all in one place.
            </p>
          </div>

          {/* What's inside */}
          <div className="space-y-3">
            {[
              {
                icon: 'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z',
                label: 'Participant management',
                sub: 'View and update participant plans and goals',
              },
              {
                icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
                label: 'Rosters and scheduling',
                sub: 'Manage shifts, appointments and staff availability',
              },
              {
                icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
                label: 'Reports and records',
                sub: 'Access progress notes, incident reports and documents',
              },
              {
                icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
                label: 'Organisation settings',
                sub: 'Manage branches, teams, roles and permissions',
              },
            ].map(({ icon, label, sub }) => (
              <div key={label} className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                  style={{ background: 'rgba(124,92,191,0.12)' }}>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="#7C5CBF" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: '#2D1B6B' }}>{label}</p>
                  <p className="text-xs mt-0.5" style={{ color: 'rgba(61,43,122,0.65)' }}>{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom — neutral footer, no fake claims */}
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <p className="text-xs" style={{ color: '#7C5CBF' }}>NDIS Manager — built for Australian disability service providers</p>
        </div>
      </div>

      {/* ── Right panel: login form ── */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 sm:px-16 lg:px-20 xl:px-28 bg-white">
        {/* Mobile logo */}
        <div className="flex items-center gap-2 mb-10 lg:hidden">
          <div className="h-9 w-9 rounded-xl bg-purple-800 flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="h-4 w-4 text-white fill-white">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <p className="font-bold text-slate-900 leading-none">NDIS Manager</p>
            <p className="text-xs text-slate-500">Management System</p>
          </div>
        </div>

        <div className="w-full max-w-sm mx-auto animate-fade-in">
          {/* Heading */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="text-slate-500 mt-1.5 text-sm">Sign in to your organisation portal</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Username</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2">
                  <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                </span>
                <input
                  name="email"
                  type="email"
                  placeholder="Enter your username (email)"
                  value={form.email}
                  onChange={handleChange}
                  required
                  className="w-full pl-9 pr-4 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-slate-700">Password</label>
                <Link to="/forgot-password" className="text-xs text-purple-600 hover:text-purple-800 font-medium">Forgot password?</Link>
              </div>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2">
                  <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                  </svg>
                </span>
                <input
                  name="password"
                  type={showPwd ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  required
                  maxLength={64}
                  className="w-full pl-9 pr-10 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPwd ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              error.toLowerCase().includes('not registered') ? (
                <div className="flex items-start gap-2.5 bg-purple-50 border border-purple-200 text-purple-800 px-4 py-3 rounded-lg text-sm">
                  <svg className="h-4 w-4 mt-0.5 shrink-0 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>
                    Email not registered.{' '}
                    <Link to="/signup" className="font-semibold underline hover:text-purple-900">Sign up here</Link>
                    {' '}to create your organisation account.
                  </span>
                </div>
              ) : (
                <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  <svg className="h-4 w-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
                  {error}
                </div>
              )
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg shadow-sm transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && (
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {loading ? 'Signing in...' : 'Sign In to Portal'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              New NDIS provider?{' '}
              <Link to="/signup" className="text-purple-600 font-semibold hover:underline">
                Register your organisation
              </Link>
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}
