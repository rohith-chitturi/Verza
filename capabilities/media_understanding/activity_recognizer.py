from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger
from interfaces.cognitive.activity_recognizer import ActivityRecognitionProvider

logger = get_logger("capabilities.media_understanding.activity_recognizer")


class ActivityRecognitionCapability(BaseCapability):
    """
    Phase 8: Heuristic Activity Recognition Capability.
    Consumes VisualContext and AudioContext to produce Activity hypotheses.
    """

    def __init__(self, provider: ActivityRecognitionProvider):
        super().__init__()
        self.provider = provider

    @property
    def name(self) -> str:
        return "Activity Recognition"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        logger.info("activity_recognition_started", trace_id=trace_id)
        
        # We need both visual and audio context to extract meaningful cross-modal activities.
        activities = self.provider.recognize_activities(
            visual_context=context.world.visual,
            audio_context=context.world.audio
        )
        
        # WorldState is immutable, so we create a new VisualContext and WorldState
        new_visual = context.world.visual.model_copy(update={"activities": activities})
        new_world = context.world.with_visual(new_visual)
        new_context = context.with_world(new_world)
        
        logger.info("activity_recognition_completed", count=len(activities), trace_id=trace_id)
        return new_context
