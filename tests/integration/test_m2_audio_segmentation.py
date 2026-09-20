import os
import shutil

import pytest

from bootstrap.container import VerzaContainer

HAS_FFMPEG = shutil.which("ffmpeg") is not None

pytestmark = pytest.mark.skipif(
    not HAS_FFMPEG, 
    reason="ENVIRONMENT DEPENDENCY FAILURE: ffmpeg is missing."
)


@pytest.fixture
def audio_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "audio_fixture.wav")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_audio_fixture.py first."
    return path


@pytest.fixture
def ffmpeg_audio_provider():
    # We resolve from the real DI container to ensure architecture compliance
    container = VerzaContainer()
    return container.ffmpeg_audio_provider()


def test_real_audio_segmentation(ffmpeg_audio_provider, audio_fixture_path):
    """
    Phase 4: Real M2 Audio Segmentation Execution.
    Verifies that FFmpegAudioSegmentationProvider opens the wav, runs silencedetect,
    parses stderr correctly, and maps ACTIVE_AUDIO / SILENCE into AudioContext.
    """
    # Execute extraction
    context = ffmpeg_audio_provider.segment_audio(audio_fixture_path)
    
    # Structural Assertions
    assert context is not None
    assert isinstance(context.speech_tracks, list)
    assert isinstance(context.silence, list)
    
    # We generated exactly 3.0 seconds: 1.0s active, 1.0s silence, 1.0s active.
    # We expect exactly 1 speech track with 1 segment containing 2 ACTIVE_AUDIO clips.
    # And 1 silence track with 1 segment containing 1 SILENCE clip.
    assert len(context.speech_tracks) == 1, "Expected 1 speech_track container for ACTIVE_AUDIO"
    assert len(context.silence) == 1, "Expected 1 silence track"
    
    speech_clips = context.speech_tracks[0].segments[0].clips
    silence_clips = context.silence[0].segments[0].clips
    
    assert len(speech_clips) == 2, f"Expected exactly 2 active clips, got {len(speech_clips)}"
    assert len(silence_clips) == 1, f"Expected exactly 1 silence clip, got {len(silence_clips)}"
    
    active_1 = speech_clips[0]
    silence = silence_clips[0]
    active_2 = speech_clips[1]
    
    # Verify contents
    assert active_1.content == "ACTIVE_AUDIO"
    assert silence.content == "SILENCE"
    assert active_2.content == "ACTIVE_AUDIO"
    
    # Verify Ordering
    assert active_1.start_s < active_1.end_s
    assert silence.start_s < silence.end_s
    assert active_2.start_s < active_2.end_s
    assert active_1.start_s >= 0.0
    
    # Ensure they do not overlap
    assert active_1.end_s <= silence.start_s
    assert silence.end_s <= active_2.start_s
    
    # Verify Boundary Accuracy using tolerance 
    # (FFmpeg might clip silence exactly at 0.999s instead of 1.000s)
    TOLERANCE = 0.1
    
    assert active_1.start_s == pytest.approx(0.0, abs=TOLERANCE)
    assert active_1.end_s == pytest.approx(1.0, abs=TOLERANCE)
    
    assert silence.start_s == pytest.approx(1.0, abs=TOLERANCE)
    assert silence.end_s == pytest.approx(2.0, abs=TOLERANCE)
    
    assert active_2.start_s == pytest.approx(2.0, abs=TOLERANCE)
    assert active_2.end_s == pytest.approx(3.0, abs=TOLERANCE)
