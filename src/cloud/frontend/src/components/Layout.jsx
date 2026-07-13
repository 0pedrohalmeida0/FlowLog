import { Link, Outlet, useNavigate } from 'react-router-dom'
import { limparTokens } from '../lib/api'

export default function Layout() {
  const navigate = useNavigate()

  function logout() {
    limparTokens()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-flowlog-primary text-white shadow">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <Link to="/dashboard" className="text-xl font-bold">
            🌊 FlowLog Cloud
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <Link to="/produtos" className="hover:underline">Produtos</Link>
            <button onClick={logout} className="hover:underline">Sair</button>
          </nav>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="bg-gray-100 border-t py-3 text-center text-xs text-gray-500">
        FlowLog Cloud v2.0.0 · <a href="/docs" className="hover:underline">API Docs</a>
      </footer>
    </div>
  )
}
