import time
from storage.catalog.repository import SnapshotRepository

from contracts.events.base import StageFinished
from contracts.schemas.context import AIContext
from contracts.schemas.result import SpeechRecognitionResult
from contracts.schemas.snapshot import Snapshot
from core.event_bus.bus import EventBus
from core.telemetry.logging import get_logger
from interfaces.speech.recognizer import SpeechRecognizer

logger = get_logger("capabilities.speech_recognition")

class SpeechRecognitionCapability:
    def __init__(self, provider: SpeechRecognizer, event_bus: EventBus, snapshot_repo: SnapshotRepository):
        self._provider = provider
        self._event_bus = event_bus
        self._snapshot_repo = snapshot_repo

    def execute(self, audio_path: str, context: AIContext, trace_id: str) -> SpeechRecognitionResult:
        start_time = time.time()
        logger.info("stage_executing", stage="SpeechRecognition", trace_id=trace_id)
        
        result = self._provider.recognize(audio_path, context)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Save snapshot
        snapshot = Snapshot(
            workflow_id=context.workflow_id,
            job_id="job-001",
            stage="SpeechRecognition",
            input_data={"audio_path": audio_path},
            output_data=result.model_dump(),
            context=context.model_dump(),
            provider="whisper",
            model="large-v3",
            version="1.0"
        )
        self._snapshot_repo.save(snapshot)
        
        # Publish typed event
        self._event_bus.publish(StageFinished(
            workflow_id=context.workflow_id,
            trace_id=trace_id,
            correlation_id="corr-001",
            stage_name="SpeechRecognition",
            duration_ms=duration_ms,
            success=True
        ))
        
        return result
