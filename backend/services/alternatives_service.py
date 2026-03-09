"""Alternatives service — find similar tools using pgvector embeddings."""

from loguru import logger

from backend.models import AlternativeTool, ToolResponse
from database.operations import get_embedding_for_tool, vector_search


def get_alternatives(tool_id: str, limit: int = 5) -> list[AlternativeTool]:
    """Return the top-N similar tools based on embedding cosine similarity.

    1. Fetch the tool's stored embedding.
    2. Run ``match_tools`` RPC with that embedding (limit + 1 to account for self).
    3. Exclude the queried tool from results.
    4. Hydrate each match with full tool data.
    """
    embedding = get_embedding_for_tool(tool_id)
    if embedding is None:
        logger.warning(f"No embedding found for tool {tool_id}")
        return []

    # Fetch one extra so we can drop the source tool
    matches = vector_search(embedding, limit=limit + 1)

    alternatives: list[AlternativeTool] = []
    for match in matches:
        # match_tools RPC returns rows with 'id' (tool) and 'similarity',
        # or sometimes just 'tool_id' and 'similarity' depending on the RPC definition.
        matched_id = match.get("tool_id") or match.get("id")
        if matched_id == tool_id:
            continue

        # The RPC may return full tool fields — use them directly
        similarity = match.get("similarity", 0.0)
        tool_fields = {k: v for k, v in match.items() if k != "similarity"}
        if "id" not in tool_fields and "tool_id" in tool_fields:
            tool_fields["id"] = tool_fields.pop("tool_id")

        try:
            tool_resp = ToolResponse(**tool_fields)
        except Exception:
            # Minimal fallback if fields don't fully match
            from database.operations import get_tool_by_id
            tool_data = get_tool_by_id(matched_id)
            if not tool_data:
                continue
            tool_resp = ToolResponse(**tool_data)

        alternatives.append(
            AlternativeTool(
                tool=tool_resp,
                similarity=similarity,
                source="knowledge_base",
            )
        )

        if len(alternatives) >= limit:
            break

    return alternatives
