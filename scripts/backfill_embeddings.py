"""Backfill missing embeddings for tools."""
import asyncio
from agents.embedding_agent import generate_tool_embedding
from database.operations import store_embedding
from database.connection import get_supabase_client


async def fix_embeddings():
    client = get_supabase_client()
    tools = client.table("tools").select("*").execute().data
    embeddings = client.table("embeddings").select("tool_id").execute().data
    embedded_ids = {e["tool_id"] for e in embeddings}

    for tool in tools:
        if tool["id"] not in embedded_ids:
            label = tool["name"] or tool["website"]
            print(f"Generating embedding for: {label}")
            emb = await generate_tool_embedding(tool)
            if emb:
                store_embedding(tool["id"], emb)
                print(f"  Stored embedding ({len(emb)} dims)")
            else:
                print("  Failed to generate embedding")


if __name__ == "__main__":
    asyncio.run(fix_embeddings())
