# TruthEngine AI

Autonomous AI knowledge engine that discovers, verifies, and organizes information about AI tools.

## Architecture

```
User → Telegram Bot → FastAPI Backend → Crawler Workers → AI Extraction → Truth Verification → Knowledge DB (Supabase + pgvector) → Vector Search → Response
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| AI Model | Groq API (Llama 3) |
| Database | Supabase PostgreSQL + pgvector |
| Crawler | BeautifulSoup, duckduckgo-search |
| Bot | Telegram Bot API |
| Frontend | Next.js, Tailwind CSS, Framer Motion, shadcn/ui |
| Hosting | PythonAnywhere (backend), Cloudflare Pages (frontend) |

## Project Structure

```
truthengine-ai/
├── backend/          # FastAPI app, config, routers, middleware
├── database/         # Supabase connection, CRUD operations, schema
├── crawler/          # Web crawler, search crawler, source storage
├── agents/           # AI agents: extraction, verification, embedding, query, comparison, discovery
├── telegram/         # Telegram bot
├── workers/          # Ingestion and discovery pipelines
├── frontend/         # Next.js frontend app
├── requirements.txt
└── .env.example
```

## Setup

### 1. Backend

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Database

1. Create a project at [supabase.com](https://supabase.com)
2. Run `database/schema.sql` in the Supabase SQL Editor
3. Copy your project URL and anon key to `.env`

### 3. API Keys (all free)

| Service | Get Key |
|---------|---------|
| Supabase | [supabase.com](https://supabase.com) |
| Groq | [console.groq.com](https://console.groq.com) |
| HuggingFace | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| Telegram Bot | [@BotFather](https://t.me/botfather) |

### 4. Run Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run Telegram Bot

```bash
python -m telegram.bot
```

### 6. Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/ingest` | Submit URL for analysis |
| POST | `/api/v1/search` | Semantic search |
| GET | `/api/v1/tools` | List tools |
| GET | `/api/v1/tools/{id}` | Get tool details |
| POST | `/api/v1/compare` | Compare tools |

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/save <url>` | Ingest an AI tool |
| `/search <query>` | Search the knowledge base |
| `/compare <id1> <id2>` | Compare two tools |
| `/list` | List recent tools |

## Deployment

### Backend → PythonAnywhere

1. Upload code to PythonAnywhere
2. Set up virtual environment and install dependencies
3. Configure WSGI to point to `backend.main:app`
4. Set environment variables in the web app config

### Frontend → Cloudflare Pages

1. Push `frontend/` to a Git repo
2. Connect to Cloudflare Pages
3. Set build command: `npm run build`
4. Set output directory: `out`
5. Set `NEXT_PUBLIC_API_URL` environment variable

## Security

- Rate limiting on all endpoints (slowapi)
- URL validation and sanitization
- Input validation via Pydantic models
- Prompt injection protection in AI prompts
- Secrets stored in environment variables only
