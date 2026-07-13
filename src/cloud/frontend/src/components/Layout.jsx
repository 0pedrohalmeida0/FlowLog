import { Link, Outlet, useNavigate } from 'react-router-dom'
import { limparTokens } from '../lib/api'
import { useBranding } from './BrandingProvider.jsx'

export default function Layout() {
  const navigate = useNavigate()
  const { branding } = useBranding()

  function logout() {
    limparTokens()
    navigate('/login', { replace: true })
  }

  const nome = branding?.nome_exibicao || 'FlowLog'

  return (
    <div className="min-h-screen flex flex-col">
      <header
        className="text-white shadow"
        style={{ background: 'var(--flowlog-primary, #1f6feb)' }}
      >
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <Link to="/dashboard" className="text-xl font-bold flex items-center gap-2">
            {branding?.logo_url ? (
              <img src={branding.logo_url} alt={nome} className="h-6" />
            ) : (
              '🌊'
            )}
            {nome} Cloud
          </Link>
          <nav className="flex gap-3 text-sm">
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <Link to="/produtos" className="hover:underline">Produtos</Link>
            <Link to="/billing" className="hover:underline">Faturas</Link>
            <Link to="/branding" className="hover:underline">Branding</Link>
            <button onClick={logout} className="hover:underline">Sair</button>
          </nav>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="bg-gray-100 border-t py-3 text-center text-xs text-gray-500">
        FlowLog Cloud v2.1.0 · <a href="/docs" className="hover:underline">API Docs</a>
      </footer>
    </div>
  )
}
