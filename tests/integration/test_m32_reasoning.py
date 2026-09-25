import os

import pytest

from bootstrap.container import VerzaContainer
from contracts.schemas.context import AIContext
from contracts.schemas.world import (
    KnowledgeGraphEdge,
    StructuredEvent,
    TemporalIntent,
)
from core.workflow.reasoning import ReasoningEngine
from providers.inference.gemini.provider import GeminiInferenceProvider


@pytest.mark.real_api
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Real API key required")
def test_m32_reasoning_engine_real_api() -> None:
    """
    Verifies that the ReasoningEngine can invoke the real Gemini API
    via the GeminiInferenceProvider, correctly synthesizing M3.1 interpretations
    into higher-level structural deltas (events, intents, relationships).
    """
    initial_context = AIContext(
        media_id="test-media-002",
        workflow_id="test-wf-002",
        language="en"
    )
    
    # Pre-populate world state with M3.1 interpretations
    initial_context.world.visual.scenes = [{"id": "scene-1", "summary": "Two people are standing in a hallway."}]
    
    # For typed models, we should inject actual models or dicts depending on what WorldState allows.
    # We will inject standard dictionary representation for characters and activities if that's what the schema accepts, 
    # but they might be proper objects. Let's see if we can just pass dictionaries. 
    # Actually, WorldState schema might require Character, Activity models.
    # Let's use the actual models to avoid validation errors if strict.
    from contracts.schemas.world import Activity, TrackedCharacter
    
    initial_context.world.visual.characters = [
        TrackedCharacter(id="char-A", tracking_id="tr-1", first_seen="00:00", last_seen="00:05", traits={"name": "Alice"}),
        TrackedCharacter(id="char-B", tracking_id="tr-2", first_seen="00:00", last_seen="00:05", traits={"name": "Bob"})
    ]
    initial_context.world.visual.activities = [
        Activity(id="act-1", actor_id="char-A", description="yelling", start="00:01", end="00:05", confidence=0.9)
    ]
    
    # Initialize DI Container
    container = VerzaContainer()
    
    # Force inference provider to be real Gemini
    gemini_inference = GeminiInferenceProvider(model_name=container.config.cognitive.reasoning_model())
    container.inference_provider.override(gemini_inference)
    
    # Get Reasoning Engine
    engine: ReasoningEngine = container.reasoning_engine()
    
    # Run reasoning engine
    final_state = engine.run(initial_context.world, initial_context.execution)
    
    # Assert structural invariants
    assert len(final_state.semantic.intentions) > 0, "Expected intentions to be inferred."
    assert isinstance(final_state.semantic.intentions[0], TemporalIntent)
    
    assert len(final_state.semantic.knowledge_graph.edges) > 0, "Expected relationships to be inferred."
    assert isinstance(final_state.semantic.knowledge_graph.edges[0], KnowledgeGraphEdge)
    
    assert len(final_state.semantic.events) > 0, "Expected narrative events to be inferred."
    assert isinstance(final_state.semantic.events[0], StructuredEvent)
    
    # Clean up
    container.inference_provider.reset_override()
