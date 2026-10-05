/**
 * usePermissions — loads the current user's effective permission codes
 * and exposes a `can(code)` helper for UI gate-keeping.
 *
 * Rules:
 *  • is_tenant_admin=true  → can do EVERYTHING (bypasses all checks)
 *  • Otherwise             → must have the exact permission_code granted
 *
 * The hook caches the permission list via react-query (staleTime 5 min)
 * so it doesn't re-fetch on every component mount.
 */
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import { getUserPermissions } from '@/api/users'

export function usePermissions() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const userId   = user?.user_id
  const isAdmin  = user?.is_tenant_admin === true

  const { data: permissions = [], isLoading } = useQuery({
    queryKey: ['my-permissions', tenantId, userId],
    queryFn:  () => getUserPermissions(tenantId, userId).then((r: any) => {
      const list = r.data || []
      // permission_code is the canonical field; fall back to permission_name (frontend alias)
      return list.map((p: any) => p.permission_code || p.permission_name || '') as string[]
    }),
    enabled:  !!tenantId && !!userId && !isAdmin,  // admins skip the fetch
    staleTime: 5 * 60 * 1000,
  })

  /**
   * can('roles:create')  → true/false
   * Admins always return true.
   */
  const can = (code: string): boolean => {
    if (isAdmin) return true
    return permissions.includes(code)
  }

  /**
   * canAny(['roles:create', 'roles:edit'])  → true if user has at least one
   */
  const canAny = (...codes: string[]): boolean => codes.some(can)

  /**
   * canAll(['roles:create', 'roles:edit'])  → true only if user has all
   */
  const canAll = (...codes: string[]): boolean => codes.every(can)

  return { can, canAny, canAll, permissions, isLoading, isAdmin }
}
