from typing import Protocol, Dict, Any

class SpeechRecognizer(Protocol):
    """
    Interface for speech recognition providers.
    """
    def recognize(self, audio_path: str, context: Dict[str, Any]) -> str:
        """
        Recognizes speech from an audio file.
        
        Args:
            audio_path: Path to the audio file.
            context: AI Context Layer object containing scene/timeline metadata.
            
        Returns:
            The recognized transcript.
        """
        ...
