from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PromptAsset(BaseModel):
    """
    A versioned asset defining how a VLM should be prompted.
    """
    model_config = ConfigDict(frozen=True)
    id: str
    version: str
    metadata: dict[str, str] = Field(default_factory=dict)
    system_prompt: str
    user_prompt_template: str
    few_shot_examples: list[dict[str, str]] = Field(default_factory=list)
    output_schema_version: str
    expected_schema: Any = None # E.g., a reference to the expected Pydantic model
    temperature: float = 0.0
    compatible_models: list[str] = Field(default_factory=list)
    fallback_prompt_id: str | None = None
