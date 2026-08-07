from typing import Any, Protocol


class ShotDetectionProvider(Protocol):
    """
    Interface for visual shot and sequence boundary detection.
    """
    __version__: str = "1.0"
    
    def detect_shots(self, media_path: str) -> list[dict[str, Any]]:
        """
        Returns a list of shots (start, end frames/times).
        """
        ...
        
    def health(self) -> bool:
        ...
        
    def capabilities(self) -> dict[str, Any]:
        ...
