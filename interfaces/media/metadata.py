from typing import Any, Protocol

from contracts.schemas.world import MediaContext


class MetadataProvider(Protocol):
    """
    Interface for extracting video metadata (e.g. via FFmpeg).
    """
    __version__: str = "1.0"
    
    def extract_metadata(self, media_path: str) -> MediaContext:
        """
        Extracts foundational metadata (resolution, framerate, codecs) from a media file.
        """
        ...
        
    def health(self) -> bool:
        ...
        
    def capabilities(self) -> dict[str, Any]:
        ...
