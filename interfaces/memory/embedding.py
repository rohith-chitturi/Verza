from abc import abstractmethod

from interfaces.base import BaseInterface


class EmbeddingInterface(BaseInterface):
    """
    Interface for embedding models used in the Memory Indexer.
    Converts text content into vector embeddings for similarity search.
    """
    
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate a dense vector embedding for the given text."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this provider."""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the embedding model being used."""
