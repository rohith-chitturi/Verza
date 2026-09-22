from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger
from interfaces.vision.face_tracker import FaceDetectionProvider

logger = get_logger("capabilities.vision.face_detector")


class FaceDetectionCapability(BaseCapability):
    """
    Executes frame-by-frame face detection over the given media.
    """

    def __init__(self, provider: FaceDetectionProvider):
        self.provider = provider

    @property
    def name(self) -> str:
        return "FaceDetection"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        media_path = context.media_id
        detections = self.provider.detect_faces(media_path=media_path)
        
        logger.info(
            "face_detection_complete", 
            trace_id=trace_id, 
            detections_count=len(detections)
        )
        
        # We don't save raw FaceDetection to WorldState directly in Phase 7.
        # But wait! 
        # The WorldState VisualContext has tracked_faces, but what about raw FaceDetection?
        # The user's architecture diagram showed: FaceDetection[] passed to IoUFaceTracker, 
        # and then TrackedFace[] saved to WorldState.visual.faces.
        # However, how does FaceDetection pass from FaceDetectionCapability to FaceTrackingCapability?
        # In Verza, capabilities communicate via AIContext/WorldState.
        # If we don't store raw detections, how does the tracker see them?
        # The current design of M4 workflow passes the full AIContext sequentially.
        # If we don't want to persist raw face detections, we could temporarily attach them to Context,
        # OR we can add `face_detections: list[FaceDetection] = Field(...)` to VisualContext.
        # Let's add them to VisualContext dynamically or formally. 
        # Actually, for Object Detection we added `objects: list[DetectedObject]`.
        # So we should add `face_detections: list[FaceDetection]` to `VisualContext` in world.py.
        # Let's assume we do this in Step 6 (I will update world.py again).
        
        return context.with_world(
            context.world.with_visual(
                context.world.visual.model_copy(update={"face_detections": detections})
            )
        )
