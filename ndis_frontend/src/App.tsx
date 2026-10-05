import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/context/AuthContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:        5 * 60 * 1000,  // 5 min — data stays "fresh" so no refetch on revisit
      gcTime:          10 * 60 * 1000,  // 10 min — cache kept in memory
      retry:           1,
      refetchOnWindowFocus: false,
    },
  },
})
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import Login from '@/pages/Login'
import Signup from '@/pages/Signup.tsx'
import OrganisationSetup from '@/pages/OrganisationSetup'
import ForgotPassword from '@/pages/ForgotPassword'
import Dashboard from '@/pages/Dashboard'
import Organisation from '@/pages/Organisation'
import Branches from '@/pages/Branches'
import BranchDetail from '@/pages/BranchDetail'
import Programs from '@/pages/Programs'
import Users from '@/pages/Users'
import RolesPermissions from '@/pages/RolesPermissions'
import Profile from '@/pages/Profile'
import ActivityPage from '@/pages/Activity'
import ChangePassword from '@/pages/ChangePassword'
import CrossBranchAccess from '@/pages/CrossBranchAccess'
import Settings from '@/pages/Settings'
import Staff from '@/pages/Staff'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login"           element={<Login />} />
          <Route path="/signup"          element={<Signup />} />
          <Route path="/organisation-setup" element={<OrganisationSetup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Protected */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/organisation" element={<ProtectedRoute><Organisation /></ProtectedRoute>} />
          <Route path="/branches" element={<ProtectedRoute><Branches /></ProtectedRoute>} />
          <Route path="/branches/:id" element={<ProtectedRoute><BranchDetail /></ProtectedRoute>} />
          <Route path="/programs" element={<ProtectedRoute><Programs /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
          <Route path="/roles"   element={<ProtectedRoute><RolesPermissions /></ProtectedRoute>} />
          <Route path="/profile"   element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/activity"  element={<ProtectedRoute><ActivityPage /></ProtectedRoute>} />
          <Route path="/cross-branch-access" element={<ProtectedRoute><CrossBranchAccess /></ProtectedRoute>} />
          <Route path="/staff" element={<ProtectedRoute><Staff /></ProtectedRoute>} />
          <Route path="/settings"  element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </QueryClientProvider>
  )
}
