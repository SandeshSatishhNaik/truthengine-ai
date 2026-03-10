"""Database CRUD operations for tools, sources, reviews, and embeddings."""

from typing import Optional

from loguru import logger

from database.connection import get_supabase_client


# ── Tools ──────────────────────────────────────────────────────────────

def create_tool(data: dict) -> dict | None:
    """Insert a new tool record. Returns the created row."""
    try:
        client = get_supabase_client()
        result = client.table("tools").insert(data).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        logger.error(f"Failed to create tool: {e}")
    return None


def update_tool(tool_id: str, data: dict) -> dict | None:
    try:
        client = get_supabase_client()
        result = client.table("tools").update(data).eq("id", tool_id).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        logger.error(f"Failed to update tool {tool_id}: {e}")
    return None


def get_tool_by_id(tool_id: str) -> dict | None:
    try:
        client = get_supabase_client()
        result = client.table("tools").select("*").eq("id", tool_id).single().execute()
        return result.data
    except Exception:
        return None


def get_tool_by_website(website: str) -> dict | None:
    """Find a tool by its website URL (for dedup)."""
    try:
        client = get_supabase_client()
        result = client.table("tools").select("*").eq("website", website).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return None


def delete_tool(tool_id: str) -> bool:
    """Delete a tool and its related embeddings, sources, and reviews."""
    try:
        client = get_supabase_client()
        client.table("embeddings").delete().eq("tool_id", tool_id).execute()
        client.table("sources").delete().eq("tool_id", tool_id).execute()
        client.table("reviews").delete().eq("tool_id", tool_id).execute()
        client.table("tools").delete().eq("id", tool_id).execute()
        logger.info(f"Deleted tool {tool_id} and related records")
        return True
    except Exception as e:
        logger.error(f"Failed to delete tool {tool_id}: {e}")
        return False


def list_tools(limit: int = 20, offset: int = 0) -> list[dict]:
    try:
        client = get_supabase_client()
        result = (
            client.table("tools")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return []


def get_tools_by_category(category: str, limit: int = 20, offset: int = 0) -> list[dict]:
    try:
        client = get_supabase_client()
        result = (
            client.table("tools")
            .select("*")
            .eq("category", category)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list tools by category: {e}")
        return []


# ── Sources ────────────────────────────────────────────────────────────

def create_source(tool_id: str, source_url: str, content: str) -> dict | None:
    try:
        client = get_supabase_client()
        result = client.table("sources").insert({
            "tool_id": tool_id,
            "source_url": source_url,
            "content": content,
        }).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
    return None


def get_sources_for_tool(tool_id: str) -> list[dict]:
    try:
        client = get_supabase_client()
        result = client.table("sources").select("*").eq("tool_id", tool_id).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to get sources for tool {tool_id}: {e}")
        return []


# ── Reviews ────────────────────────────────────────────────────────────

def create_review(tool_id: str, review_text: str, sentiment: str) -> dict | None:
    try:
        client = get_supabase_client()
        result = client.table("reviews").insert({
            "tool_id": tool_id,
            "review_text": review_text,
            "sentiment": sentiment,
        }).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
    return None


def get_reviews_for_tool(tool_id: str) -> list[dict]:
    try:
        client = get_supabase_client()
        result = client.table("reviews").select("*").eq("tool_id", tool_id).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to get reviews for tool {tool_id}: {e}")
        return []


# ── Embeddings ─────────────────────────────────────────────────────────

def store_embedding(tool_id: str, embedding: list[float]) -> bool:
    """Store or update an embedding for a tool using the match_tools RPC."""
    try:
        client = get_supabase_client()
        # Upsert: delete existing then insert
        client.table("embeddings").delete().eq("tool_id", tool_id).execute()
        client.table("embeddings").insert({
            "tool_id": tool_id,
            "embedding": embedding,
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to store embedding for {tool_id}: {e}")
        return False


def get_embedding_for_tool(tool_id: str) -> list[float] | None:
    """Retrieve the stored embedding vector for a tool."""
    try:
        client = get_supabase_client()
        result = (
            client.table("embeddings")
            .select("embedding")
            .eq("tool_id", tool_id)
            .single()
            .execute()
        )
        if result.data:
            raw = result.data["embedding"]
            # Supabase may return the vector as a string like "[0.1, 0.2, ...]"
            if isinstance(raw, str):
                import json
                return json.loads(raw)
            return raw
    except Exception as e:
        logger.error(f"Failed to get embedding for tool {tool_id}: {e}")
    return None


def vector_search(query_embedding: list[float], limit: int = 10) -> list[dict]:
    """
    Perform vector similarity search using Supabase RPC.
    Requires the `match_tools` database function (see setup SQL).
    """
    try:
        client = get_supabase_client()
        result = client.rpc("match_tools", {
            "query_embedding": query_embedding,
            "match_count": limit,
        }).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


def text_search(query: str, limit: int = 10) -> list[dict]:
    """
    Fallback text-based search when embedding service is unavailable.
    Splits query into keywords and searches name, core_function, category using ilike.
    """
    _STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "what", "which", "who", "whom", "this", "that", "these", "those",
        "am", "do", "does", "did", "will", "would", "shall", "should",
        "can", "could", "may", "might", "must", "have", "has", "had",
        "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
        "they", "them", "their", "and", "but", "or", "nor", "not", "so",
        "for", "of", "in", "on", "at", "to", "from", "with", "by", "about",
        "how", "very", "most", "top",
    }
    try:
        client = get_supabase_client()
        # Extract meaningful keywords (3+ chars, not stop words)
        keywords = [
            w for w in query.lower().split()
            if len(w) >= 3 and w not in _STOP_WORDS
        ]
        if not keywords:
            keywords = [query.strip()]

        # Build OR filter: each keyword matches searchable fields
        filters = []
        for kw in keywords[:5]:  # cap at 5 keywords
            q = f"%{kw}%"
            filters.extend([
                f"name.ilike.{q}",
                f"core_function.ilike.{q}",
                f"category.ilike.{q}",
                f"pricing_model.ilike.{q}",
                f"free_tier_limits.ilike.{q}",
            ])

        result = (
            client.table("tools")
            .select("*")
            .or_(",".join(filters))
            .order("trust_score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        return []
