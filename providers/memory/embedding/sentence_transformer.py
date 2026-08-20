from sentence_transformers import SentenceTransformer

from interfaces.memory.embedding import EmbeddingInterface


class SentenceTransformerProvider(EmbeddingInterface):
    """
    Local-first embedding provider using SentenceTransformers.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        self._model_name = model_name
        self._model = SentenceTransformer(self._model_name)
    
    def embed(self, text: str) -> list[float]:
        embedding = self._model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]
        
    @property
    def dimension(self) -> int:
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        return self._model.get_sentence_embedding_dimension() or 384
    
    @property
    def model_name(self) -> str:
        return self._model_name
