"""Seed the knowledge base with popular AI tools."""
import sys
import time
import httpx

API = "http://127.0.0.1:8000/api/v1/ingest"

URLS = [
    "https://openai.com",
    "https://anthropic.com",
    "https://midjourney.com",
    "https://stability.ai",
    "https://replicate.com",
    "https://ollama.com",
    "https://elevenlabs.io",
    "https://perplexity.ai",
    "https://together.ai",
    "https://fireworks.ai",
    "https://deepgram.com",
    "https://cohere.com",
    "https://mistral.ai",
    "https://runwayml.com",
    "https://leonardo.ai",
    "https://langchain.com",
    "https://pinecone.io",
    "https://weaviate.io",
    "https://unstructured.io",
    "https://streamlit.io",
]


def main():
    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] Submitting: {url}")
        try:
            resp = httpx.post(API, json={"url": url}, timeout=15)
            data = resp.json()
            print(f"  -> {data.get('status', 'error')}: {data.get('message', resp.text[:100])}")
        except Exception as e:
            print(f"  -> Failed: {e}")
        # Small delay to avoid overwhelming the server
        time.sleep(2)

    print("\nAll URLs submitted. Processing will happen in the background.")
    print("Monitor progress with: Get-Content logs/truthengine.log -Tail 30 -Wait")


if __name__ == "__main__":
    main()
