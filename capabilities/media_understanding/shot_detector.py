from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from interfaces.vision.shot_detector import ShotDetectionProvider


class ShotDetectionCapability(BaseCapability):
    def __init__(self, provider: ShotDetectionProvider):
        self.provider = provider

    @property
    def name(self) -> str:
        return "ShotDetection"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        shots = self.provider.detect_shots(context.media_id)

        # Clone existing visual context and add shots
        # Since pydantic models are frozen, we'd use model_copy(update=...)
        new_visual = context.world.visual.model_copy(update={"shots": shots})

        new_world = context.world.with_visual(new_visual)
        return context.with_world(new_world)
