from typing import Any

from contracts.schemas.memory import RetrievalQuery, RetrievedMemory
from interfaces.memory.embedding import EmbeddingInterface
from storage.catalog.memory_repository import PostgresMemoryRepository


class SemanticRetrievalCapability:
    """
    Executes a RetrievalQuery via HybridRetriever and builds a deterministic ContextWindow.
    """

    def __init__(
        self,
        repository: PostgresMemoryRepository,
        embedding_provider: EmbeddingInterface,
    ):
        self._repository = repository
        self._embedding_provider = embedding_provider

    def execute(self, query: RetrievalQuery, context: dict[str, Any] | None = None) -> list[RetrievedMemory]:
        """
        Build deterministic context window from repository based on the structured query.
        """
        # Embed the query text
        query_embedding = self._embedding_provider.embed(query.query)
        
        # Execute hybrid retrieval
        retrieved_memories = self._repository.retrieve(query, query_embedding=query_embedding)
        
        # In a real pipeline, you would format this into a ContextWindow object.
        # Returning the raw retrieved memories allows the next capability (Synthesis) to structure it.
        return retrieved_memories
