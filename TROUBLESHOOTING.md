# TruthEngine AI — Troubleshooting Guide

## Common Issues

### 1. Backend Returns 502/503
**Cause**: Render free tier spins down after inactivity. First request takes ~30s.
**Fix**: Wait 30 seconds and retry. The service auto-starts on first request.

### 2. Frontend Shows "Failed to fetch" or Network Errors
**Cause**: Backend is cold-starting, or CORS misconfigured.
**Fix**:
- Check backend is alive: `curl https://truthengine-backend.onrender.com/health`
- Verify `CORS_ORIGINS` env var on Render includes the Vercel domain
- Check browser console for specific CORS error messages

### 3. Search Returns No Results
**Cause**: Embeddings not generated, or HuggingFace API token expired.
**Fix**:
- Check embeddings table has rows: Supabase dashboard → Table Editor → embeddings
- Verify `HF_API_TOKEN` is valid: test with `curl -H "Authorization: Bearer <token>" https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2`
- Re-run embedding backfill: `python scripts/backfill_embeddings.py`

### 4. Ingestion Fails
**Cause**: Groq API key invalid, rate limited, or target URL unreachable.
**Fix**:
- Check Render logs for specific error
- Verify `GROQ_API_KEY` by testing: `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer <key>"`
- Check if the target URL is accessible

### 5. Compare Page Shows Errors
**Cause**: Tool IDs in URL params don't exist, or API timeout.
**Fix**:
- Verify tool IDs exist: `curl https://truthengine-backend.onrender.com/api/v1/tools/<id>`
- Check Render logs for the compare endpoint error

### 6. Database Connection Errors
**Cause**: Supabase URL or key incorrect, or Supabase project paused.
**Fix**:
- Verify Supabase project is active at https://supabase.com/dashboard
- Check `SUPABASE_URL` and `SUPABASE_KEY` env vars on Render
- Supabase free projects pause after 7 days of inactivity — restore from dashboard

### 7. Discovery Worker Not Finding New Tools
**Cause**: DuckDuckGo search may be rate-limited or circuit breaker tripped.
**Fix**:
- Check Render logs for discovery worker errors
- The circuit breaker auto-resets after a cooldown period
- Discovery runs every 6 hours via APScheduler

### 8. Deployment Fails on Render
**Cause**: Build error in dependencies or code.
**Fix**:
- Check Render dashboard → Deploy → Build Logs
- Common issue: `lxml` needs system deps (already handled in `render.yaml` with pip)
- Verify `requirements.txt` has no version conflicts

### 9. Vercel Build Fails
**Cause**: TypeScript errors, missing dependencies, or env var issues.
**Fix**:
- Run `npm run build` locally in the `frontend/` directory
- Check for missing `NEXT_PUBLIC_API_URL` env var
- Verify `package-lock.json` is committed

### 10. Telegram Bot Not Responding
**Cause**: Bot token invalid, or webhook not set up.
**Fix**:
- The Telegram bot runs as part of the backend scheduler
- Verify `TELEGRAM_BOT_TOKEN` in Render env vars
- Check Render logs for Telegram-related errors

---

## Monitoring Commands

```bash
# Backend health
curl https://truthengine-backend.onrender.com/health

# System metrics
curl https://truthengine-backend.onrender.com/metrics

# List tools
curl https://truthengine-backend.onrender.com/api/v1/tools

# Test search
curl -X POST https://truthengine-backend.onrender.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI code assistant"}'

# Test ingestion
curl -X POST https://truthengine-backend.onrender.com/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example-tool.com"}'
```

---

## Logs Access

- **Render**: https://dashboard.render.com/web/srv-d6nhqr450q8c73a8l0tg → Logs
- **Vercel**: https://vercel.com/sandeshsatishnaik-gmailcoms-projects/frontend → Deployments
- **Supabase**: https://supabase.com/dashboard/project/ayktwnfzdgnjrwondpuo → Logs
