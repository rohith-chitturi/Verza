from typing import Dict, Any

# Assuming interfaces are importable (for M0 execution script we'll manage paths)
from interfaces.speech.recognizer import SpeechRecognizer
from core.job.snapshot import SnapshotManager

class SpeechRecognitionCapability:
    """
    Capability layer for Speech Recognition.
    Abstracts the provider and handles cross-cutting concerns (snapshots, context).
    """
    def __init__(self, provider: SpeechRecognizer):
        self._provider = provider

    def execute(self, audio_path: str, context: Dict[str, Any]) -> str:
        print("[SpeechRecognitionCapability] Executing capability...")
        
        # Invoke Provider
        result = self._provider.recognize(audio_path, context)
        
        # Store snapshot for reproducibility
        SnapshotManager.store_snapshot(
            stage_name="SpeechRecognition",
            input_data={"audio_path": audio_path},
            output_data={"transcript": result},
            context=context
        )
        
        return result
