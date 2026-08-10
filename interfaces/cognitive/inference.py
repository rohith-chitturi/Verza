from typing import Any
from pydantic import BaseModel

from contracts.schemas.context import ExecutionContext
from contracts.schemas.prompt import PromptAsset


class InferenceProvider:
    """
    Provider-neutral interface for structured reasoning.
    Could be backed by a VLM, LLM, or deterministic rule engine.
    """
    def infer_structured(
        self,
        context_data: dict[str, Any],
        prompt: PromptAsset,
        execution_context: ExecutionContext | None = None
    ) -> BaseModel:
        raise NotImplementedError
