# TruthEngine AI — Deployment Guide

## Production URLs

| Service     | URL                                                        | Platform |
|-------------|-----------------------------------------------------------|----------|
| **Backend** | https://truthengine-backend.onrender.com                  | Render   |
| **Frontend**| https://frontend-chi-nine-94.vercel.app                   | Vercel   |
| **Database**| https://ayktwnfzdgnjrwondpuo.supabase.co                  | Supabase |
| **GitHub**  | https://github.com/SandeshSatishhNaik/truthengine-ai      | GitHub   |

## API Endpoints (Production)

| Endpoint                      | Method | Description              |
|-------------------------------|--------|--------------------------|
| `/health`                     | GET    | Health check             |
| `/metrics`                    | GET    | Metrics snapshot         |
| `/api/v1/tools`               | GET    | List all tools           |
| `/api/v1/tools/{id}`          | GET    | Get tool by ID           |
| `/api/v1/tools/{id}/alternatives` | GET | Similar tools           |
| `/api/v1/ingest`              | POST   | Ingest new tool URL      |
| `/api/v1/search`              | POST   | Semantic search          |
| `/api/v1/compare`             | POST   | Compare tools            |

---

## Architecture

```
User → Vercel (Next.js frontend)
         ↓
       Render (FastAPI backend) ← APScheduler (discovery, cache, metrics)
         ↓
       Supabase (PostgreSQL + pgvector)
         ↓
       External APIs: Groq (LLM), HuggingFace (embeddings), DuckDuckGo (discovery)
```

---

## Deployment Checklist

### Pre-Deploy
- [x] Git repo initialized and pushed to GitHub
- [x] `.env` file NOT committed (in `.gitignore`)
- [x] `requirements.txt` has all Python dependencies
- [x] `frontend/package.json` has all Node dependencies
- [x] Frontend builds successfully (`next build`)
- [x] All 146 tests pass (`pytest tests/`)
- [x] CORS set to production frontend URL (not `*`)

### Backend (Render)
- [x] Service created: `truthengine-backend` (free plan, Oregon)
- [x] Runtime: Python, auto-deploy from `main` branch
- [x] Start command: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 10000`
- [x] Build command: `pip install -r requirements.txt`
- [x] Environment variables set:
  - [x] `SUPABASE_URL`
  - [x] `SUPABASE_KEY`
  - [x] `GROQ_API_KEY`
  - [x] `GROQ_MODEL`
  - [x] `HF_API_TOKEN`
  - [x] `EMBEDDING_MODEL`
  - [x] `EMBEDDING_DIM`
  - [x] `TELEGRAM_BOT_TOKEN`
  - [x] `DEBUG=false`
  - [x] `CORS_ORIGINS` (set to Vercel URLs)
  - [x] `PYTHON_VERSION=3.10.12`
- [x] Health check passing: `/health` returns `{"status":"healthy"}`
- [x] API responding: `/api/v1/tools` returns 23 tools

### Frontend (Vercel)
- [x] Project linked: `frontend`
- [x] Framework auto-detected: Next.js
- [x] `output: "standalone"` configured in `next.config.js`
- [x] Environment variable set: `NEXT_PUBLIC_API_URL=https://truthengine-backend.onrender.com/api/v1`
- [x] All 8 pages rendering correctly
- [x] Navigation working across all routes

### Database (Supabase)
- [x] Tables present: `tools` (23 rows), `sources` (74 rows), `reviews`, `embeddings` (23 rows)
- [x] pgvector extension enabled
- [x] `match_tools` RPC function created
- [x] 384-dimensional embeddings (all-MiniLM-L6-v2)
- [x] Foreign key constraints working (sources, reviews, embeddings → tools)

### Security
- [x] No secrets in git history
- [x] CORS restricted to Vercel frontend domains
- [x] Rate limiting enabled (30/min general, 20/min search, 10/min ingest, 10/min compare)
- [x] Input validation via Pydantic models
- [x] Request logging middleware active

---

## Environment Variables Reference

### Backend (Render)

| Variable           | Required | Default                                   | Description                |
|--------------------|----------|-------------------------------------------|----------------------------|
| `SUPABASE_URL`     | Yes      | —                                         | Supabase project URL       |
| `SUPABASE_KEY`     | Yes      | —                                         | Supabase anon key          |
| `GROQ_API_KEY`     | Yes      | —                                         | Groq LLM API key           |
| `GROQ_MODEL`       | No       | `llama-3.3-70b-versatile`                 | Groq model                 |
| `HF_API_TOKEN`     | Yes      | —                                         | HuggingFace API token      |
| `EMBEDDING_MODEL`  | No       | `sentence-transformers/all-MiniLM-L6-v2`  | Embedding model            |
| `EMBEDDING_DIM`    | No       | `384`                                     | Embedding dimensions       |
| `TELEGRAM_BOT_TOKEN`| Yes     | —                                         | Telegram bot token         |
| `DEBUG`            | No       | `false`                                   | Debug mode                 |
| `CORS_ORIGINS`     | Yes      | `http://localhost:3000`                   | Comma-separated origins    |
| `PYTHON_VERSION`   | No       | —                                         | Render Python version      |

### Frontend (Vercel)

| Variable              | Required | Default                          | Description           |
|-----------------------|----------|----------------------------------|-----------------------|
| `NEXT_PUBLIC_API_URL` | Yes      | `http://localhost:8000/api/v1`   | Backend API base URL  |

---

## Render Service Details

- **Service ID**: `srv-d6nhqr450q8c73a8l0tg`
- **Dashboard**: https://dashboard.render.com/web/srv-d6nhqr450q8c73a8l0tg
- **Region**: Oregon
- **Plan**: Free
- **Auto-deploy**: Enabled (on push to `main`)
- **SSH**: `srv-d6nhqr450q8c73a8l0tg@ssh.oregon.render.com`

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- 750 hours/month of uptime

---

## Vercel Project Details

- **Project ID**: `prj_zVfjPvKcfKJGf3Uz7eB5MOGqUosO`
- **Team**: `sandeshsatishnaik-gmailcoms-projects`
- **Production URL**: https://frontend-chi-nine-94.vercel.app
- **Framework**: Next.js (auto-detected)

---

## Deployment Workflow

### Updating Backend
```bash
git add -A
git commit -m "your changes"
git push origin main
# Render auto-deploys from main branch
```

### Updating Frontend
```bash
cd frontend
npx vercel --prod
# Or push to GitHub → connect Vercel git integration
```

### Monitoring
- **Backend health**: `curl https://truthengine-backend.onrender.com/health`
- **Backend metrics**: `curl https://truthengine-backend.onrender.com/metrics`
- **Render logs**: Dashboard → Logs tab
- **Vercel logs**: Dashboard → Deployments → Functions tab
