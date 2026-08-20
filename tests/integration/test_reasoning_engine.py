from bootstrap.container import VerzaContainer
from contracts.schemas.context import ExecutionContext
from contracts.schemas.world import WorldState


def test_reasoning_engine_integration():
    container = VerzaContainer()
    engine = container.reasoning_engine()

    initial_state = WorldState()
    context = ExecutionContext(workflow_id="w-1", trace_id="t-1", correlation_id="c-1")

    final_state = engine.run(initial_state, context)

    # Assert that Intents were added
    assert len(final_state.semantic.intentions) == 1
    assert final_state.semantic.intentions[0].intent == "CONFRONT"

    # Assert that Relationships (KnowledgeGraph edges) were linked
    assert len(final_state.semantic.knowledge_graph.edges) == 1
    assert final_state.semantic.knowledge_graph.edges[0].relation == "HOSTILE_TOWARDS"

    # Assert that Events were added
    assert len(final_state.semantic.events) == 1
    assert final_state.semantic.events[0].type == "CONFRONTATION"

    # The DeltaJournal should have recorded all operations
    journal = container.delta_journal()
    history = journal.get_history()
    # 3 deltas: Intent, Relationship, Event
    assert len(history) == 3
