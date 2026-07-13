// Branding (v2.1) — white-label por tenant

import { useEffect, useState } from 'react'
import { api } from '../lib/api'

const DEFAULT = {
  nome_exibicao: '',
  logo_url: '',
  cor_primaria: '#1f6feb',
  cor_fundo: '#f9fafb',
  cor_texto: '#111827',
  dominio_custom: '',
}

export default function Branding() {
  const [form, setForm] = useState(DEFAULT)
  const [salvo, setSalvo] = useState('')
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.meuBranding()
      .then((b) => setForm({ ...DEFAULT, ...b }))
      .catch((e) => setErro(e.message))
  }, [])

  function update(k, v) {
    setForm((f) => ({ ...f, [k]: v }))
    // Live preview
    if (k.startsWith('cor_')) {
      document.documentElement.style.setProperty(`--flowlog-${k.replace('cor_', '')}`, v)
    }
    if (k === 'nome_exibicao' && v) {
      document.title = `${v} — Cloud`
    }
  }

  async function salvar() {
    setErro('')
    setSalvo('')
    setLoading(true)
    try {
      const updates = Object.fromEntries(
        Object.entries(form).filter(([_, v]) => v !== '' && v != null)
      )
      await api.atualizarBranding(updates)
      setSalvo('Branding atualizado!')
      setTimeout(() => setSalvo(''), 3000)
    } catch (e) {
      setErro(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">White-label (Branding)</h1>

      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 text-sm">
          {erro}
        </div>
      )}
      {salvo && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded mb-4 text-sm">
          {salvo}
        </div>
      )}

      <div className="bg-white shadow rounded p-6 space-y-4">
        <Field label="Nome de exibição" value={form.nome_exibicao} onChange={(v) => update('nome_exibicao', v)} />
        <Field label="URL do logo" value={form.logo_url} onChange={(v) => update('logo_url', v)} placeholder="https://..." />
        <ColorField label="Cor primária" value={form.cor_primaria} onChange={(v) => update('cor_primaria', v)} />
        <ColorField label="Cor de fundo" value={form.cor_fundo} onChange={(v) => update('cor_fundo', v)} />
        <ColorField label="Cor do texto" value={form.cor_texto} onChange={(v) => update('cor_texto', v)} />
        <Field
          label="Domínio custom (v2.2)"
          value={form.dominio_custom}
          onChange={(v) => update('dominio_custom', v)}
          placeholder="app.minhaempresa.com.br"
          hint="Funcionalidade de CNAME vem na v2.2. Por enquanto, guardamos o valor."
        />

        <div className="pt-4 border-t">
          <p className="text-sm text-gray-500 mb-3">Preview ao vivo (aplicado agora):</p>
          <div
            className="rounded p-6 text-center"
            style={{ background: form.cor_fundo, color: form.cor_texto }}
          >
            <div className="text-3xl mb-2">🌊</div>
            <div className="text-xl font-bold" style={{ color: form.cor_primaria }}>
              {form.nome_exibicao || 'FlowLog'}
            </div>
            <div className="text-sm mt-1">Cloud</div>
            <button
              className="mt-4 px-4 py-2 rounded text-white"
              style={{ background: form.cor_primaria }}
            >
              Botão de exemplo
            </button>
          </div>
        </div>

        <button
          onClick={salvar}
          disabled={loading}
          className="bg-flowlog-primary text-white px-4 py-2 rounded hover:opacity-90 disabled:opacity-50"
          style={{ background: 'var(--flowlog-primary)' }}
        >
          {loading ? 'Salvando...' : 'Salvar branding'}
        </button>
      </div>
    </div>
  )
}

function Field({ label, value, onChange, placeholder, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border rounded px-3 py-2"
      />
      {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
    </div>
  )
}

function ColorField({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <div className="flex gap-2">
        <input
          type="color"
          value={value || '#000000'}
          onChange={(e) => onChange(e.target.value)}
          className="h-10 w-12 rounded border"
        />
        <input
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 border rounded px-3 py-2 font-mono text-sm"
        />
      </div>
    </div>
  )
}
