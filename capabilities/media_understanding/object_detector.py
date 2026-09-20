from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger
from interfaces.vision.object_detector import ObjectDetectionProvider

logger = get_logger("capabilities.vision.object")


class ObjectDetectionCapability(BaseCapability):
    """
    Executes object detection via the registered provider.
    Replaces MockObjectDetectionCapability in the M2 pipeline.
    """

    def __init__(self, provider: ObjectDetectionProvider):
        self.provider = provider
        if not self.provider.health():
            logger.warning("object_detection_provider_unhealthy", provider=provider.__class__.__name__)

    @property
    def name(self) -> str:
        return "ObjectDetection"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        media_path = context.world.media.provenance.provider if context.world.media.provenance else context.media_id
        
        # Note: If no real physical media is mapped during M4, we assume media_id is path.
        # But per M2 patterns, media_id is passed as the path.
        
        objects = self.provider.detect_objects(media_path=media_path)
        
        logger.info(
            "object_detection_complete", 
            trace_id=trace_id, 
            object_count=len(objects)
        )
        
        # Merge objects into VisualContext
        return context.with_world(
            context.world.with_visual(
                context.world.visual.model_copy(update={"objects": objects})
            )
        )
