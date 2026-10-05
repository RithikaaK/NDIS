import { createContext, useContext, useState, useCallback } from 'react'

interface User {
  user_id: string
  tenant_id: number
  email: string
  full_name: string
  first_name: string
  last_name: string
  is_tenant_admin: boolean
  schema_name: string
  tenant_code: string
  must_change_password?: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (data: { access_token: string; token_type: string; user: User }) => void
  logout: () => void
  updateUser: (partial: Partial<User>) => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try { return JSON.parse(localStorage.getItem('ndis_user') || 'null') } catch { return null }
  })

  const login = useCallback((tokenData: any) => {
    localStorage.setItem('ndis_token', tokenData.access_token)
    localStorage.setItem('ndis_user', JSON.stringify(tokenData))
    setUser(tokenData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('ndis_token')
    localStorage.removeItem('ndis_user')
    setUser(null)
  }, [])

  // Call this after saving profile/contact changes so the header refreshes immediately
  const updateUser = useCallback((partial: Partial<User>) => {
    setUser(prev => {
      if (!prev) return prev
      const updated = { ...prev, ...partial }
      localStorage.setItem('ndis_user', JSON.stringify(updated))
      return updated
    })
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      token: localStorage.getItem('ndis_token'),
      login,
      logout,
      updateUser,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
