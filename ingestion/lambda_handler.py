import os
import sys
import time
from typing import Dict, Any

# Add parent backend directory to path if running inside AWS Lambda / standalone
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from fetch_github import fetch_trending_repos
from chunker import chunk_repository

def lambda_handler(event: Dict[str, Any] = None, context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint triggered by EventBridge Scheduler.
    Fetches trending GitHub repos, chunks text, generates embeddings, and upserts into Qdrant.
    """
    start_time = time.time()
    print("Starting GitHub trending repo ingestion...")

    try:
        # 1. Fetch recent trending repos
        repos = fetch_trending_repos(limit=5)
        print(f"Fetched {len(repos)} repositories from GitHub.")

        all_chunks = []
        for repo in repos:
            chunks = chunk_repository(repo)
            all_chunks.extend(chunks)

        print(f"Total chunks created: {len(all_chunks)}")

        # Note: Vector embedding & Qdrant upserting call qdrant_service / embedding_service
        # which will be active when qdrant_service implementation stub is completed.
        
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
    # Local invocation test
    res = lambda_handler()
    print("Local Lambda Execution Result:", res)
