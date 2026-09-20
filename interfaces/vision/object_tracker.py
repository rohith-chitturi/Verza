from typing import Protocol

from contracts.schemas.world import DetectedObject, TrackedObject


class ObjectTrackingProvider(Protocol):
    """
    Protocol for algorithms/models that establish temporal object identity (trajectories)
    across a stream of detections (e.g., IoU, SORT, ByteTrack).
    """

    __version__: str

    def track_objects(self, detections: list[DetectedObject]) -> list[TrackedObject]:
        """
        Executes tracking over a list of detections, linking them by identity.
        The detections should be passed in chronological order (or will be sorted internally).
        """
        ...
