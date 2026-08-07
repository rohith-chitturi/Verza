from typing import Any, Protocol

from contracts.schemas.world import AudioContext


class AudioSegmentationProvider(Protocol):
    """
    Interface for audio track and segment identification.
    """
    __version__: str = "1.0"
    
    def segment_audio(self, media_path: str) -> AudioContext:
        """
        Extracts structured tracks for speech, music, effects, ambience, and silence.
        """
        ...
        
    def health(self) -> bool:
        ...
        
    def capabilities(self) -> dict[str, Any]:
        ...
