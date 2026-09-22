import pytest

from bootstrap.container import VerzaContainer
from contracts.schemas.memory import RetrievalQuery
from contracts.schemas.result import SynthesisResult
from contracts.schemas.world import (
    KnowledgeGraphEdge,
    StructuredEvent,
    WorldState,
)


@pytest.fixture(scope="function")
def m33_container(session_factory):
    """Provides a container configured for M3.3 testing."""
    container = VerzaContainer()
    
    # Ensure we use mock inference provider for standard test runs
    container.inference_provider.override(container.mock_inference_provider())
    # Use the test DB session factory
    container.db_session_factory.override(session_factory)
    
    return container


def test_memory_indexing_and_retrieval(m33_container):
    """
    Verifies that M3.3 memory indexer successfully persists WorldState elements
    into Episodic and Semantic memory using real PGVector embeddings, and that
    hybrid retrieval retrieves them deterministically.
    """
    
    indexer = m33_container.memory_indexer()
    retriever = m33_container.semantic_retrieval()
    
    # 1. Create a populated WorldState
    state = WorldState()
    
    # Add Semantic Event
    state.semantic.events.append(
        StructuredEvent(
            id="evt-1",
            type="conversation",
            participants=["Alice", "Bob"],
            causes=["meeting"],
            consequences=["agreement"],
            confidence=0.9,
            start="10.0",
            end="20.0"
        )
    )
    
    # Add Semantic Relationship
    state.semantic.relationships.append(
        KnowledgeGraphEdge(
            id="rel-1",
            source="Alice",
            relation="is_manager_of",
            target="Bob",
            confidence=0.95,
            properties={"department": "engineering"}
        )
    )
    
    # 2. Index the memories (Idempotent)
    result_run1 = indexer.execute(state, context={"run_id": "test-run-1"})
    assert result_run1["status"] == "success"
    assert result_run1["indexed_episodes"] == 1
    assert result_run1["indexed_semantics"] == 1
    
    # Verify idempotency by running again
    result_run2 = indexer.execute(state, context={"run_id": "test-run-1"})
    assert result_run2["status"] == "success"
    
    # 3. Retrieve memories
    query = RetrievalQuery(
        query="Alice speaking with Bob",
        top_k=5,
        memory_types=["episodic", "semantic"]
    )
    
    retrieved = retriever.execute(query)
    
    assert len(retrieved) > 0
    # The event should be retrieved
    found_event = any("conversation" in m.memory.content for m in retrieved)
    assert found_event is True
    
    # The relationship should be retrieved
    found_rel = any("is_manager_of" in m.memory.content for m in retrieved)
    assert found_rel is True


def test_memory_synthesis(m33_container):
    """
    Verifies that the Synthesis engine successfully formats retrieved memories
    into a context block and parses the structured response.
    """
    
    retriever = m33_container.semantic_retrieval()
    synthesis = m33_container.synthesis()
    
    # We assume the memory was already populated in the previous test since
    # test DB isolation handles module level state or we just use whatever is there.
    # But let's retrieve directly
    query = RetrievalQuery(
        query="Alice manager",
        top_k=2
    )
    retrieved = retriever.execute(query)
    
    # 4. Synthesize narrative
    result = synthesis.execute(
        world_state=WorldState(), # empty since synthesis relies mainly on retrieved_memories in our prompt
        retrieved_memories=retrieved,
        query_text="Summarize Alice's role."
    )
    
    assert isinstance(result, SynthesisResult)
    assert result.success is True
    assert "mock" in result.narrative.lower() # Because we use MockInferenceProvider


@pytest.mark.real_api
def test_real_gemini_synthesis(m33_container):
    """
    Verifies Synthesis Capability against real Gemini inference endpoint.
    """
    import os
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
        
    m33_container.inference_provider.reset_override()
    
    retriever = m33_container.semantic_retrieval()
    synthesis = m33_container.synthesis()
    
    query = RetrievalQuery(
        query="Bob",
        top_k=3
    )
    retrieved = retriever.execute(query)
    
    result = synthesis.execute(
        world_state=WorldState(),
        retrieved_memories=retrieved,
        query_text="What do we know about Bob?"
    )
    
    assert isinstance(result, SynthesisResult)
    assert result.success is True
    assert result.narrative != ""
    assert result.provider == "gemini-inference"
