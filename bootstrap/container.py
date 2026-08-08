from dependency_injector import containers, providers
from storage.catalog.repository import LocalSnapshotRepository

from capabilities.media_understanding.audio import AudioSegmentationCapability
from capabilities.media_understanding.document import DocumentUnderstandingCapability
from capabilities.media_understanding.metadata import MetadataExtractionCapability
from capabilities.media_understanding.shot_detector import ShotDetectionCapability
from capabilities.speech_recognition import SpeechRecognitionCapability
from core.event_bus.bus import InMemoryEventBus
from providers.media.ffmpeg.audio_provider import AudioSegmentationProvider
from providers.media.ffmpeg.metadata_provider import FFmpegMetadataProvider
from providers.speech.whisper.provider import WhisperRecognizer
from providers.vision.easyocr.provider import EasyOCRProvider
from providers.vision.pyscenedetect.provider import PySceneDetectProvider


# Fake providers for M1
class FakeSceneAnalyzer:
    def analyze(self, *args, **kwargs): return "Scene analyzed"
class FakeTranslator:
    def translate(self, *args, **kwargs): return "Translated text"
class FakeTTS:
    def synthesize(self, *args, **kwargs): return "Audio generated"

# Fake capabilities for M1
class FakeCapability:
    def __init__(self, name, provider, event_bus, snapshot_repo):
        self.name = name
    def execute(self, *args, **kwargs):
        from contracts.schemas.result import ExecutionResult
        return ExecutionResult(
            success=True,
            duration_ms=50,
            provider="fake_provider",
            model="fake_model",
            metadata={"result": f"{self.name} Result"}
        )

class VerzaContainer(containers.DeclarativeContainer):
    """
    IoC container of Verza core services and providers.
    """
    
    # Core Infrastructure
    event_bus = providers.Singleton(InMemoryEventBus)
    snapshot_repository = providers.Singleton(LocalSnapshotRepository)
    
    # Providers (M1)
    speech_recognizer_provider = providers.Singleton(WhisperRecognizer)
    scene_analyzer_provider = providers.Singleton(FakeSceneAnalyzer)
    translator_provider = providers.Singleton(FakeTranslator)
    tts_provider = providers.Singleton(FakeTTS)
    
    # Providers (M2)
    ffmpeg_metadata_provider = providers.Singleton(FFmpegMetadataProvider)
    pyscenedetect_provider = providers.Singleton(PySceneDetectProvider)
    easyocr_provider = providers.Singleton(EasyOCRProvider)
    ffmpeg_audio_provider = providers.Singleton(AudioSegmentationProvider)
    
    # Capabilities (M1)
    speech_recognition_capability = providers.Factory(
        SpeechRecognitionCapability,
        provider=speech_recognizer_provider,
        event_bus=event_bus,
        snapshot_repo=snapshot_repository
    )
    
    scene_analysis_capability = providers.Factory(
        FakeCapability, name="SceneAnalysis", provider=scene_analyzer_provider, event_bus=event_bus, snapshot_repo=snapshot_repository
    )
    
    translation_capability = providers.Factory(
        FakeCapability, name="Translation", provider=translator_provider, event_bus=event_bus, snapshot_repo=snapshot_repository
    )
    
    tts_capability = providers.Factory(
        FakeCapability, name="TTS", provider=tts_provider, event_bus=event_bus, snapshot_repo=snapshot_repository
    )
    
    # Capabilities (M2)
    metadata_cap = providers.Factory(
        MetadataExtractionCapability,
        provider=ffmpeg_metadata_provider
    )
    
    shot_cap = providers.Factory(
        ShotDetectionCapability,
        provider=pyscenedetect_provider
    )
    
    doc_cap = providers.Factory(
        DocumentUnderstandingCapability,
        provider=easyocr_provider
    )
    
    audio_cap = providers.Factory(
        AudioSegmentationCapability,
        provider=ffmpeg_audio_provider
    )

    # Core State & Prompts (M3.1)
    from core.prompts.registry import PromptRegistry
    from core.state.journal import DeltaJournal
    from core.state.merger import DeltaMerger
    from core.state.validator import DeltaValidator
    
    delta_validator = providers.Singleton(DeltaValidator)
    delta_merger = providers.Singleton(DeltaMerger)
    delta_journal = providers.Singleton(DeltaJournal)
    prompt_registry = providers.Singleton(PromptRegistry)
    
    # Cognitive Providers (M3.1)
    from interfaces.cognitive.mock_vlm import MockVLMProvider
    mock_vlm_provider = providers.Singleton(MockVLMProvider)
    
    # Interpreters (M3.1)
    from capabilities.cognitive.activity_interpreter import ActivityInterpreter
    from capabilities.cognitive.character_interpreter import CharacterInterpreter
    from capabilities.cognitive.scene_interpreter import SceneInterpreter
    
    scene_interpreter = providers.Factory(SceneInterpreter)
    character_interpreter = providers.Factory(CharacterInterpreter)
    activity_interpreter = providers.Factory(ActivityInterpreter)
