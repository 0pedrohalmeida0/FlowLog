// FlowLog Cloud — Service Worker (v2.1, sem push)
// Estratégia: cache-first pra assets estáticos, network-first pra /v1/*

const CACHE_NAME = 'flowlog-v2.1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
]

// Instala: pré-cachea assets estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

// Ativa: limpa caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  )
  self.clients.claim()
})

// Fetch: network-first pra API, cache-first pra resto
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // API: network-first, fallback pro cache
  if (url.pathname.startsWith('/v1/')) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          // Cacheia GETs bem-sucedidos
          if (event.request.method === 'GET' && res.ok) {
            const clone = res.clone()
            caches.open(CACHE_NAME).then((c) => c.put(event.request, clone))
          }
          return res
        })
        .catch(() => caches.match(event.request))
    )
    return
  }

  // Frontend: cache-first, fallback pra network
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached
      return fetch(event.request).then((res) => {
        if (res.ok && event.request.method === 'GET') {
          const clone = res.clone()
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone))
        }
        return res
      })
    })
  )
})

// Push notification (v2.2 — por enquanto só estrutura)
// self.addEventListener('push', (event) => { ... })
