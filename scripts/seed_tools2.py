"""Seed the knowledge base with popular AI tools (batch 2)."""
import time
import httpx

API = "http://127.0.0.1:8000/api/v1/ingest"

URLS = [
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
            status = data.get("status", "error")
            msg = data.get("message", resp.text[:100])
            print(f"  -> {status}: {msg}")
            if "Rate limit" in str(data):
                print("  Rate limited! Waiting 60s...")
                time.sleep(60)
                # Retry
                resp = httpx.post(API, json={"url": url}, timeout=15)
                data = resp.json()
                print(f"  -> Retry: {data.get('status', 'error')}")
        except Exception as e:
            print(f"  -> Failed: {e}")
        time.sleep(6)

    print("\nDone submitting batch 2.")


if __name__ == "__main__":
    main()
