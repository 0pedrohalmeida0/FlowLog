# FlowLog Cloud — Frontend (v2.0)

Stack:
- React 18 + Vite 5
- React Router 6
- Tailwind CSS 3
- Sem TypeScript (MVP — fácil de migrar depois)

## Rodar local (dev)

```bash
cd src/cloud/frontend
npm install
npm run dev
# Frontend em http://localhost:5173
# (proxy /v1 → http://localhost:8000)
```

Certifique-se de que o backend Cloud está rodando em outra aba:

```bash
cd /workspace/FlowLog
PYTHONPATH=. uvicorn cloud.main:app --reload --port 8000
```

## Build produção

```bash
npm run build
# Saída em dist/
```

O `dist/` é o que vai pro CDN (Cloudflare Pages, Vercel, etc).
