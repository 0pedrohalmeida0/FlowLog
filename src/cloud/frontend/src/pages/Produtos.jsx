import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Produtos() {
  const [produtos, setProdutos] = useState([])
  const [erro, setErro] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ nome: '', quantidade: 0, preco_custo: 0, preco_venda: 0, alerta_minimo: 5 })
  const [edit, setEdit] = useState(null)  // id do produto em edição inline

  async function carregar() {
    try {
      const data = await api.listarProdutos()
      setProdutos(data)
    } catch (e) {
      setErro(e.message)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  async function criar(e) {
    e.preventDefault()
    try {
      await api.criarProduto(form)
      setForm({ nome: '', quantidade: 0, preco_custo: 0, preco_venda: 0, alerta_minimo: 5 })
      setShowForm(false)
      await carregar()
    } catch (e) {
      setErro(e.message)
    }
  }

  async function registrarMov(id, tipo) {
    const qtdStr = prompt(`Quantidade para ${tipo}:`)
    if (!qtdStr) return
    const qtd = parseInt(qtdStr, 10)
    if (isNaN(qtd) || qtd <= 0) {
      alert('Quantidade inválida')
      return
    }
    try {
      if (tipo === 'entrada') {
        await api.entrada(id, qtd)
      } else {
        await api.saida(id, qtd)
      }
      await carregar()
    } catch (e) {
      alert(e.message)
    }
  }

  async function salvarEdicao(p) {
    try {
      await api.editarProduto(p.id, {
        nome: p.nome,
        preco_custo: p.preco_custo,
        preco_venda: p.preco_venda,
        alerta_minimo: p.alerta_minimo,
      })
      setEdit(null)
      await carregar()
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Produtos</h1>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="bg-flowlog-primary text-white px-4 py-2 rounded hover:opacity-90"
        >
          {showForm ? 'Cancelar' : '+ Novo produto'}
        </button>
      </div>

      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 text-sm">
          {erro}
        </div>
      )}

      {showForm && (
        <form onSubmit={criar} className="bg-white p-4 rounded shadow mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            placeholder="Nome"
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            className="border rounded px-3 py-2"
            required
          />
          <input
            type="number"
            placeholder="Qtd inicial"
            value={form.quantidade}
            onChange={(e) => setForm({ ...form, quantidade: parseInt(e.target.value, 10) || 0 })}
            className="border rounded px-3 py-2"
          />
          <input
            type="number"
            step="0.01"
            placeholder="Preço custo"
            value={form.preco_custo}
            onChange={(e) => setForm({ ...form, preco_custo: parseFloat(e.target.value) || 0 })}
            className="border rounded px-3 py-2"
          />
          <input
            type="number"
            step="0.01"
            placeholder="Preço venda"
            value={form.preco_venda}
            onChange={(e) => setForm({ ...form, preco_venda: parseFloat(e.target.value) || 0 })}
            className="border rounded px-3 py-2"
          />
          <input
            type="number"
            placeholder="Alerta mín"
            value={form.alerta_minimo}
            onChange={(e) => setForm({ ...form, alerta_minimo: parseInt(e.target.value, 10) || 0 })}
            className="border rounded px-3 py-2"
          />
          <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded hover:opacity-90">
            Salvar
          </button>
        </form>
      )}

      <div className="bg-white shadow rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="px-4 py-2">Nome</th>
              <th className="px-4 py-2">Qtd</th>
              <th className="px-4 py-2">Custo</th>
              <th className="px-4 py-2">Venda</th>
              <th className="px-4 py-2">Alerta</th>
              <th className="px-4 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {produtos.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-4 py-6 text-center text-gray-500">
                  Nenhum produto cadastrado.
                </td>
              </tr>
            ) : (
              produtos.map((p) => {
                const emAlerta = p.alerta_minimo != null && p.quantidade <= p.alerta_minimo
                const editando = edit === p.id
                if (editando) {
                  return (
                    <tr key={p.id} className="border-t bg-yellow-50">
                      <td className="px-4 py-2">
                        <input
                          defaultValue={p.nome}
                          onChange={(e) => (p.nome = e.target.value)}
                          className="border rounded px-2 py-1 w-full"
                        />
                      </td>
                      <td className="px-4 py-2 text-gray-500">{p.quantidade}</td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          step="0.01"
                          defaultValue={p.preco_custo}
                          onChange={(e) => (p.preco_custo = parseFloat(e.target.value) || 0)}
                          className="border rounded px-2 py-1 w-20"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          step="0.01"
                          defaultValue={p.preco_venda || ''}
                          onChange={(e) => (p.preco_venda = parseFloat(e.target.value) || null)}
                          className="border rounded px-2 py-1 w-20"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          defaultValue={p.alerta_minimo || ''}
                          onChange={(e) => (p.alerta_minimo = parseInt(e.target.value, 10) || null)}
                          className="border rounded px-2 py-1 w-16"
                        />
                      </td>
                      <td className="px-4 py-2 space-x-1">
                        <button onClick={() => salvarEdicao(p)} className="text-green-600">✓</button>
                        <button onClick={() => setEdit(null)} className="text-gray-500">×</button>
                      </td>
                    </tr>
                  )
                }
                return (
                  <tr key={p.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{p.nome}</td>
                    <td className={`px-4 py-2 font-semibold ${emAlerta ? 'text-red-600' : ''}`}>
                      {p.quantidade}
                    </td>
                    <td className="px-4 py-2">R$ {Number(p.preco_custo).toFixed(2)}</td>
                    <td className="px-4 py-2">
                      {p.preco_venda != null ? `R$ ${Number(p.preco_venda).toFixed(2)}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-gray-500">{p.alerta_minimo ?? '—'}</td>
                    <td className="px-4 py-2 space-x-2 text-xs">
                      <button onClick={() => registrarMov(p.id, 'entrada')} className="text-green-600">+ Entrada</button>
                      <button onClick={() => registrarMov(p.id, 'saida')} className="text-red-600">− Saída</button>
                      <button onClick={() => setEdit(p.id)} className="text-blue-600">✏️</button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
