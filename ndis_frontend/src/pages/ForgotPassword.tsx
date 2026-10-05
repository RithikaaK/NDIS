import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { sendOtp, resetPassword } from '@/api/auth'

const OTP_LENGTH = 6

// ── Password rules ────────────────────────────────────────────────────────────
const PWD_RULES = [
  { key: 'len', test: (v: string) => v.length >= 8 && v.length <= 64, label: '8–64 characters' },
  { key: 'upper', test: (v: string) => /[A-Z]/.test(v), label: 'Uppercase letter (A-Z)' },
  { key: 'lower', test: (v: string) => /[a-z]/.test(v), label: 'Lowercase letter (a-z)' },
  { key: 'digit', test: (v: string) => /[0-9]/.test(v), label: 'Number (0-9)' },
  { key: 'special', test: (v: string) => /[!@#$%^&*]/.test(v), label: 'Special character (!@#$%^&*)' },
  { key: 'space', test: (v: string) => !/\s/.test(v), label: 'No spaces' },
]
const validatePassword = (pwd: string) => {
  const failed = PWD_RULES.filter(r => !r.test(pwd))
  return failed.length ? failed[0].label : null
}
const PasswordRules = ({ password }: { password: string }) => {
  if (!password) return null
  return (
    <div className="mt-2 space-y-1">
      {PWD_RULES.map(r => {
        const ok = r.test(password)
        return (
          <div key={r.key} className={`flex items-center gap-1.5 text-xs ${ok ? 'text-emerald-600' : 'text-slate-400'}`}>
            {ok
              ? <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              : <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="12" cy="12" r="9" /></svg>
            }
            {r.label}
          </div>
        )
      })}
    </div>
  )
}

// ── Shared left branding panel ────────────────────────────────────────────────
const LeftPanel = () => (
  <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12"
    style={{ background: 'linear-gradient(160deg, #7C5CBF 0%, #4E3594 100%)' }}>
    <div className="flex items-center gap-3">
      <div className="h-10 w-10 rounded-xl flex items-center justify-center border border-white/20"
        style={{ background: 'rgba(255,255,255,0.15)' }}>
        <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      </div>
      <div>
        <p className="text-white font-bold text-lg leading-none">NDIS Manager</p>
        <p className="text-xs" style={{ color: '#C4B0F0' }}>Management System</p>
      </div>
    </div>

    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white leading-tight">
          Secure account<br />
          <span style={{ color: '#C4B0F0' }}>recovery</span>
        </h1>
        <p className="mt-4 text-sm leading-relaxed max-w-sm" style={{ color: 'rgba(196,176,240,0.8)' }}>
          We'll send a one-time code to your registered email so you can set a new password safely.
        </p>
      </div>
      <div className="space-y-3">
        {[
          { icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z', label: 'One-time code verification', sub: 'Code is valid for 10 minutes' },
          { icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z', label: 'Sent to your registered email', sub: 'Check your inbox and spam folder' },
          { icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z', label: 'Your data stays secure', sub: 'End-to-end encrypted connection' },
        ].map(({ icon, label, sub }) => (
          <div key={label} className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
              style={{ background: 'rgba(255,255,255,0.1)' }}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="#C4B0F0" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-medium">{label}</p>
              <p className="text-xs mt-0.5" style={{ color: 'rgba(196,176,240,0.65)' }}>{sub}</p>
            </div>
          </div>
        ))}
      </div>
    </div>

    <div className="flex items-center gap-2">
      <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
      <p className="text-xs" style={{ color: 'rgba(196,176,240,0.55)' }}>NDIS Manager — built for Australian disability service providers</p>
    </div>
  </div>
)

const EyeIcon = ({ open }: { open: boolean }) => open
  ? <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
  : <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>

const ErrorBanner = ({ msg }: { msg: string }) => !msg ? null : (
  <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
    <svg className="h-4 w-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
    {msg}
  </div>
)

const Spinner = () => (
  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
)

export default function ForgotPassword() {
  const navigate = useNavigate()

  // phase: 'email' → 'otp' → 'password' → 'done'
  const [phase, setPhase] = useState('email')
  const [email, setEmail] = useState('')
  const [otpDigits, setOtpDigits] = useState(Array(OTP_LENGTH).fill(''))
  const [verifiedOtp, setVerifiedOtp] = useState('')   // stored after OTP screen
  const [devOtp, setDevOtp] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])

  // ── Phase 1: Send OTP ─────────────────────────────────────────────────────
  const handleSendOtp = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await sendOtp(email)
      if (data.dev_otp) setDevOtp(data.dev_otp)
      setOtpDigits(Array(OTP_LENGTH).fill(''))
      setPhase('otp')
      setTimeout(() => otpRefs.current[0]?.focus(), 100)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send code. Please check the email and try again.')
    } finally { setLoading(false) }
  }

  // ── OTP box handlers ──────────────────────────────────────────────────────
  const handleOtpChange = (i: number, val: string) => {
    const digit = val.replace(/\D/g, '').slice(-1)
    const next = [...otpDigits]; next[i] = digit; setOtpDigits(next)
    if (digit && i < OTP_LENGTH - 1) otpRefs.current[i + 1]?.focus()
  }
  const handleOtpKeyDown = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[i] && i > 0) otpRefs.current[i - 1]?.focus()
  }
  const handleOtpPaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault()
    const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH)
    if (!text) return
    const next = [...otpDigits]
    text.split('').forEach((d, i) => { next[i] = d })
    setOtpDigits(next)
    otpRefs.current[Math.min(text.length, OTP_LENGTH - 1)]?.focus()
  }

  // ── Phase 2: Confirm OTP → move to password screen ───────────────────────
  const handleConfirmOtp = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    const otp = otpDigits.join('')
    if (otp.length < OTP_LENGTH) { setError('Please enter the full 6-digit code.'); return }
    setVerifiedOtp(otp)
    setPhase('password')
  }

  // ── Phase 3: Set new password ─────────────────────────────────────────────
  const handleReset = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    const pwdError = validatePassword(newPwd)
    if (pwdError) { setError(`Password must include: ${pwdError}.`); return }
    if (newPwd !== confirmPwd) { setError('Passwords do not match.'); return }
    setLoading(true)
    try {
      await resetPassword(email, verifiedOtp, newPwd)
      setPhase('done')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reset failed. Please try again.')
    } finally { setLoading(false) }
  }

  const inputCls = "w-full pl-9 pr-4 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"

  return (
    <div className="min-h-screen flex">
      <LeftPanel />

      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 sm:px-16 lg:px-20 bg-white overflow-y-auto">
        <div className="w-full max-w-md mx-auto py-12 animate-fade-in">

          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-10 lg:hidden">
            <div className="h-9 w-9 rounded-xl bg-purple-800 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="h-4 w-4 fill-white"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
            </div>
            <div>
              <p className="font-bold text-slate-900 leading-none">NDIS Manager</p>
              <p className="text-xs text-slate-500">Management System</p>
            </div>
          </div>

          {/* ── Phase 1: Email ── */}
          {phase === 'email' && (
            <>
              <div className="mb-7">
                <h2 className="text-xl font-bold text-slate-900">Forgot your password?</h2>
                <p className="text-slate-500 mt-1.5 text-sm">
                  Enter your email and we'll send a verification code to reset your password.
                </p>
              </div>

              <form onSubmit={handleSendOtp} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Email Address</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>
                    </span>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="you@organisation.com.au"
                      required
                      className={inputCls}
                    />
                  </div>
                </div>

                <ErrorBanner msg={error} />

                <button
                  type="submit"
                  disabled={loading || !email}
                  className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  {loading && <Spinner />}
                  {loading ? 'Sending...' : 'Send Verification Code →'}
                </button>
              </form>

              <p className="text-center text-sm text-slate-500 mt-6">
                Remember your password?{' '}
                <Link to="/login" className="text-purple-600 font-semibold hover:underline">Sign in</Link>
              </p>
            </>
          )}

          {/* ── Phase 2: OTP Verification ── */}
          {phase === 'otp' && (
            <>
              <div className="mb-7">
                <h2 className="text-xl font-bold text-slate-900">Check your email</h2>
                <p className="text-slate-500 mt-1.5 text-sm">
                  We sent a 6-digit code to{' '}
                  <span className="font-semibold text-slate-700">{email}</span>
                </p>
              </div>


              <form onSubmit={handleConfirmOtp} className="space-y-5">
                {/* OTP boxes */}
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide block mb-3">Verification Code</label>
                  <div className="flex gap-2 justify-center" onPaste={handleOtpPaste}>
                    {otpDigits.map((d, i) => (
                      <input
                        key={i}
                        ref={el => { otpRefs.current[i] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={d}
                        onChange={e => handleOtpChange(i, e.target.value)}
                        onKeyDown={e => handleOtpKeyDown(i, e)}
                        className={`w-12 h-14 text-center text-xl font-bold rounded-xl border transition-all outline-none ${d ? 'border-purple-400 bg-purple-50 text-purple-700' : 'border-slate-200 bg-slate-50 text-slate-900'
                          } focus:border-purple-400 focus:ring-2 focus:ring-purple-200`}
                      />
                    ))}
                  </div>
                </div>

                <ErrorBanner msg={error} />

                <button
                  type="submit"
                  disabled={otpDigits.join('').length < OTP_LENGTH}
                  className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  Verify Code →
                </button>
              </form>

              <div className="mt-5 text-center space-y-2">
                <p className="text-sm text-slate-500">
                  Didn't receive it?{' '}
                  <button
                    onClick={() => { setPhase('email'); setError('') }}
                    className="text-purple-600 font-semibold hover:underline"
                  >
                    Try a different email
                  </button>
                </p>
              </div>
            </>
          )}

          {/* ── Phase 3: New Password ── */}
          {phase === 'password' && (
            <>
              <div className="mb-7">
                <h2 className="text-xl font-bold text-slate-900">Set a new password</h2>
                <p className="text-slate-500 mt-1.5 text-sm">
                  Choose a strong password for your account.
                </p>
              </div>

              <form onSubmit={handleReset} className="space-y-5">
                {/* New password */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">New Password</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
                    </span>
                    <input
                      type={showPwd ? 'text' : 'password'}
                      value={newPwd}
                      onChange={e => setNewPwd(e.target.value)}
                      placeholder="Min. 8 characters"
                      autoFocus
                      className="w-full pl-9 pr-10 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"
                    />
                    <button type="button" onClick={() => setShowPwd(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <EyeIcon open={showPwd} />
                    </button>
                  </div>
                  <PasswordRules password={newPwd} />
                </div>

                {/* Confirm password */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Confirm New Password</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2">
                      <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
                    </span>
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      value={confirmPwd}
                      onChange={e => setConfirmPwd(e.target.value)}
                      placeholder="Re-enter new password"
                      className="w-full pl-9 pr-10 h-11 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent focus:bg-white transition-all"
                    />
                    <button type="button" onClick={() => setShowConfirm(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <EyeIcon open={showConfirm} />
                    </button>
                  </div>
                </div>

                <ErrorBanner msg={error} />

                <button
                  type="submit"
                  disabled={loading || !newPwd || !confirmPwd}
                  className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  {loading && <Spinner />}
                  {loading ? 'Resetting...' : 'Reset Password →'}
                </button>
              </form>

              <p className="text-center mt-5">
                <button
                  onClick={() => { setPhase('otp'); setError('') }}
                  className="text-sm text-slate-400 hover:text-purple-600"
                >
                  ← Back to code entry
                </button>
              </p>
            </>
          )}

          {/* ── Phase 4: Done ── */}
          {phase === 'done' && (
            <div className="text-center">
              <div className="h-14 w-14 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                <svg className="h-7 w-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Password reset!</h2>
              <p className="text-slate-500 text-sm mb-8">
                Your password has been updated. You can now sign in with your new password.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full h-11 bg-purple-800 hover:bg-purple-900 text-white font-semibold text-sm rounded-lg transition-colors"
              >
                Sign In →
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
