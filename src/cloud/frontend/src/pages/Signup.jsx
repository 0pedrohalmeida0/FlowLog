import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api, salvarTokens } from '../lib/api'

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    tenant_nome: '',
    tenant_cnpj: '',
    admin_email: '',
    admin_username: '',
    admin_senha: '',
    plano: 'free',
  })
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  function update(k, v) {
    setForm((f) => ({ ...f, [k]: v }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErro('')
    setLoading(true)
    try {
      const data = await api.signup(form)
      salvarTokens(data.access_token, data.refresh_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setErro(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-2 text-flowlog-primary">
          🌊 FlowLog Cloud
        </h1>
        <p className="text-center text-sm text-gray-600 mb-6">
          14 dias grátis. Sem cartão.
        </p>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="Nome da empresa" required value={form.tenant_nome} onChange={(v) => update('tenant_nome', v)} />
          <Field label="CNPJ (opcional)" value={form.tenant_cnpj} onChange={(v) => update('tenant_cnpj', v)} placeholder="00.000.000/0000-00" />
          <Field label="Seu email" type="email" required value={form.admin_email} onChange={(v) => update('admin_email', v)} />
          <Field label="Seu usuário" required value={form.admin_username} onChange={(v) => update('admin_username', v)} />
          <Field label="Sua senha (mín 8)" type="password" required value={form.admin_senha} onChange={(v) => update('admin_senha', v)} />
          <div>
            <label className="block text-sm font-medium mb-1">Plano</label>
            <select
              value={form.plano}
              onChange={(e) => update('plano', e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="free">Free — 1 user, 100 produtos</option>
              <option value="pro">Pro — 5 users, ilimitado (R$ 99/mês)</option>
              <option value="business">Business — 50 users, API (R$ 299/mês)</option>
            </select>
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
            {loading ? 'Criando conta...' : 'Começar trial grátis'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600 mt-4">
          Já tem conta? <Link to="/login" className="text-flowlog-primary">Entrar</Link>
        </p>
      </div>
    </div>
  )
}

function Field({ label, type = 'text', value, onChange, required, placeholder }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        className="w-full border rounded px-3 py-2"
      />
    </div>
  )
}
