from dependency_injector import containers, providers

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
from storage.catalog.repository import LocalSnapshotRepository


# Fake providers for M1
class FakeSceneAnalyzer:
    provider_type = "mock"

    def get_metadata(self):
        return {"name": "fake-scene", "type": "mock", "version": "1.0"}

    def analyze(self, *args, **kwargs):
        return "Scene analyzed"


class FakeTranslator:
    provider_type = "mock"

    def get_metadata(self):
        return {"name": "fake-translator", "type": "mock", "version": "1.0"}

    def translate(self, *args, **kwargs):
        return "Translated text"


class FakeTTS:
    provider_type = "mock"

    def get_metadata(self):
        return {"name": "fake-tts", "type": "mock", "version": "1.0"}

    def synthesize(self, *args, **kwargs):
        return "Audio generated"


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
            metadata={"result": f"{self.name} Result"},
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
        snapshot_repo=snapshot_repository,
    )

    scene_analysis_capability = providers.Factory(
        FakeCapability,
        name="SceneAnalysis",
        provider=scene_analyzer_provider,
        event_bus=event_bus,
        snapshot_repo=snapshot_repository,
    )

    translation_capability = providers.Factory(
        FakeCapability,
        name="Translation",
        provider=translator_provider,
        event_bus=event_bus,
        snapshot_repo=snapshot_repository,
    )

    tts_capability = providers.Factory(
        FakeCapability,
        name="TTS",
        provider=tts_provider,
        event_bus=event_bus,
        snapshot_repo=snapshot_repository,
    )

    # Capabilities (M2)
    metadata_cap = providers.Factory(
        MetadataExtractionCapability, provider=ffmpeg_metadata_provider
    )

    shot_cap = providers.Factory(
        ShotDetectionCapability, provider=pyscenedetect_provider
    )

    doc_cap = providers.Factory(
        DocumentUnderstandingCapability, provider=easyocr_provider
    )

    audio_cap = providers.Factory(
        AudioSegmentationCapability, provider=ffmpeg_audio_provider
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

    # State Consistency (M3.2)
    from core.state.consistency import ConsistencyChecker

    consistency_checker = providers.Singleton(ConsistencyChecker)

    # Inference Providers (M3.2)
    from providers.inference.mock_inference import MockInferenceProvider

    mock_inference_provider = providers.Singleton(MockInferenceProvider)

    # Reasoners (M3.2)
    from capabilities.cognitive.event_reasoner import EventReasoner
    from capabilities.cognitive.intent_reasoner import IntentReasoner
    from capabilities.cognitive.relationship_reasoner import RelationshipReasoner

    intent_reasoner = providers.Factory(IntentReasoner)
    relationship_reasoner = providers.Factory(RelationshipReasoner)
    event_reasoner = providers.Factory(EventReasoner)

    # Reasoning Engine (M3.2)
    from core.workflow.reasoning import ReasoningEngine

    reasoning_engine = providers.Factory(
        ReasoningEngine,
        inference_provider=mock_inference_provider,
        intent_reasoner=intent_reasoner,
        relationship_reasoner=relationship_reasoner,
        event_reasoner=event_reasoner,
        validator=delta_validator,
        consistency_checker=consistency_checker,
        merger=delta_merger,
        journal=delta_journal,
        prompt_registry=prompt_registry,
    )
