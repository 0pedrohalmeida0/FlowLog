// Botão de "Entrar com Google" (v2.1).
// Requer <GoogleOAuthProvider> no main.jsx + GOOGLE_CLIENT_ID no backend.

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, salvarTokens } from '../lib/api'

// Google Identity Services: carrega o SDK on-demand
function loadGoogleSDK(clientId) {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve(window.google)
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => resolve(window.google)
    script.onerror = reject
    document.head.appendChild(script)
  })
}

export default function GoogleButton({ mode = 'login' }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')

  async function handleGoogle() {
    setErro('')
    setLoading(true)
    try {
      // Em produção, usar VITE_GOOGLE_CLIENT_ID do .env
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
      if (!clientId) {
        setErro('Google SSO não configurado (defina VITE_GOOGLE_CLIENT_ID)')
        setLoading(false)
        return
      }
      const google = await loadGoogleSDK(clientId)
      google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          try {
            const data = await api[mode === 'signup' ? 'googleSignup' : 'googleLogin']({
              id_token: response.credential,
              tenant_nome: mode === 'signup' ? 'Minha Empresa' : undefined,
            })
            salvarTokens(data.access_token, data.refresh_token)
            navigate('/dashboard', { replace: true })
          } catch (e) {
            setErro(e.message)
          }
        },
      })
      google.accounts.id.prompt()
    } catch (e) {
      setErro(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleGoogle}
        disabled={loading}
        className="w-full bg-white border border-gray-300 text-gray-700 py-2 rounded hover:bg-gray-50 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4" />
          <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.836.86-3.048.86-2.344 0-4.328-1.583-5.036-3.71H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853" />
          <path d="M3.964 10.708c-.18-.54-.282-1.117-.282-1.708s.102-1.168.282-1.708V4.96H.957C.347 6.175 0 7.55 0 9s.348 2.825.957 4.04l3.007-2.332z" fill="#FBBC05" />
          <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.96L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335" />
        </svg>
        {loading ? 'Carregando...' : (mode === 'signup' ? 'Cadastrar com Google' : 'Entrar com Google')}
      </button>
      {erro && (
        <div className="mt-2 text-xs text-red-600">{erro}</div>
      )}
    </div>
  )
}
