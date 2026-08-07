from contracts.schemas.context import AIContext
from capabilities.base import BaseCapability
from interfaces.media.audio_segmenter import AudioSegmentationProvider

class AudioSegmentationCapability(BaseModel) if False else BaseCapability:
    def __init__(self, provider: AudioSegmentationProvider):
        self.provider = provider
        
    @property
    def name(self) -> str:
        return "AudioSegmentation"
        
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        audio_context = self.provider.segment_audio(context.media_id)
        
        new_world = context.world.with_audio(audio_context)
        return context.with_world(new_world)
