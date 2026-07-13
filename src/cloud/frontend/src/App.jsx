import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Produtos from './pages/Produtos.jsx'
import Billing from './pages/Billing.jsx'
import Branding from './pages/Branding.jsx'
import Layout from './components/Layout.jsx'
import { BrandingProvider } from './components/BrandingProvider.jsx'

function isLoggedIn() {
  return !!localStorage.getItem('flowlog_access_token')
}

function PrivateRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" replace />
}

// Pega o tenant_slug da URL (ex: /t/meu-slug/dashboard) ou de ?tenant=xxx
function getTenantSlug() {
  const params = new URLSearchParams(window.location.search)
  return params.get('tenant') || null
}

export default function App() {
  const tenantSlug = getTenantSlug()

  return (
    <BrandingProvider tenantSlug={tenantSlug}>
      <Routes>
        <Route path="/login" element={<Login tenantSlug={tenantSlug} />} />
        <Route path="/signup" element={<Signup tenantSlug={tenantSlug} />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="produtos" element={<Produtos />} />
          <Route path="billing" element={<Billing />} />
          <Route path="branding" element={<Branding />} />
        </Route>
      </Routes>
    </BrandingProvider>
  )
}
