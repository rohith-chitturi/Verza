import random

from interfaces.memory.embedding import EmbeddingInterface


class MockEmbeddingProvider(EmbeddingInterface):
    """
    Mock embedding provider for unit tests and fast local validation.
    """
    
    def __init__(self, dimension: int = 384):
        super().__init__()
        self._dimension = dimension
        
    def embed(self, text: str) -> list[float]:
        # Return random normalized vector
        vec = [random.uniform(-1, 1) for _ in range(self._dimension)]
        magnitude = sum(x**2 for x in vec) ** 0.5
        if magnitude == 0:
            return [0.0] * self._dimension
        return [x / magnitude for x in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
        
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return "mock-embedding-v1"
