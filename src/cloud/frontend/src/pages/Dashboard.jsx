import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api.resumo().then(setData).catch((e) => setErro(e.message))
  }, [])

  if (erro) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Erro: {erro}
      </div>
    )
  }
  if (!data) {
    return <div className="text-gray-500">Carregando...</div>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card titulo="Total de produtos" valor={data.total_produtos} icone="📦" />
        <Card titulo="Itens em estoque" valor={data.total_quantidade_estoque} icone="📊" />
        <Card titulo="Em alerta mínimo" valor={data.produtos_em_alerta} icone="⚠️" cor="red" />
        <Card titulo="Movs no mês" valor={data.movimentacoes_mes_atual} icone="🔄" />
      </div>
    </div>
  )
}

function Card({ titulo, valor, icone, cor = 'gray' }) {
  const corMap = {
    gray: 'bg-gray-50 border-gray-200',
    red: 'bg-red-50 border-red-200',
    green: 'bg-green-50 border-green-200',
  }
  return (
    <div className={`${corMap[cor]} border rounded-lg p-4`}>
      <div className="text-2xl mb-1">{icone}</div>
      <div className="text-sm text-gray-600">{titulo}</div>
      <div className="text-2xl font-bold mt-1">{valor}</div>
    </div>
  )
}
