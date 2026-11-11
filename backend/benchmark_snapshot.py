"""Load the pinned GitHub README corpus into an in-process Qdrant collection."""
import base64
import hashlib
import json
import sys
from pathlib import Path

from qdrant_client import QdrantClient

from app.services.qdrant_client import qdrant_service

sys.path.append(str(Path(__file__).resolve().parents[1] / "ingestion"))
from fetch_github import github_client
from lambda_handler import index_repository


def index_snapshot(manifest, cache=None):
    repos = json.loads(manifest.read_text(encoding="utf-8"))
    cached = {}
    if cache:
        cached = {row["repo_name"]: row["readme_content"] for row in json.loads(cache.read_text(encoding="utf-8"))}

    qdrant_service._client = QdrantClient(":memory:")
    qdrant_service.create_collection_if_not_exists()
    with github_client() as client:
        for entry in repos:
            name, blob = entry["repo_name"], entry["readme_blob"]
            if name in cached:
                data = cached[name].encode("utf-8")
            else:
                response = client.get(f"/repos/{name}/git/blobs/{blob}")
                response.raise_for_status()
                data = base64.b64decode(response.json()["content"])
            digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            if digest != blob:
                raise ValueError(f"README hash mismatch for {name}")
            if not index_repository({**entry, "readme_content": data.decode("utf-8")}):
                raise ValueError(f"Snapshot repository was not indexed: {name}")
    return qdrant_service.client.count(qdrant_service.collection_name).count
