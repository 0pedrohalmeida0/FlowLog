// Billing (v2.1) — faturas do tenant + status

import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Billing() {
  const [faturas, setFaturas] = useState([])
  const [pendentes, setPendentes] = useState([])
  const [erro, setErro] = useState('')

  async function carregar() {
    try {
      const [todas, p] = await Promise.all([
        api.listarFaturas(),
        api.listarFaturasPendentes(),
      ])
      setFaturas(todas)
      setPendentes(p)
    } catch (e) {
      setErro(e.message)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  const totalPago = faturas
    .filter((f) => f.status === 'pago')
    .reduce((s, f) => s + f.valor_centavos, 0)
  const totalPendente = pendentes.reduce((s, f) => s + f.valor_centavos, 0)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Faturas</h1>

      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 text-sm">
          {erro}
        </div>
      )}

      {/* Cards resumo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card titulo="Pago (total)" valor={formatBRL(totalPago)} icone="✅" cor="green" />
        <Card titulo="Pendente" valor={formatBRL(totalPendente)} icone="⏰" cor="yellow" />
        <Card titulo="Total de faturas" valor={faturas.length} icone="📄" />
      </div>

      {/* Banner de pendentes */}
      {pendentes.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <p className="font-semibold">Você tem {pendentes.length} fatura(s) pendente(s).</p>
          <p className="text-sm text-gray-600">
            Efetue o pagamento via PIX/boleto e envie o comprovante por e-mail.
          </p>
        </div>
      )}

      {/* Tabela */}
      <div className="bg-white shadow rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="px-4 py-2">Número</th>
              <th className="px-4 py-2">Descrição</th>
              <th className="px-4 py-2">Valor</th>
              <th className="px-4 py-2">Vencimento</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {faturas.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-4 py-6 text-center text-gray-500">
                  Nenhuma fatura emitida.
                </td>
              </tr>
            ) : (
              faturas.map((f) => (
                <tr key={f.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-xs">{f.numero}</td>
                  <td className="px-4 py-2">{f.descricao}</td>
                  <td className="px-4 py-2">R$ {(f.valor_centavos / 100).toFixed(2)}</td>
                  <td className="px-4 py-2 text-gray-500">{new Date(f.vence_em).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-2">
                    <StatusBadge status={f.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Card({ titulo, valor, icone, cor = 'gray' }) {
  const cores = {
    gray: 'bg-gray-50 border-gray-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
  }
  return (
    <div className={`${cores[cor]} border rounded-lg p-4`}>
      <div className="text-2xl mb-1">{icone}</div>
      <div className="text-sm text-gray-600">{titulo}</div>
      <div className="text-2xl font-bold mt-1">{valor}</div>
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    pago: 'bg-green-100 text-green-800',
    pendente: 'bg-yellow-100 text-yellow-800',
    vencido: 'bg-red-100 text-red-800',
    cancelado: 'bg-gray-100 text-gray-800',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${map[status] || 'bg-gray-100'}`}>
      {status}
    </span>
  )
}

function formatBRL(centavos) {
  return `R$ ${(centavos / 100).toFixed(2)}`
}
