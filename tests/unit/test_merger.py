from contracts.schemas.delta import (
    ConfidenceScore,
    DeltaChange,
    Operation,
    WorldStateDelta,
)
from contracts.schemas.world import KnowledgeGraphEdge, WorldState
from core.state.merger import DeltaMerger


def test_merger_add_node():
    merger = DeltaMerger()
    state = WorldState()

    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="t-1",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.ADD,
                domain="semantic.knowledge_graph.nodes",
                payload={
                    "id": "node-1",
                    "type": "CHARACTER",
                    "properties": {},
                    "confidence": 0.9,
                },
                confidence=ConfidenceScore(confidence=0.9),
            )
        ],
    )

    new_state = merger.merge(state, delta)
    assert len(new_state.semantic.knowledge_graph.nodes) == 1
    assert new_state.semantic.knowledge_graph.nodes[0].id == "node-1"


def test_merger_link_edge():
    merger = DeltaMerger()
    state = WorldState()

    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="t-1",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.LINK,
                domain="semantic.knowledge_graph.edges",
                payload={
                    "id": "edge-1",
                    "source": "n1",
                    "target": "n2",
                    "relation": "LIKES",
                    "confidence": 0.8,
                },
                confidence=ConfidenceScore(confidence=0.8),
            )
        ],
    )

    new_state = merger.merge(state, delta)
    assert len(new_state.semantic.knowledge_graph.edges) == 1
    assert new_state.semantic.knowledge_graph.edges[0].relation == "LIKES"


def test_merger_unlink_edge():
    merger = DeltaMerger()
    state = WorldState()
    # Add an edge
    state.semantic.knowledge_graph.edges.append(
        KnowledgeGraphEdge(
            id="edge-1", source="n1", target="n2", relation="LIKES", confidence=0.9
        )
    )

    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="t-1",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.UNLINK,
                domain="semantic.knowledge_graph.edges",
                entity_id="edge-1",
                confidence=ConfidenceScore(confidence=0.9),
            )
        ],
    )

    new_state = merger.merge(state, delta)
    assert len(new_state.semantic.knowledge_graph.edges) == 0
