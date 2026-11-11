from unittest.mock import Mock

from qdrant_client import QdrantClient, models

from app.services.embeddings import LocalEmbeddingService
from app.services.qdrant_client import QdrantService


def test_embedding_wrapper(monkeypatch):
    model = Mock()
    model.embed.side_effect = lambda texts: (Mock(tolist=lambda: [1.0] * 384) for _ in texts)
    service = LocalEmbeddingService()
    monkeypatch.setattr(LocalEmbeddingService, "model", model)

    assert len(service.embed_text("query")) == 384
    assert len(service.embed_documents(["first", "second"])) == 2
    model.embed.assert_called_with(["first", "second"])


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
