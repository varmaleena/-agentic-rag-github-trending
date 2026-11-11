from functools import cached_property


class LocalEmbeddingService:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model_name = model_name

    @cached_property
    def model(self):
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=self.model_name, threads=2)

    def embed_text(self, text):
        return next(self.model.embed([text])).tolist()

    def embed_documents(self, documents):
        return [vector.tolist() for vector in self.model.embed(documents)]


embedding_service = LocalEmbeddingService()
