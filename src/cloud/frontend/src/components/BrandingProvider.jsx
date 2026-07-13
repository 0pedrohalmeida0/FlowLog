// Aplica CSS vars dinâmicas (white-label) baseado no branding do tenant.
// Carrega o branding público de `slug` (CNPJ ou ID do tenant) —
// funciona ANTES do user logar (pra página de login já ter o tema).

import { useEffect, useState, createContext, useContext } from 'react'

const BrandingContext = createContext({
  branding: null,
  loading: true,
})

export function useBranding() {
  return useContext(BrandingContext)
}

export function BrandingProvider({ tenantSlug, children }) {
  const [branding, setBranding] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!tenantSlug) {
      setLoading(false)
      return
    }

    fetch(`/v1/branding/public/${encodeURIComponent(tenantSlug)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setBranding(data)
          // Aplica CSS vars no :root
          const root = document.documentElement
          Object.entries(data.css_vars || {}).forEach(([k, v]) => {
            root.style.setProperty(k, v)
          })
          document.title = `${data.nome_exibicao || 'FlowLog'} — Cloud`
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [tenantSlug])

  return (
    <BrandingContext.Provider value={{ branding, loading }}>
      {children}
    </BrandingContext.Provider>
  )
}
