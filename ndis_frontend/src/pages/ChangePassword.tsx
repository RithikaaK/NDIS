import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Lock, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import { forcedChangePassword } from '@/api/auth'
import { useAuth } from '@/context/AuthContext'

export default function ChangePassword() {
  const navigate = useNavigate()
  const { updateUser } = useAuth()

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => forcedChangePassword({ new_password: newPassword }),
    onSuccess: () => {
      // Clear must_change_password flag in auth context so ProtectedRoute stops redirecting
      updateUser({ must_change_password: false })
      navigate('/dashboard', { replace: true })
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || 'Failed to change password. Please try again.')
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    mutation.mutate()
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
          {/* Header */}
          <div className="px-8 pt-8 pb-6 border-b border-slate-100 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-violet-50 mb-4">
              <ShieldCheck className="w-7 h-7 text-violet-700" />
            </div>
            <h1 className="text-xl font-semibold text-slate-900">Set a new password</h1>
            <p className="text-sm text-slate-500 mt-1">
              Your account requires a password change before you can continue.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 py-6 space-y-5">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* New password */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-slate-700">
                New password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showNew ? 'text' : 'password'}
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  required
                  className="w-full pl-9 pr-10 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowNew(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm password */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-slate-700">
                Confirm new password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your new password"
                  required
                  className="w-full pl-9 pr-10 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Password strength hint */}
            <ul className="text-xs text-slate-400 space-y-0.5 pl-1">
              <li className={newPassword.length >= 8 ? 'text-emerald-600' : ''}>
                {newPassword.length >= 8 ? '✓' : '·'} At least 8 characters
              </li>
              <li className={/[A-Z]/.test(newPassword) ? 'text-emerald-600' : ''}>
                {/[A-Z]/.test(newPassword) ? '✓' : '·'} One uppercase letter
              </li>
              <li className={/[0-9]/.test(newPassword) ? 'text-emerald-600' : ''}>
                {/[0-9]/.test(newPassword) ? '✓' : '·'} One number
              </li>
            </ul>

            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full py-2.5 px-4 bg-violet-700 hover:bg-violet-800 disabled:bg-violet-400 text-white text-sm font-semibold rounded-lg transition"
            >
              {mutation.isPending ? 'Saving…' : 'Set new password'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-400 mt-4">
          NDIS Manager · Secure password reset
        </p>
      </div>
    </div>
  )
}
