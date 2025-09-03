# DiViz Frontend (Next.js SPA)

A minimal Next.js 14 app that statically exports to `frontend/out` and is served by FastAPI at `/static`.

The SPA calls the FastAPI `/user` endpoint and renders the JSON under a "User" section.

## Prerequisites
- Node.js 18+ (recommend using nvm)
- npm 9+ (or pnpm/yarn if you prefer)

## Install
```bash
cd frontend
npm install
```

## Local development (Next.js dev server)
Useful for UI iteration, but note that it runs on port 3000 and will request `/user` from localhost:3000 (different origin than FastAPI at 8000). You may see 401s or CORS unless you proxy. For end-to-end testing, prefer the static export steps below.

```bash
npm run dev
# open http://localhost:3000
```

## Build (static export served by FastAPI)
This flow produces a static site in `frontend/out` that FastAPI serves under `/static`.

```bash
# From frontend/
npm run build

# In another terminal (repo root), run FastAPI
uv run uvicorn diviz.main:app --host 0.0.0.0 --port 8000 --reload

# Open the SPA (served by FastAPI)
open http://localhost:8000/static
```

Notes
- `next.config.js` is set to `output: 'export'` and uses `/static/` as `assetPrefix` in production, so exported assets resolve correctly under FastAPI's `/static` mount.
- The page calls `GET /user`. If your API requires auth, you will see a 401 JSON error until logged in.
- Re-run `npm run build` after frontend changes.

## Project scripts
```jsonc
// package.json (frontend)
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "export": "next export",
    "start": "next start"
  }
}
```

## Troubleshooting
- If `/static` returns 404, ensure you have exported files at `frontend/out` and that FastAPI has mounted it. The repo mounts automatically if the folder exists.
- If the SPA cannot reach `/user` in dev mode, use the export flow above or set up a proxy from Next dev server to FastAPI.

