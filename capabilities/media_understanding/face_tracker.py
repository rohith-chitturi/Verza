from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger
from interfaces.vision.face_tracker import FaceTrackingProvider

logger = get_logger("capabilities.vision.face_tracker")


class FaceTrackingCapability(BaseCapability):
    """
    Executes face tracking by correlating FaceDetection instances into persistent TrackedFace trajectories.
    """

    def __init__(self, provider: FaceTrackingProvider):
        self.provider = provider

    @property
    def name(self) -> str:
        return "FaceTracking"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        detections = getattr(context.world.visual, "face_detections", [])
        
        if not detections:
            logger.info("face_tracking_skipped", trace_id=trace_id, reason="no_detections")
            return context
            
        tracked_faces = self.provider.track_faces(detections=detections)
        
        logger.info(
            "face_tracking_complete", 
            trace_id=trace_id, 
            tracked_faces_count=len(tracked_faces)
        )
        
        return context.with_world(
            context.world.with_visual(
                context.world.visual.model_copy(update={"faces": tracked_faces})
            )
        )
