import time

from qdrant_client import QdrantClient, models

from app.config import settings


class QdrantService:
    def __init__(self, host=None, port=None, collection_name=None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port, timeout=10)
        return self._client

    def create_collection_if_not_exists(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                self.collection_name, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

    def upsert_chunks(self, chunks):
        if chunks:
            self.client.upsert(self.collection_name, [
                models.PointStruct(id=chunk["id"], vector=chunk["vector"], payload=chunk["payload"])
                for chunk in chunks
            ], wait=True)
        return True

    def search_similar(self, query_vector, top_k=5):
        results = self.client.query_points(self.collection_name, query=query_vector, limit=top_k).points
        return [{"id": r.id, "score": r.score, "payload": r.payload or {}} for r in results]

    def flag_chunk_for_reindex(self, chunk_id, reason):
        self.client.set_payload(
            self.collection_name,
            {"needs_reindex": True, "reindex_reason": reason, "reindex_flagged_at": int(time.time())},
            points=[chunk_id], wait=True,
        )

    def flagged_chunks(self):
        offset = None
        condition = models.Filter(must=[
            models.FieldCondition(key="needs_reindex", match=models.MatchValue(value=True))
        ])
        while True:
            points, offset = self.client.scroll(
                self.collection_name, scroll_filter=condition, offset=offset, limit=100
            )
            yield from points
            if offset is None:
                return


qdrant_service = QdrantService()
