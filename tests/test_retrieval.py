import pytest
from app.services.embeddings import LocalEmbeddingService

def test_local_embedding_dimensions():
    """Verify local bge-small-en model generates 384-dimensional normalized float vectors."""
    service = LocalEmbeddingService()
    embedding = service.embed_text("Sample trending repository query")
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert isinstance(embedding[0], float)

def test_embed_documents_batch():
    """Verify batch embedding generation for multiple text chunks."""
    service = LocalEmbeddingService()
    chunks = [
        "First repo chunk describing an AI agent framework.",
        "Second repo chunk detailing installation via pip."
    ]
    embeddings = service.embed_documents(chunks)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384
