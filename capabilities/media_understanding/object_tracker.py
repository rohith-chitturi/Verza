from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger
from interfaces.vision.object_tracker import ObjectTrackingProvider

logger = get_logger("capabilities.vision.tracking")


class ObjectTrackingCapability(BaseCapability):
    """
    Executes object tracking by mathematically associating frame-level DetectedObject instances
    into persistent TrackedObject instances representing trajectories.
    """

    def __init__(self, provider: ObjectTrackingProvider):
        self.provider = provider

    @property
    def name(self) -> str:
        return "ObjectTracking"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        detections = context.world.visual.objects
        
        if not detections:
            logger.info("object_tracking_skipped", trace_id=trace_id, reason="no_detections")
            return context
            
        tracked_objects = self.provider.track_objects(detections=detections)
        
        logger.info(
            "object_tracking_complete", 
            trace_id=trace_id, 
            tracked_objects_count=len(tracked_objects)
        )
        
        # Merge tracked_objects into VisualContext
        return context.with_world(
            context.world.with_visual(
                context.world.visual.model_copy(update={"tracked_objects": tracked_objects})
            )
        )
