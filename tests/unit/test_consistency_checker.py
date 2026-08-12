from contracts.schemas.delta import (
    ConfidenceScore,
    DeltaChange,
    Operation,
    WorldStateDelta,
)
from contracts.schemas.world import KnowledgeGraphEdge, WorldState
from core.state.consistency import ConsistencyChecker, ConsistencyState


def test_consistency_checker_duplicate():
    checker = ConsistencyChecker()
    
    # State has a relationship
    state = WorldState()
    edge = KnowledgeGraphEdge(
        source="char-1",
        target="char-2",
        relation="FRIENDS",
        confidence=0.9
    )
    # Using private assignment for test
    state.semantic.knowledge_graph.edges.append(edge)
    
    # Delta tries to add same relationship
    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="test-trace",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.LINK,
                domain="semantic.knowledge_graph.edges",
                payload={"source": "char-1", "target": "char-2", "relation": "FRIENDS"},
                confidence=ConfidenceScore(confidence=0.9)
            )
        ]
    )
    
    result = checker.check(delta, state)
    assert result.state == ConsistencyState.DUPLICATE

def test_consistency_checker_superseding():
    checker = ConsistencyChecker()
    
    state = WorldState()
    edge = KnowledgeGraphEdge(
        source="char-1",
        target="char-2",
        relation="FRIEND_OF",
        confidence=0.9
    )
    state.semantic.knowledge_graph.edges.append(edge)
    
    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="test-trace",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.LINK,
                domain="semantic.knowledge_graph.edges",
                payload={"source": "char-1", "target": "char-2", "relation": "HOSTILE_TOWARDS"},
                confidence=ConfidenceScore(confidence=0.9)
            )
        ]
    )
    
    result = checker.check(delta, state)
    assert result.state == ConsistencyState.SUPERSEDING

def test_consistency_checker_valid():
    checker = ConsistencyChecker()
    state = WorldState()
    
    delta = WorldStateDelta(
        capability="test",
        provider="test",
        version="1.0",
        trace_id="test-trace",
        parent_world_state_id="1",
        operations=[
            DeltaChange(
                operation=Operation.ADD,
                domain="semantic.intentions",
                payload={"actor": "char-1", "intent": "run", "confidence": 0.9},
                confidence=ConfidenceScore(confidence=0.9)
            )
        ]
    )
    
    result = checker.check(delta, state)
    assert result.state == ConsistencyState.VALID
