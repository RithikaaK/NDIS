import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { signupRegistered, signupNonRegistered } from '@/api/tenant'
import { login as loginApi } from '@/api/auth'
import { useAuth } from '@/context/AuthContext'
import { splitFieldErrors } from '@/lib/errors'

const STATES = ['ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']

// Backend field name -> local form field key, for the few fields where they
// differ (the payload sends head_office_* while the form state uses the
// shorter local names). Used so a field_errors entry from the backend lands
// on the right input regardless of which name the backend used.
const FIELD_NAME_MAP: Record<string, string> = {
  head_office_address_line1: 'street_address',
  head_office_suburb: 'suburb',
  head_office_state_code: 'state_code',
  head_office_postcode: 'postcode',
}
const KNOWN_BACKEND_FIELDS = [
  'organisation_name', 'abn', 'acn', 'ndis_registration_number',
  ...Object.keys(FIELD_NAME_MAP),
]

export default function OrganisationSetup() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const { email, password } = (location.state as any) || {}

  const [providerType, setProviderType] = useState<'registered' | 'non-registered'>('registered')
  const [form, setForm] = useState({
    organisation_name: '',
    abn: '',
    acn: '',
    ndis_registration_number: '',
    admin_first_name: '',
    admin_last_name: '',
    street_address: '',
    suburb: '',
    state_code: '',
    postcode: '',
  })
  const [loading, setLoading] = useState(false)
  // Generic fallback message — only used for errors that can't be tied to a
  // field rendered on this screen (e.g. the admin email, which lives on the
  // previous Signup step, not here).
  const [error, setError] = useState('')
  // Field-level errors — the one place a backend error renders when it maps
  // to a specific field on THIS screen, e.g. { abn: "ABN already exists" }.
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const applyBackendError = (err: any, fallback: string) => {
    const { fieldErrors: feRaw, genericMessage } = splitFieldErrors(err, KNOWN_BACKEND_FIELDS, fallback)
    const fe: Record<string, string> = {}
    for (const [k, v] of Object.entries(feRaw)) fe[FIELD_NAME_MAP[k] ?? k] = v
    setFieldErrors(fe)
    setError(genericMessage ?? '')
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    // Clear that field's error as soon as the user edits it again.
    if (fieldErrors[e.target.name]) {
      setFieldErrors(fe => {
        const next = { ...fe }
        delete next[e.target.name]
        return next
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) { navigate('/signup'); return }
    setError(''); setFieldErrors({}); setLoading(true)
    try {
      const payload: any = {
        organisation_name: form.organisation_name,
        abn: form.abn.replace(/\s/g, ''),
        acn: form.acn || undefined,
        primary_email: email,
        admin_first_name: form.admin_first_name || 'Admin',
        admin_last_name: form.admin_last_name || 'User',
        admin_email: email,
        admin_password: password,
        head_office_address_line1: form.street_address || undefined,
        head_office_suburb: form.suburb || undefined,
        head_office_state_code: form.state_code || undefined,
        head_office_postcode: form.postcode || undefined,
      }
      if (providerType === 'registered') {
        payload.ndis_registration_number = form.ndis_registration_number
        // provider_type defaults to "Registered" in TenantSignupRegistered schema
        await signupRegistered(payload)
      } else {
        // Explicitly send "Non-Registered" — user made an active choice
        payload.provider_type = 'Non-Registered'
        await signupNonRegistered(payload)
      }
      // Auto-login and go straight to dashboard
      const { data } = await loginApi({ email, password })
      login(data)
      navigate('/dashboard')
    } catch (err: any) {
      applyBackendError(err, `Registration failed (${err?.response?.status ?? 500}). Please try again.`)
    } finally { setLoading(false) }
  }

  const handleSkip = async () => {
    if (!email || !password) { navigate('/signup'); return }
    setError(''); setFieldErrors({}); setLoading(true)
    try {
      await signupNonRegistered({
        organisation_name: 'My Organisation',
        primary_email: email,
        admin_first_name: 'Admin',
        admin_last_name: 'User',
        admin_email: email,
        admin_password: password,
      })
      // Auto-login and go straight to dashboard
      const { data } = await loginApi({ email, password })
      login(data)
      navigate('/dashboard')
    } catch (err: any) {
      applyBackendError(err, 'Registration failed. Please try again.')
    } finally { setLoading(false) }
  }

  const inputCls = "w-full px-3 h-10 rounded-lg border border-slate-200 bg-white text-sm placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all"
  const inputErrCls = "w-full px-3 h-10 rounded-lg border border-red-300 bg-red-50 text-sm placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent transition-all"
  const labelCls = "block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1"
  const cls = (name: string) => (fieldErrors[name] ? inputErrCls : inputCls)
  // Renders directly below the matching field — this is the one place a
  // field-specific error ever shows for this form (no separate error UI
  // elsewhere), so e.g. a duplicate ABN always appears right under ABN.
  const FieldError = ({ name }: { name: string }) =>
    fieldErrors[name] ? <p className="mt-1 text-xs text-red-600">{fieldErrors[name]}</p> : null

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel ── */}
      <div className="hidden lg:flex lg:w-5/12 flex-col justify-between p-12"
        style={{ background: 'linear-gradient(160deg, #EDE8FF 0%, #DDD5F7 100%)' }}>
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg flex items-center justify-center" style={{ background: '#7C5CBF' }}>
            <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <p className="font-bold text-base leading-none" style={{ color: '#2D1B6B' }}>NDIS Manager</p>
            <p className="text-xs" style={{ color: '#9B85D0' }}>Management System</p>
          </div>
        </div>

        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold leading-snug" style={{ color: '#2D1B6B' }}>
              Your team, your participants,<br />
              <span style={{ color: '#7C5CBF' }}>all in one place</span>
            </h1>
            <p className="mt-4 text-sm leading-relaxed max-w-xs" style={{ color: 'rgba(61,43,122,0.65)' }}>
              Designed for NDIS providers who want to spend less time on paperwork and more time on care.
            </p>
          </div>
          <div className="space-y-4">
            {[
              { icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', label: 'Manage participants easily', sub: 'Track plans, goals and services in one spot' },
              { icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z', label: 'Scheduling made simple', sub: 'Rosters, shifts and appointments at a glance' },
              { icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z', label: 'Stay on top of compliance', sub: 'Reports and audits ready when you need them' },
              { icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z', label: 'Your data stays safe', sub: 'Secure access for your whole team' },
            ].map(({ icon, label, sub }) => (
              <div key={label} className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style={{ background: 'rgba(124,92,191,0.12)' }}>
                  <svg className="h-4 w-4" style={{ color: '#7C5CBF' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
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

        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <p className="text-xs" style={{ color: '#7C5CBF' }}>Trusted by NDIS providers across Australia</p>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="w-full lg:w-7/12 flex flex-col justify-center px-8 sm:px-12 lg:px-16 bg-white overflow-y-auto py-10">
        <div className="w-full max-w-lg mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Organisation details</h2>
            <p className="text-slate-500 mt-1 text-sm">Tell us about your NDIS organisation — you can always update this later</p>
          </div>

          {/* Provider type toggle */}
          <div className="flex rounded-lg border border-slate-200 bg-white p-1 mb-6 w-fit">
            <button type="button"
              onClick={() => setProviderType('registered')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${providerType === 'registered' ? 'text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              style={providerType === 'registered' ? { background: '#7C5CBF' } : {}}>
              Registered Provider
            </button>
            <button type="button"
              onClick={() => setProviderType('non-registered')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${providerType === 'non-registered' ? 'text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              style={providerType === 'non-registered' ? { background: '#7C5CBF' } : {}}>
              Non-Registered
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Organisation Name */}
            <div>
              <label className={labelCls}>Organisation Name *</label>
              <input name="organisation_name" type="text" placeholder="Care Co Pty Ltd"
                value={form.organisation_name} onChange={handleChange} required className={cls('organisation_name')} />
              <FieldError name="organisation_name" />
            </div>

            {/* ABN + ACN */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>ABN *</label>
                <input name="abn" type="text" placeholder="12 345 678 901"
                  value={form.abn} onChange={handleChange} required maxLength={14} className={cls('abn')} />
                <FieldError name="abn" />
              </div>
              <div>
                <label className={labelCls}>ACN</label>
                <input name="acn" type="text" placeholder="123 456 789"
                  value={form.acn} onChange={handleChange} maxLength={11} className={cls('acn')} />
                <FieldError name="acn" />
              </div>
            </div>

            {/* NDIS Registration Number */}
            {providerType === 'registered' && (
              <div>
                <label className={labelCls}>NDIS Registration Number *</label>
                <input name="ndis_registration_number" type="text" placeholder="4-050-0123"
                  value={form.ndis_registration_number} onChange={handleChange} required className={cls('ndis_registration_number')} />
                <FieldError name="ndis_registration_number" />
              </div>
            )}

            {/* Head Office Address */}
            <div className="pt-2">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Head Office Address</p>
              <div className="space-y-3">
                <div>
                  <label className={labelCls}>Street Address</label>
                  <input name="street_address" type="text" placeholder="123 Main Street"
                    value={form.street_address} onChange={handleChange} className={cls('street_address')} />
                  <FieldError name="street_address" />
                </div>
                <div>
                  <label className={labelCls}>Suburb</label>
                  <input name="suburb" type="text" placeholder="Sydney"
                    value={form.suburb} onChange={handleChange} className={cls('suburb')} />
                  <FieldError name="suburb" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>State</label>
                    <select name="state_code" value={form.state_code} onChange={handleChange} className={cls('state_code')}>
                      <option value="">Select state</option>
                      {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <FieldError name="state_code" />
                  </div>
                  <div>
                    <label className={labelCls}>Postcode</label>
                    <input name="postcode" type="text" placeholder="2000"
                      value={form.postcode} onChange={handleChange} maxLength={4} className={cls('postcode')} />
                    <FieldError name="postcode" />
                  </div>
                </div>
              </div>
            </div>

            {/* Generic fallback — only for errors that don't map to a field on this screen (e.g. the admin email, set on the previous step) */}
            {error && (
              <div className="flex items-center gap-2.5 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={handleSkip} disabled={loading}
                className="flex-1 h-11 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 font-medium text-sm rounded-lg transition-all disabled:opacity-50">
                Skip for now
              </button>
              <button type="submit" disabled={loading}
                className="flex-1 h-11 text-white font-semibold text-sm rounded-lg shadow-sm transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                style={{ background: '#7C5CBF' }}
                onMouseEnter={e => { if (!loading) (e.currentTarget as HTMLButtonElement).style.background = '#6A4DAE' }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#7C5CBF' }}>
                {loading && (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                {loading ? 'Registering...' : 'Complete Registration →'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
