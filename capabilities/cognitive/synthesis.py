import time
from typing import Any

from pydantic import BaseModel, Field

from contracts.schemas.memory import RetrievedMemory
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.result import SynthesisResult
from contracts.schemas.world import WorldState
from interfaces.cognitive.inference import InferenceProvider


class SynthesisOutputSchema(BaseModel):
    narrative: str = Field(description="A cohesive natural language narrative synthesizing the context.")
    key_events: list[str] = Field(description="List of key events extracted from the context.")
    memory_citations: list[str] = Field(description="List of memory fragment IDs used to form the synthesis.")
    confidence: float = Field(description="Confidence score of the synthesis between 0.0 and 1.0.")


class SynthesisCapability:
    """
    SynthesisEngine: Passes deterministic ContextWindow to InferenceProvider and returns probabilistic SynthesisResult.
    """

    def __init__(self, inference_provider: InferenceProvider):
        self._inference_provider = inference_provider

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
            context_blocks.append(f"[ID: {rm.memory.id}] [{rm.memory.memory_type.upper()}] {rm.memory.content}")
            
        context_str = "\n".join(context_blocks)
        
        prompt_text = (
            f"Given the following contextual memory evidence:\n{context_str}\n\n"
            f"And the current query: '{query_text}'\n\n"
            "Synthesize a cohesive narrative. Cite the memory IDs you rely on. Your output must strictly follow the output schema."
        )
        
        start_time = time.time()
        
        try:
            prompt_asset = PromptAsset(
                id="synthesis_prompt", 
                version="1.0",
                system_prompt="You are a synthesis engine. Your job is to extract events and form a narrative.",
                user_prompt_template=prompt_text,
                output_schema_version="1.0"
            )
            output = self._inference_provider.infer_structured(
                input_text=query_text, 
                prompt=prompt_asset, 
                expected_schema=SynthesisOutputSchema
            )
            
            # Mypy safely checks types here
            assert isinstance(output, SynthesisOutputSchema)
            
            result = SynthesisResult(
                success=True,
                duration_ms=int((time.time() - start_time) * 1000),
                provider="gemini-inference",
                model="gemini-2.5-pro", # In a real implementation this comes from inference_provider.model_name but we hardcode for now or assume configured model
                narrative=output.narrative,
                key_events=output.key_events,
                timeline=[],
                memory_citations=output.memory_citations,
                evidence=[],
                confidence=output.confidence,
                provenance=None
            )
        except Exception as e:  # noqa: BLE001
            result = SynthesisResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                provider="gemini-inference",
                model="unknown",
                narrative=f"Synthesis failed: {e!s}",
                confidence=0.0,
            )

        return result
