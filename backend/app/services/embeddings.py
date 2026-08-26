import os
import time
from sentence_transformers import SentenceTransformer
from typing import List, Optional

_GLOBAL_MODEL: Optional[SentenceTransformer] = None

class LocalEmbeddingService:
    """Service wrapper for loading and invoking the local bge-small-en embedding model."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loader for the sentence-transformer model with global caching to prevent Windows HuggingFace cache collisions."""
        global _GLOBAL_MODEL
        if _GLOBAL_MODEL is None:
            # Handle potential Windows HuggingFace cache file lock collisions
            for attempt in range(3):
                try:
                    _GLOBAL_MODEL = SentenceTransformer(self.model_name)
                    break
                except PermissionError:
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
        return _GLOBAL_MODEL

    def embed_text(self, text: str) -> List[float]:
        """Encodes a single text string into a vector embedding."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Encodes a list of text document chunks into a list of vector embeddings."""
        embeddings = self.model.encode(documents, normalize_embeddings=True)
        return embeddings.tolist()

# Global singleton instance
embedding_service = LocalEmbeddingService()
