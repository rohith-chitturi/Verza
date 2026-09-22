from typing import Protocol

from contracts.schemas.world import Activity, AudioContext, VisualContext


class ActivityRecognitionProvider(Protocol):
    """
    Protocol for Activity Recognition.
    
    Synthesizes signals from VisualContext and AudioContext into high-level activities.
    For M2 Phase 8, this is implemented heuristically (without a learned model).
    """

    def recognize_activities(
        self,
        visual_context: VisualContext,
        audio_context: AudioContext,
    ) -> list[Activity]:
        ...
