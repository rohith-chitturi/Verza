import uuid
from typing import Any

from pydantic import BaseModel, create_model

from contracts.schemas.context import ExecutionContext
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import (
    KnowledgeGraphEdge,
    StructuredEvent,
    TemporalIntent,
)
from interfaces.cognitive.inference import InferenceProvider


class MockInferenceProvider(InferenceProvider):
    """
    Mock inference provider that returns deterministic structured output
    based on the prompt's target model.
    """

    provider_type = "mock"

    def get_metadata(self) -> dict[str, Any]:
        return {"name": "mock-inference", "type": "mock", "version": "1.0"}

    def infer_structured(
        self,
        input_text: str,
        prompt: PromptAsset,
        expected_schema: type[BaseModel],
        execution_context: ExecutionContext | None = None,
    ) -> BaseModel:

        # Determine what to return based on the reasoner invoking it
        if "intent" in prompt.id.lower():
            IntentOutputSchema = create_model(
                "IntentOutputSchema", intentions=(list[TemporalIntent], ...)
            )
            return IntentOutputSchema(
                intentions=[
                    TemporalIntent(
                        actor="character-001",
                        target="character-002",
                        intent="CONFRONT",
                        start="00:01",
                        end="00:05",
                        confidence=0.8,
                    )
                ]
            )

        elif "relationship" in prompt.id.lower():
            RelationshipOutputSchema = create_model(
                "RelationshipOutputSchema", edges=(list[KnowledgeGraphEdge], ...)
            )
            return RelationshipOutputSchema(
                edges=[
                    KnowledgeGraphEdge(
                        id=f"edge-{uuid.uuid4().hex[:8]}",
                        source="character-001",
                        target="character-002",
                        relation="HOSTILE_TOWARDS",
                        valid_from="scene-1",
                        valid_until="scene-5",
                        confidence=0.9,
                    )
                ]
            )

        elif "event" in prompt.id.lower():
            EventOutputSchema = create_model(
                "EventOutputSchema", events=(list[StructuredEvent], ...)
            )
            return EventOutputSchema(
                events=[
                    StructuredEvent(
                        id=f"event-{uuid.uuid4().hex[:8]}",
                        type="CONFRONTATION",
                        start="00:01",
                        end="00:05",
                        participants=["character-001", "character-002"],
                        causes=["argument"],
                        consequences=["character-002 leaves"],
                        confidence=0.88,
                    )
                ]
            )

        elif "synthesis" in prompt.id.lower():
            return expected_schema(
                narrative="Mock synthesized narrative.",
                key_events=["event 1", "event 2"],
                memory_citations=["mem-1", "mem-2"],
                confidence=0.95
            )

        # Fallback
        # Note: If expected_schema doesn't have an 'output' field, this will throw ValidationError.
        try:
            return expected_schema(output="Mock inference")
        except ValueError:
            # Try to return an empty instance if it has defaults, or just raise
            pass
            
        raise ValueError(f"No mock behavior defined for prompt ID: {prompt.id}")
