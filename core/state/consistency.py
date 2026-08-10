from enum import Enum

from contracts.schemas.delta import Operation, WorldStateDelta
from contracts.schemas.world import WorldState
from core.telemetry.logging import get_logger

logger = get_logger("core.state.consistency")

class ConsistencyState(str, Enum):
    VALID = "VALID"
    CONFLICTING = "CONFLICTING"
    DUPLICATE = "DUPLICATE"
    SUPERSEDING = "SUPERSEDING"
    UNCERTAIN = "UNCERTAIN"

class ConsistencyResult:
    def __init__(self, state: ConsistencyState, reason: str = ""):
        self.state = state
        self.reason = reason

class ConsistencyChecker:
    """
    Analyzes validated WorldStateDeltas against the current WorldState
    to detect semantic contradictions, duplicates, or superseding facts.
    """
    
    def check(self, delta: WorldStateDelta, current_state: WorldState) -> ConsistencyResult:
        # A full implementation would build a temporal logic graph and detect contradictions.
        # For M3.2 prototype, we will implement some basic heuristic checks.
        
        for op in delta.operations:
            if op.domain == "semantic.knowledge_graph.edges":
                # Check if this edge already exists (DUPLICATE) or contradicts (CONFLICTING)
                kg = current_state.semantic.knowledge_graph
                
                # Check for duplicate edge
                if op.operation == Operation.ADD or op.operation == Operation.LINK:
                    source = op.payload.get("source")
                    target = op.payload.get("target")
                    relation = op.payload.get("relation")
                    
                    for existing_edge in kg.edges:
                        if (existing_edge.source == source and 
                            existing_edge.target == target and 
                            existing_edge.relation == relation):
                            
                            # If temporal bounds overlap, it's a duplicate or superseding
                            # Simplifying for now:
                            logger.info(f"Duplicate relation detected: {source} {relation} {target}")
                            return ConsistencyResult(ConsistencyState.DUPLICATE, "Relation already exists")
                            
                        # Example contradiction check:
                        if (existing_edge.source == source and 
                            existing_edge.target == target and
                            existing_edge.relation == "FRIEND_OF" and relation == "HOSTILE_TOWARDS"):
                            
                            # This might be superseding if time has passed, or conflicting
                            logger.info(f"Potential conflict/superseding: {source} {relation} {target} vs {existing_edge.relation}")
                            return ConsistencyResult(ConsistencyState.SUPERSEDING, "Relationship changed over time")

        # By default, assume valid
        return ConsistencyResult(ConsistencyState.VALID)
