
from contracts.schemas.prompt import PromptAsset
from core.telemetry.logging import get_logger

logger = get_logger("core.prompts.registry")

class PromptRegistry:
    """
    Registry for managing versioned PromptAssets.
    """
    def __init__(self) -> None:
        self._prompts: dict[str, PromptAsset] = {}
        
    def register(self, prompt: PromptAsset) -> None:
        key = f"{prompt.id}@{prompt.version}"
        self._prompts[key] = prompt
        logger.info(f"Registered prompt asset: {key}")
        
    def get_prompt(self, prompt_id: str, version: str) -> PromptAsset:
        key = f"{prompt_id}@{version}"
        if key not in self._prompts:
            raise ValueError(f"Prompt asset {key} not found in registry.")
        return self._prompts[key]
