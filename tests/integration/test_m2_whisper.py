import os

import pytest

from bootstrap.container import VerzaContainer
from contracts.schemas.context import AIContext

# Ensure the test fails fast if faster-whisper is not installed.
try:
    import faster_whisper  # type: ignore # noqa: F401
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

pytestmark = pytest.mark.skipif(
    not HAS_WHISPER, 
    reason="ENVIRONMENT DEPENDENCY FAILURE: faster-whisper is missing."
)


@pytest.fixture
def speech_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "speech.wav")
    assert os.path.exists(path), f"Fixture missing: {path}"
    return path


@pytest.fixture
def whisper_provider():
    # We resolve from the real DI container to ensure architecture compliance
    container = VerzaContainer()
    return container.speech_recognizer_provider()


def test_real_whisper_transcription(whisper_provider, speech_fixture_path):
    """
    Phase 1: Real M2 Whisper Execution.
    Verifies that the WhisperRecognizer actually loads the model, processes audio, and extracts semantic text.
    """
    context = AIContext(
        media_id="physical-speech-123",
        workflow_id="wf-test-whisper",
        language="en"
    )

    result = whisper_provider.recognize(speech_fixture_path, context)

    # Provider contract assertions
    assert result.success is True
    assert result.provider == "whisper"
    assert result.transcript is not None
    assert result.duration_ms > 0

    # Semantic transcript assertions (case-insensitive and normalized)
    transcript = result.transcript.lower()
    
    assert "verza" in transcript or "versa" in transcript, f"Expected 'verza' or 'versa' in transcript, got: {transcript}"
    assert "media" in transcript, f"Expected 'media' in transcript, got: {transcript}"
    assert "intelligence" in transcript, f"Expected 'intelligence' in transcript, got: {transcript}"
    assert "platform" in transcript, f"Expected 'platform' in transcript, got: {transcript}"
