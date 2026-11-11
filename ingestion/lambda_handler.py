import logging
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from fetch_github import fetch_repository, fetch_trending_repos
from chunker import chunk_repository
from screening import contains_prompt_injection
from secrets_config import read_secret
from app.config import settings
from app.services.embeddings import embedding_service
from app.services.qdrant_client import qdrant_service

logger = logging.getLogger(__name__)


def index_repository(repo):
    if any(contains_prompt_injection(repo[field]) for field in ("description", "readme_content")):
        logger.warning("Skipped repository with suspected prompt injection: %s", repo["repo_name"])
        return set()
    chunks = chunk_repository(repo)
    vectors = embedding_service.embed_documents([chunk["text"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk["vector"] = vector
        chunk["payload"] = {**chunk["metadata"], "text": chunk["text"], "needs_reindex": False}
    qdrant_service.upsert_chunks(chunks)
    return {chunk["id"] for chunk in chunks}


def lambda_handler(event=None, context=None):
    if secret_id := os.environ.get("QDRANT_API_KEY_SECRET_ARN"):
        settings.QDRANT_API_KEY = read_secret(secret_id)
    qdrant_service.create_collection_if_not_exists()
    flagged = defaultdict(set)
    for point in qdrant_service.flagged_chunks():
        flagged[point.payload["repo_name"]].add(point.id)

    chunks_indexed = 0
    refreshed = set()
    for repo_name, point_ids in flagged.items():
        try:
            current_ids = index_repository(fetch_repository(repo_name))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
            current_ids = set()
            logger.warning("Repository unavailable on GitHub: %s", repo_name)

        if obsolete_ids := point_ids - current_ids:
            qdrant_service.client.delete(
                qdrant_service.collection_name, points_selector=list(obsolete_ids), wait=True
            )
        chunks_indexed += len(current_ids)
        refreshed.add(repo_name)

    repos = fetch_trending_repos(limit=5)
    for repo in repos:
        if repo["repo_name"] not in refreshed:
            chunks_indexed += len(index_repository(repo))
            refreshed.add(repo["repo_name"])

    return {
        "statusCode": 200,
        "body": {
            "repos_processed": len(refreshed),
            "total_chunks": chunks_indexed,
            "last_ingested_at": int(time.time()),
        },
    }


if __name__ == "__main__":
    print(lambda_handler())
