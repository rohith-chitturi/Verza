from typing import Protocol

from contracts.schemas.world import FaceDetection, TrackedFace


class FaceDetectionProvider(Protocol):
    """
    Protocol for algorithms/models that detect faces in media.
    """

    __version__: str

    def detect_faces(self, media_path: str) -> list[FaceDetection]:
        """
        Extracts face bounding boxes frame-by-frame.
        """
        ...


class FaceTrackingProvider(Protocol):
    """
    Protocol for algorithms/models that establish temporal identity across face detections.
    """

    __version__: str

    def track_faces(self, detections: list[FaceDetection]) -> list[TrackedFace]:
        """
        Links a chronological stream of face detections into persistent face trajectories.
        """
        ...
