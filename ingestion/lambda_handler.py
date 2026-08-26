import os
import sys
import time
from typing import Dict, Any

# Ensure backend modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from fetch_github import fetch_trending_repos
from chunker import chunk_repository

try:
    from app.services.embeddings import embedding_service
    from app.services.qdrant_client import qdrant_service
except ImportError:
    embedding_service = None
    qdrant_service = None

def lambda_handler(event: Dict[str, Any] = None, context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint triggered by EventBridge Scheduler.
    Fetches trending GitHub repos, chunks text, generates embeddings, and upserts into Qdrant.
    """
    start_time = time.time()
    print("Starting GitHub trending repo ingestion...")

    try:
        repos = fetch_trending_repos(limit=5)
        print(f"Fetched {len(repos)} repositories from GitHub.")

        all_chunks = []
        for repo in repos:
            chunks = chunk_repository(repo)
            all_chunks.extend(chunks)

        print(f"Total chunks created: {len(all_chunks)}")

        if embedding_service and qdrant_service and all_chunks:
            texts = [c["text"] for c in all_chunks]
            vectors = embedding_service.embed_documents(texts)
            
            for chunk, vector in zip(all_chunks, vectors):
                chunk["vector"] = vector
                chunk["payload"] = chunk.get("metadata", {})
                chunk["payload"]["text"] = chunk["text"]

            qdrant_service.upsert_chunks(all_chunks)
            print(f"Successfully upserted {len(all_chunks)} chunks to vector index.")

        last_ingested_at = int(time.time())
        execution_duration = round(time.time() - start_time, 2)

        return {
            "statusCode": 200,
            "body": {
                "message": "Ingestion completed successfully.",
                "repos_processed": len(repos),
                "total_chunks": len(all_chunks),
                "last_ingested_at": last_ingested_at,
                "duration_seconds": execution_duration
            }
        }
    except Exception as e:
        print(f"Ingestion failed with error: {str(e)}")
        return {
            "statusCode": 500,
            "body": {
                "message": "Ingestion failed.",
                "error": str(e)
            }
        }

if __name__ == "__main__":
    res = lambda_handler()
    print("Local Lambda Execution Result:", res)

