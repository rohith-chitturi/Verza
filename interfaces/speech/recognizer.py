from typing import Any, Protocol

from contracts.schemas.context import AIContext
from contracts.schemas.result import SpeechRecognitionResult


class SpeechRecognizer(Protocol):
    """
    Interface for speech recognition providers.
    """
    __version__ = "1.0"
    
    def recognize(self, audio_path: str, context: AIContext) -> SpeechRecognitionResult:
        """
        Recognizes speech from an audio file.
        """
        ...
        
    def health(self) -> bool:
        ...
        
    def capabilities(self) -> dict[str, Any]:
        ...
        
    def version(self) -> str:
        ...
