# Claude Project Memory

Project Name: TruthEngine AI

Claude must read this file before generating code.

---

PROJECT PURPOSE

TruthEngine AI is an autonomous knowledge engine that collects, verifies, and organizes information about AI tools.

The system will:

• ingest URLs
• crawl the internet
• verify pricing models
• analyze community feedback
• store structured knowledge
• provide semantic search
• compare tools
• discover new tools automatically

---

SYSTEM CONSTRAINTS

1. Use only free services
2. No credit cards required
3. No paid APIs
4. Cloud-based deployment
5. Modular architecture

---

TECHNOLOGY STACK

Backend:
Python
FastAPI

AI Model:
Groq API

Database:
Supabase PostgreSQL

Vector Search:
pgvector

Crawler:
BeautifulSoup
duckduckgo-search

Frontend:
Next.js
Tailwind CSS
Framer Motion

Hosting:
PythonAnywhere
Cloudflare Pages

---

ARCHITECTURE

User
↓
Telegram Bot
↓
FastAPI Backend
↓
Ingestion Queue
↓
Crawler Workers
↓
Raw Data Storage
↓
AI Extraction Engine
↓
Truth Verification
↓
Knowledge Database
↓
Vector Search
↓
Response Generator

---

CORE MODULES

telegram_bot
api_gateway
crawler_engine
ai_processing_engine
truth_verification_engine
knowledge_storage
vector_search_engine
query_engine
comparison_engine
discovery_engine

---

AI OUTPUT FORMAT

{
"tool_name": "",
"core_function": "",
"pricing_model": "",
"free_tier_limits": "",
"community_verdict": "",
"tags": []
}

---

SECURITY

rate limiting
input validation
prompt injection protection

END
