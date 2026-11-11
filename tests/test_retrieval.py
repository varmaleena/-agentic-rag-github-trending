from unittest.mock import Mock

from qdrant_client import QdrantClient, models

from app.services.embeddings import LocalEmbeddingService
from app.services.qdrant_client import QdrantService


def test_embedding_wrapper(monkeypatch):
    model = Mock()
    model.encode.side_effect = lambda text, **kwargs: Mock(
        tolist=lambda: [1.0] * 384 if isinstance(text, str) else [[1.0] * 384 for _ in text]
    )
    monkeypatch.setattr("app.services.embeddings._GLOBAL_MODEL", model)
    service = LocalEmbeddingService()
    assert len(service.embed_text("query")) == 384
    assert len(service.embed_documents(["first", "second"])) == 2
    assert model.encode.call_args.kwargs == {"normalize_embeddings": True}


def test_qdrant_flag_is_persisted():
    service = QdrantService()
    service._client = QdrantClient(":memory:")
    service.create_collection_if_not_exists()
    service.client.upsert(service.collection_name, [models.PointStruct(id=1, vector=[1.0] * 384)])
    service.flag_chunk_for_reindex(1, "Low score")
    point, = service.flagged_chunks()
    assert point.id == 1
    assert point.payload["needs_reindex"] is True
    assert point.payload["reindex_reason"] == "Low score"
    assert point.payload["reindex_flagged_at"] > 0
