"""List all tools in the database."""
from database.connection import get_supabase_client

client = get_supabase_client()
tools = client.table("tools").select("name,website,trust_score").execute().data
embs = client.table("embeddings").select("tool_id").execute().data
emb_ids = {e["tool_id"] for e in embs}

for t in tools:
    name = t["name"] or "<no name>"
    has_emb = "Y" if any(e["tool_id"] == t.get("id") for e in embs) else "?"
    print(f"  {name:25s} | {t['website']:35s} | trust: {t['trust_score']}")

print(f"\nTotal tools: {len(tools)}, embeddings: {len(embs)}")
