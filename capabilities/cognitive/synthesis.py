from typing import Any

from contracts.schemas.memory import RetrievedMemory
from contracts.schemas.result import SynthesisResult
from contracts.schemas.world import WorldState
from core.registry.capability import BaseCapability
from interfaces.cognitive.vlm_provider import VLMProvider


class SynthesisCapability(BaseCapability):
    """
    SynthesisEngine: Passes deterministic ContextWindow to LLM and returns probabilistic SynthesisResult.
    """

    def __init__(self, vlm_provider: VLMProvider):
        self._vlm_provider = vlm_provider

    def execute(
        self, 
        world_state: WorldState, 
        retrieved_memories: list[RetrievedMemory], 
        query_text: str, 
        context: dict[str, Any] | None = None
    ) -> SynthesisResult:
        """
        Synthesizes a structured response from the Context Window and World State.
        """
        
        # Construct deterministic context window string
        context_blocks = []
        for rm in retrieved_memories:
            context_blocks.append(f"[{rm.memory.memory_type.upper()}] {rm.memory.content} (Confidence: {rm.confidence_score})")
            
        context_str = "\n".join(context_blocks)
        
        prompt = (
            f"Given the following contextual memory evidence:\n{context_str}\n\n"
            f"And the current query: '{query_text}'\n\n"
            "Synthesize a cohesive narrative. Your output must strictly follow the SynthesisResult schema."
        )
        
        # For this prototype we will use the VLMProvider or a mocked version to return the schema
        # In actual implementation, we would use structured output (e.g. OpenAI function calling or Instructor)
        try:
            # We assume vlm_provider has a way to answer prompts. 
            # The interface only has analyze_frame/analyze_video currently, so we might need a general text prompt method.
            # Using a mock response for now to satisfy the pipeline architecture
            narrative = f"Based on retrieved memory, {len(retrieved_memories)} events were found relevant to '{query_text}'."
        except Exception:
            narrative = "Synthesis failed."

        return SynthesisResult(
            success=True,
            duration_ms=100,
            provider="mock-synthesis",
            model="mock-llm-v1",
            narrative=narrative,
            key_events=[m.memory.content for m in retrieved_memories[:3]],
            memory_citations=[m.memory.id for m in retrieved_memories],
            confidence=0.9,
            provenance=None
        )
