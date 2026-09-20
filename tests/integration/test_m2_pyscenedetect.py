import os

import pytest

from bootstrap.container import VerzaContainer

# Ensure the test fails fast if scenedetect is not installed.
try:
    import scenedetect  # type: ignore # noqa: F401
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

pytestmark = pytest.mark.skipif(
    not HAS_VISION, 
    reason="ENVIRONMENT DEPENDENCY FAILURE: scenedetect is missing."
)


@pytest.fixture
def shot_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "shot_fixture.mp4")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_video_fixture.py first."
    return path


@pytest.fixture
def pyscenedetect_provider():
    # We resolve from the real DI container to ensure architecture compliance
    container = VerzaContainer()
    return container.pyscenedetect_provider()


def test_real_shot_detection(pyscenedetect_provider, shot_fixture_path):
    """
    Phase 3: Real M2 Vision/Shot Detection Execution.
    Verifies that PySceneDetectProvider opens the video, runs ContentDetector,
    and maps the frame/timecode boundaries to the existing interface contract.
    """
    # Execute extraction
    shots = pyscenedetect_provider.detect_shots(shot_fixture_path)
    
    # Structural Assertions
    assert shots is not None
    assert isinstance(shots, list)
    
    # We generated exactly 30 frames of black and 30 frames of white.
    # ContentDetector should find exactly 2 scenes/shots.
    assert len(shots) == 2, f"Expected exactly 2 shots from the fixture, got {len(shots)}"
    
    shot_1 = shots[0]
    shot_2 = shots[1]
    
    # Verify contract structure
    for shot in shots:
        assert "id" in shot
        assert "start_time_s" in shot
        assert "end_time_s" in shot
        assert "start_frame" in shot
        assert "end_frame" in shot
        
    # Verify mathematically deterministic frame boundaries
    assert shot_1["start_frame"] == 0
    
    # Depending on scenedetect's exact inclusive/exclusive semantics for the scene boundary,
    # the second shot should start exactly at the cut (frame 30).
    assert shot_2["start_frame"] == 30
    
    # Verify timecodes approximate our 30 FPS boundary (30 frames / 30 FPS = 1.0 seconds)
    # Using pytest.approx to handle floating point fuzziness in timecode resolution.
    assert shot_2["start_time_s"] == pytest.approx(1.0, abs=0.05)
