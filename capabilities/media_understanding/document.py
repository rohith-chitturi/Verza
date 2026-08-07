from contracts.schemas.context import AIContext
from capabilities.base import BaseCapability
from interfaces.vision.document_understanding import DocumentUnderstandingProvider

class DocumentUnderstandingCapability(BaseCapability):
    def __init__(self, provider: DocumentUnderstandingProvider):
        self.provider = provider
        
    @property
    def name(self) -> str:
        return "DocumentUnderstanding"
        
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        documents = self.provider.extract_text(context.media_id)
        
        new_visual = context.world.visual.model_copy(update={"documents": documents})
        new_world = context.world.with_visual(new_visual)
        return context.with_world(new_world)
