from dependency_injector import containers, providers
from core.event_bus.bus import InMemoryEventBus
from storage.catalog.repository import LocalSnapshotRepository
from providers.speech.whisper.provider import WhisperRecognizer
from capabilities.speech_recognition import SpeechRecognitionCapability

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
        from core.telemetry.logging import get_logger
        get_logger(f"capabilities.{self.name}").info("stage_executing", stage=self.name)
        return f"{self.name} Result"

class VerzaContainer(containers.DeclarativeContainer):
    """
    IoC container of Verza core services and providers.
    """
    
    # Core Infrastructure
    event_bus = providers.Singleton(InMemoryEventBus)
    snapshot_repository = providers.Singleton(LocalSnapshotRepository)
    
    # Providers
    speech_recognizer_provider = providers.Singleton(WhisperRecognizer)
    scene_analyzer_provider = providers.Singleton(FakeSceneAnalyzer)
    translator_provider = providers.Singleton(FakeTranslator)
    tts_provider = providers.Singleton(FakeTTS)
    
    # Capabilities
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
