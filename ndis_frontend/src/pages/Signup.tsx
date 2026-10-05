import { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { sendOtp, verifyOtp } from '@/api/auth'
import { checkEmailDomain } from '@/api/tenant'
import { splitFieldErrors } from '@/lib/errors'

type Step = 'form' | 'verify'

const KNOWN_FIELDS = ['email', 'password', 'confirm_password']

export default function Signup() {
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>('form')
  const [form, setForm] = useState({ email: '', password: '', confirm_password: '' })
  const [digits, setDigits] = useState(['', '', '', '', '', ''])
  const [loading, setLoading] = useState(false)
  // Generic fallback — only for errors that aren't tied to email/password/confirm_password.
  const [error, setError] = useState('')
  // Field-level errors, rendered directly under the matching input.
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirmPwd, setShowConfirmPwd] = useState(false)
  const [countdown, setCountdown] = useState(60)
  const [domainError, setDomainError] = useState('')
  const [domainChecking, setDomainChecking] = useState(false)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const otp = digits.join('')

  useEffect(() => {
    if (step === 'verify') {
      setCountdown(60)
      timerRef.current = setInterval(() => {
        setCountdown(c => { if (c <= 1) { clearInterval(timerRef.current!); return 0 } return c - 1 })
      }, 1000)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [step])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (fieldErrors[name]) {
      setFieldErrors(fe => {
        const next = { ...fe }
        delete next[name]
        return next
      })
    }

    if (name === 'email') {
      setDomainError('')
      if (debounceRef.current) clearTimeout(debounceRef.current)

      const trimmed = value.trim().toLowerCase()
      const atIdx = trimmed.lastIndexOf('@')
      if (atIdx > 0 && trimmed.length > atIdx + 1) {
        setDomainChecking(true)
        debounceRef.current = setTimeout(async () => {
          try {
            const { data } = await checkEmailDomain(trimmed)
            if (!data.available) setDomainError(data.message)
          } catch { /* network error — let backend catch it on submit */ }
          finally { setDomainChecking(false) }
        }, 500)
      }
    }
  }

  const handleDigitChange = (i: number, val: string) => {
    const d = val.replace(/\D/g, '').slice(-1)
    const next = [...digits]; next[i] = d; setDigits(next)
    if (d && i < 5) inputRefs.current[i + 1]?.focus()
  }

  const handleDigitKeyDown = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[i] && i > 0) inputRefs.current[i - 1]?.focus()
  }

  const handleDigitPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) { setDigits(pasted.split('')); inputRefs.current[5]?.focus() }
    e.preventDefault()
  }

  const handleResend = async () => {
    setError(''); setDigits(['', '', '', '', '', ''])
    try {
      await sendOtp(form.email)
      setCountdown(60)
      timerRef.current = setInterval(() => {
        setCountdown(c => { if (c <= 1) { clearInterval(timerRef.current!); return 0 } return c - 1 })
      }, 1000)
      inputRefs.current[0]?.focus()
    } catch { setError('Failed to resend code.') }
  }

  const handleSendCode = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError(''); setFieldErrors({})
    if (domainError) return
    if (form.password !== form.confirm_password) {
      setFieldErrors({ confirm_password: 'Passwords do not match.' })
      return
    }
    if (form.password.length < 8) {
      setFieldErrors({ password: 'Password must be at least 8 characters.' })
      return
    }
    setLoading(true)
    try {
      await sendOtp(form.email)
      setStep('verify')
    } catch (err: any) {
      const { fieldErrors: fe, genericMessage } = splitFieldErrors(err, KNOWN_FIELDS, 'Failed to send verification code.')
      setFieldErrors(fe)
      setError(genericMessage ?? '')
    } finally { setLoading(false) }
  }

  const handleVerify = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      await verifyOtp(form.email, otp)
      // OTP verified — go to organisation setup with credentials in state
      navigate('/organisation-setup', { state: { email: form.email, password: form.password } })
    } catch (err: any) {
      const { genericMessage } = splitFieldErrors(err, [], 'Invalid verification code.')
      setError(genericMessage ?? 'Invalid verification code.')
    } finally { setLoading(false) }
  }

  const inputCls = "w-full pl-9 pr-4 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"

  const ErrorBox = ({ msg }: { msg: string }) => (
    <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
      <svg className="h-4 w-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      {msg}
    </div>
  )

  const Spinner = () => (
    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12"
        style={{ background: 'linear-gradient(160deg, #EDE8FF 0%, #DDD5F7 100%)' }}>
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
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold leading-tight" style={{ color: '#2D1B6B' }}>
              Get started today.<br />
              <span style={{ color: '#7C5CBF' }}>All in one place.</span>
            </h1>
            <p className="mt-4 text-sm leading-relaxed max-w-sm" style={{ color: 'rgba(61,43,122,0.65)' }}>
              Register your NDIS provider organisation and manage participants, staff, schedules and compliance — from day one.
            </p>
          </div>
          <div className="space-y-3">
            {[
              { icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', label: 'Quick setup', sub: 'Your organisation portal ready in minutes' },
              { icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z', label: 'Secure & compliant', sub: 'Built to meet NDIS standards and data security requirements' },
              { icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', label: 'Multi-user support', sub: 'Invite your team with role-based access control' },
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
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <p className="text-xs" style={{ color: '#7C5CBF' }}>NDIS Manager — built for Australian disability service providers</p>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 sm:px-16 lg:px-20 xl:px-28 bg-white">
        <div className="w-full max-w-sm mx-auto">

          {/* ── STEP 1: Email + Password ── */}
          {step === 'form' && (
            <>
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-slate-900">Create your account</h2>
                <p className="text-slate-500 mt-1.5 text-sm">Sign up to get started with NDIS Manager</p>
              </div>
              <form onSubmit={handleSendCode} className="space-y-5">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Email Address</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                      </svg>
                    </span>
                    <input name="email" type="email" placeholder="you@organisation.com.au"
                      value={form.email} onChange={handleChange} required
                      className={inputCls + ((domainError || fieldErrors.email) ? ' border-red-400 focus:ring-red-400' : '')} />
                    {domainChecking && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2">
                        <svg className="animate-spin h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                      </span>
                    )}
                  </div>
                  {(domainError || fieldErrors.email) && (
                    <div className="flex items-start gap-1.5 mt-1">
                      <svg className="h-4 w-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                      </svg>
                      <p className="text-xs text-red-600">{domainError || fieldErrors.email}</p>
                    </div>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Password</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                      </svg>
                    </span>
                    <input name="password" type={showPwd ? 'text' : 'password'} placeholder="Min 8 characters"
                      value={form.password} onChange={handleChange} required minLength={8} maxLength={64}
                      className={inputCls + ' pr-10' + (fieldErrors.password ? ' border-red-400 focus:ring-red-400' : '')} />
                    <button type="button" onClick={() => setShowPwd(!showPwd)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        {showPwd
                          ? <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                          : <><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>
                        }
                      </svg>
                    </button>
                  </div>
                  {fieldErrors.password && <p className="text-xs text-red-600 mt-1">{fieldErrors.password}</p>}
                  {/* Password rules — shown once user starts typing */}
                  {form.password.length > 0 && (() => {
                    const pwd = form.password
                    const rules = [
                      { label: 'At least 8 characters', ok: pwd.length >= 8 },
                      { label: 'One uppercase letter (A–Z)', ok: /[A-Z]/.test(pwd) },
                      { label: 'One lowercase letter (a–z)', ok: /[a-z]/.test(pwd) },
                      { label: 'One number (0–9)', ok: /[0-9]/.test(pwd) },
                      { label: 'One special character (!@#$…)', ok: /[^A-Za-z0-9]/.test(pwd) },
                    ]
                    return (
                      <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
                        {rules.map(r => (
                          <div key={r.label} className="flex items-center gap-2">
                            {r.ok
                              ? <svg className="h-3.5 w-3.5 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                              : <svg className="h-3.5 w-3.5 text-slate-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><circle cx="12" cy="12" r="9" /></svg>
                            }
                            <span className={`text-xs ${r.ok ? 'text-emerald-600' : 'text-slate-500'}`}>{r.label}</span>
                          </div>
                        ))}
                      </div>
                    )
                  })()}
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Confirm Password</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                      </svg>
                    </span>
                    <input name="confirm_password" type={showConfirmPwd ? 'text' : 'password'} placeholder="Re-enter password"
                      value={form.confirm_password} onChange={handleChange} required
                      className={inputCls + ' pr-10' + (fieldErrors.confirm_password ? ' border-red-400 focus:ring-red-400' : '')} />
                    <button type="button" onClick={() => setShowConfirmPwd(!showConfirmPwd)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        {showConfirmPwd
                          ? <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                          : <><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>
                        }
                      </svg>
                    </button>
                  </div>
                  {fieldErrors.confirm_password && <p className="text-xs text-red-600 mt-1">{fieldErrors.confirm_password}</p>}
                </div>
                {error && <ErrorBox msg={error} />}
                <button type="submit" disabled={loading || !!domainError || domainChecking}
                  className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg shadow-sm transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {loading && <Spinner />}
                  {loading ? 'Sending code...' : 'Send Verification Code'}
                </button>
              </form>
              <div className="mt-6 text-center">
                <p className="text-sm text-slate-500">
                  Already have an account?{' '}
                  <Link to="/login" className="text-purple-600 font-semibold hover:underline">Sign in</Link>
                </p>
              </div>
            </>
          )}

          {/* ── STEP 2: OTP ── */}
          {step === 'verify' && (
            <>
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-slate-900">Check your email</h2>
                <p className="text-slate-500 mt-1.5 text-sm">
                  We sent a 6-digit code to <span className="font-semibold text-slate-800">{form.email}</span>
                </p>
              </div>
              <form onSubmit={handleVerify} className="space-y-6">
                <div className="flex gap-2 justify-center">
                  {digits.map((d, i) => (
                    <input key={i}
                      ref={el => { inputRefs.current[i] = el }}
                      type="text" inputMode="numeric" maxLength={1}
                      value={d}
                      onChange={e => handleDigitChange(i, e.target.value)}
                      onKeyDown={e => handleDigitKeyDown(i, e)}
                      onPaste={handleDigitPaste}
                      className="w-11 text-center text-xl font-semibold rounded-xl border-2 border-slate-200 bg-slate-50 focus:outline-none focus:border-purple-500 focus:bg-white transition-all"
                      style={{ height: '52px' }}
                    />
                  ))}
                </div>
                {error && <ErrorBox msg={error} />}
                <button type="submit" disabled={loading || otp.length < 6}
                  className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg shadow-sm transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {loading && <Spinner />}
                  {loading ? 'Verifying...' : 'Verify & Continue →'}
                </button>
                <div className="text-center space-y-1">
                  <p className="text-sm text-slate-500">
                    Didn't receive it?{' '}
                    {countdown > 0
                      ? <span className="text-slate-400">Resend in {countdown}s</span>
                      : <button type="button" onClick={handleResend} className="text-purple-600 font-semibold hover:underline">Resend code</button>
                    }
                  </p>
                  <button type="button" onClick={() => { setStep('form'); setError(''); setDigits(['', '', '', '', '', '']) }}
                    className="text-sm text-slate-400 hover:text-slate-600">
                    ← Change email address
                  </button>
                </div>
              </form>
            </>
          )}

        </div>
      </div>
    </div>
  )
}
