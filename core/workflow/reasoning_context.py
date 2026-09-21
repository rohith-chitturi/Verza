import json

from contracts.schemas.world import WorldState


class ReasoningContextBuilder:
    """
    Builds structured textual representation of the WorldState for reasoning models.
    Centralizes serialization logic and ensures deterministic context generation.
    """
    
    @staticmethod
    def build_intent_context(world_state: WorldState) -> str:
        """Context specifically for intent reasoning."""
        context_data = {
            "characters": world_state.visual.characters,
            "activities": [a.model_dump() for a in world_state.visual.activities],
            "scenes": world_state.visual.scenes,
        }
        return json.dumps(context_data, indent=2)
        
    @staticmethod
    def build_relationship_context(world_state: WorldState) -> str:
        """Context specifically for relationship reasoning."""
        context_data = {
            "characters": world_state.visual.characters,
            "activities": [a.model_dump() for a in world_state.visual.activities],
            "intentions": [i.model_dump() for i in world_state.semantic.intentions],
        }
        return json.dumps(context_data, indent=2)
        
    @staticmethod
    def build_event_context(world_state: WorldState) -> str:
        """Context specifically for event reasoning."""
        context_data = {
            "intentions": [i.model_dump() for i in world_state.semantic.intentions],
            "relationships": [r.model_dump() for r in world_state.semantic.relationships],
            "activities": [a.model_dump() for a in world_state.visual.activities],
            "scenes": world_state.visual.scenes,
        }
        return json.dumps(context_data, indent=2)
