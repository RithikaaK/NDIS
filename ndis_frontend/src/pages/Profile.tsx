import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { getMe, updateMe, changePassword } from '@/api/auth'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

const inputCls = "w-full h-10 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls = "block text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1.5"

const EyeIcon = ({ open }: { open: boolean }) => open
  ? <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
  : <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>

export default function Profile() {
  const { user, updateUser } = useAuth()

  // Profile form state
  const [profile, setProfile] = useState({ first_name: '', last_name: '', mobile: '', job_title: '' })
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileMsg, setProfileMsg] = useState(null)  // { type: 'success'|'error', text }

  // Password form state
  const [pwdForm, setPwdForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [pwdLoading, setPwdLoading] = useState(false)
  const [pwdMsg, setPwdMsg] = useState(null)

  // Load current profile
  useEffect(() => {
    getMe().then(({ data }) => {
      setProfile({
        first_name: data.first_name || '',
        last_name:  data.last_name  || '',
        mobile:     data.mobile     || '',
        job_title:  data.job_title  || '',
      })
    }).catch(() => {})
  }, [])

  const initials = `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`.toUpperCase() || 'U'
  const fullName = `${profile.first_name} ${profile.last_name}`.trim() || user?.full_name || 'Your Profile'

  // ── Save profile ───────────────────────────────────────────────────────────
  const handleProfileSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setProfileMsg(null)
    if (!profile.first_name.trim() || !profile.last_name.trim()) {
      setProfileMsg({ type: 'error', text: 'First name and last name are required.' })
      return
    }
    setProfileLoading(true)
    try {
      const { data } = await updateMe({
        first_name: profile.first_name.trim(),
        last_name:  profile.last_name.trim(),
        mobile:     profile.mobile.trim() || null,
        job_title:  profile.job_title.trim() || null,
      })
      // Sync auth context → header avatar/name updates instantly
      updateUser({
        full_name:  data.full_name  || `${profile.first_name.trim()} ${profile.last_name.trim()}`.trim(),
        first_name: profile.first_name.trim(),
        last_name:  profile.last_name.trim(),
      })
      setProfileMsg({ type: 'success', text: 'Profile updated successfully.' })
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setProfileMsg({ type: 'error', text: typeof detail === 'string' ? detail : 'Failed to update profile.' })
    } finally { setProfileLoading(false) }
  }

  // ── Change password ────────────────────────────────────────────────────────
  const handlePasswordChange = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setPwdMsg(null)
    if (pwdForm.new_password.length < 8) {
      setPwdMsg({ type: 'error', text: 'New password must be at least 8 characters.' })
      return
    }
    if (pwdForm.new_password !== pwdForm.confirm_password) {
      setPwdMsg({ type: 'error', text: 'Passwords do not match.' })
      return
    }
    setPwdLoading(true)
    try {
      await changePassword({ current_password: pwdForm.current_password, new_password: pwdForm.new_password })
      setPwdForm({ current_password: '', new_password: '', confirm_password: '' })
      setPwdMsg({ type: 'success', text: 'Password changed successfully.' })
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setPwdMsg({ type: 'error', text: typeof detail === 'string' ? detail : 'Failed to change password.' })
    } finally { setPwdLoading(false) }
  }

  const Msg = ({ msg }) => msg ? (
    <div className={`flex items-center gap-2.5 px-4 py-3 rounded-lg text-sm ${
      msg.type === 'success'
        ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
        : 'bg-red-50 border border-red-200 text-red-700'
    }`}>
      {msg.type === 'success'
        ? <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
        : <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
      }
      {msg.text}
    </div>
  ) : null

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto space-y-6">

            {/* ── Avatar card ───────────────────────────────────────────── */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex items-center gap-5">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-xl font-bold shrink-0">
                {initials}
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">{fullName}</h1>
                <p className="text-sm text-slate-500 mt-0.5">{user?.email || ''}</p>
                {user?.is_tenant_admin && (
                  <span className="inline-flex items-center gap-1 mt-1.5 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-xs font-semibold">
                    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                    Tenant Administrator
                  </span>
                )}
              </div>
            </div>

            {/* ── Profile details form ───────────────────────────────────── */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
              <div className="px-6 py-4 border-b border-slate-100">
                <h2 className="text-base font-bold text-slate-900">Personal Information</h2>
                <p className="text-xs text-slate-500 mt-0.5">Update your name, mobile and job title</p>
              </div>
              <form onSubmit={handleProfileSave} className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>First Name *</label>
                    <input
                      className={inputCls}
                      value={profile.first_name}
                      onChange={e => setProfile(p => ({ ...p, first_name: e.target.value }))}
                      placeholder="Jane"
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Last Name *</label>
                    <input
                      className={inputCls}
                      value={profile.last_name}
                      onChange={e => setProfile(p => ({ ...p, last_name: e.target.value }))}
                      placeholder="Smith"
                    />
                  </div>
                </div>
                <div>
                  <label className={labelCls}>Email Address</label>
                  <input
                    className={`${inputCls} opacity-60 cursor-not-allowed`}
                    value={user?.email || ''}
                    disabled
                    title="Email cannot be changed"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Email address cannot be changed</p>
                </div>
                <div>
                  <label className={labelCls}>Mobile Number</label>
                  <input
                    className={inputCls}
                    value={profile.mobile}
                    onChange={e => setProfile(p => ({ ...p, mobile: e.target.value }))}
                    placeholder="0400 000 000"
                  />
                </div>
                <div>
                  <label className={labelCls}>Job Title</label>
                  <input
                    className={inputCls}
                    value={profile.job_title}
                    onChange={e => setProfile(p => ({ ...p, job_title: e.target.value }))}
                    placeholder="e.g. Service Manager"
                  />
                </div>

                <Msg msg={profileMsg} />

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={profileLoading}
                    className="h-10 px-6 text-white font-semibold text-sm rounded-lg transition-colors disabled:opacity-60 flex items-center gap-2"
                    style={{ background: '#7C5CBF' }}
                    onMouseEnter={e => { if (!profileLoading) (e.currentTarget as HTMLButtonElement).style.background = '#6A4DAE' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#7C5CBF' }}
                  >
                    {profileLoading && <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
                    {profileLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>

            {/* ── Change password form ───────────────────────────────────── */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
              <div className="px-6 py-4 border-b border-slate-100">
                <h2 className="text-base font-bold text-slate-900">Change Password</h2>
                <p className="text-xs text-slate-500 mt-0.5">Choose a strong password with at least 8 characters</p>
              </div>
              <form onSubmit={handlePasswordChange} className="p-6 space-y-4">
                {/* Current password */}
                <div>
                  <label className={labelCls}>Current Password</label>
                  <div className="relative">
                    <input
                      type={showCurrent ? 'text' : 'password'}
                      value={pwdForm.current_password}
                      onChange={e => setPwdForm(p => ({ ...p, current_password: e.target.value }))}
                      placeholder="Your current password"
                      className={`${inputCls} pr-10`}
                    />
                    <button type="button" onClick={() => setShowCurrent(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <EyeIcon open={showCurrent} />
                    </button>
                  </div>
                </div>
                {/* New password */}
                <div>
                  <label className={labelCls}>New Password</label>
                  <div className="relative">
                    <input
                      type={showNew ? 'text' : 'password'}
                      value={pwdForm.new_password}
                      onChange={e => setPwdForm(p => ({ ...p, new_password: e.target.value }))}
                      placeholder="Min. 8 characters"
                      className={`${inputCls} pr-10`}
                    />
                    <button type="button" onClick={() => setShowNew(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <EyeIcon open={showNew} />
                    </button>
                  </div>
                </div>
                {/* Confirm */}
                <div>
                  <label className={labelCls}>Confirm New Password</label>
                  <div className="relative">
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      value={pwdForm.confirm_password}
                      onChange={e => setPwdForm(p => ({ ...p, confirm_password: e.target.value }))}
                      placeholder="Re-enter new password"
                      className={`${inputCls} pr-10`}
                    />
                    <button type="button" onClick={() => setShowConfirm(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      <EyeIcon open={showConfirm} />
                    </button>
                  </div>
                </div>

                <Msg msg={pwdMsg} />

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={pwdLoading || !pwdForm.current_password || !pwdForm.new_password || !pwdForm.confirm_password}
                    className="h-10 px-6 bg-slate-800 hover:bg-slate-900 text-white font-semibold text-sm rounded-lg transition-colors disabled:opacity-60 flex items-center gap-2"
                  >
                    {pwdLoading && <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
                    {pwdLoading ? 'Updating...' : 'Change Password'}
                  </button>
                </div>
              </form>
            </div>

          </div>
        </main>
      </div>
    </div>
  )
}
