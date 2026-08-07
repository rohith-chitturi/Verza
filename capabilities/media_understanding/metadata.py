from contracts.schemas.context import AIContext
from capabilities.base import BaseCapability
from interfaces.media.metadata import MetadataProvider

class MetadataExtractionCapability(BaseModel) if False else BaseCapability:
    def __init__(self, provider: MetadataProvider):
        self.provider = provider
        
    @property
    def name(self) -> str:
        return "MetadataExtraction"
        
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        media_context = self.provider.extract_metadata(context.media_id)
        # Immutably update the WorldState
        new_world = context.world.with_media(media_context)
        return context.with_world(new_world)
