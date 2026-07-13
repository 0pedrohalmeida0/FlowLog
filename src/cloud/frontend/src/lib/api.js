// API client — todas as chamadas vão pra /v1 (proxy pro backend)

const API_BASE = '/v1'

function getToken() {
  return localStorage.getItem('flowlog_access_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    // Token expirou — limpa e redireciona
    localStorage.removeItem('flowlog_access_token')
    localStorage.removeItem('flowlog_refresh_token')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Auth
  signup: (data) => request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  refresh: (data) => request('/auth/refresh', { method: 'POST', body: JSON.stringify(data) }),
  me: () => request('/auth/me'),
  googleLogin: (data) => request('/auth/google/login', { method: 'POST', body: JSON.stringify(data) }),
  googleSignup: (data) => request('/auth/google/signup', { method: 'POST', body: JSON.stringify(data) }),

  // Billing
  listarFaturas: () => request('/billing/minhas'),
  listarFaturasPendentes: () => request('/billing/minhas/pendentes'),

  // Branding
  meuBranding: () => request('/branding/me'),
  atualizarBranding: (data) => request('/branding/me', { method: 'PATCH', body: JSON.stringify(data) }),

  // Produtos
  listarProdutos: () => request('/produtos'),
  criarProduto: (data) => request('/produtos', { method: 'POST', body: JSON.stringify(data) }),
  buscarProduto: (id) => request(`/produtos/${id}`),
  editarProduto: (id, data) => request(`/produtos/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  entrada: (id, quantidade) => request(`/produtos/${id}/entrada`, { method: 'POST', body: JSON.stringify({ quantidade }) }),
  saida: (id, quantidade) => request(`/produtos/${id}/saida`, { method: 'POST', body: JSON.stringify({ quantidade }) }),

  // Dashboard
  resumo: () => request('/dashboard/resumo'),
}

export function salvarTokens(access, refresh) {
  localStorage.setItem('flowlog_access_token', access)
  localStorage.setItem('flowlog_refresh_token', refresh)
}

export function limparTokens() {
  localStorage.removeItem('flowlog_access_token')
  localStorage.removeItem('flowlog_refresh_token')
}
