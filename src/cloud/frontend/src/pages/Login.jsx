import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api, salvarTokens } from '../lib/api'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setErro('')
    setLoading(true)
    try {
      const data = await api.login({ email, senha })
      salvarTokens(data.access_token, data.refresh_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setErro(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6 text-flowlog-primary">
          🌊 FlowLog Cloud
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              className="w-full border rounded px-3 py-2"
            />
          </div>
          {erro && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {erro}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-flowlog-primary text-white py-2 rounded hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600 mt-4">
          Não tem conta? <Link to="/signup" className="text-flowlog-primary">Cadastre-se</Link>
        </p>
      </div>
    </div>
  )
}
