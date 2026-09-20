import os

import pytest

try:
    import ultralytics  # noqa: F401
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

from bootstrap.container import VerzaContainer

pytestmark = pytest.mark.skipif(
    not HAS_ULTRALYTICS, 
    reason="ENVIRONMENT DEPENDENCY FAILURE: ultralytics is missing."
)


@pytest.fixture
def object_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "object_fixture.mp4")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_object_fixture.py first."
    return path


@pytest.fixture
def yolo_model_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "models", "yolov8n.pt")
    assert os.path.exists(path), f"Model missing: {path}. Run generate_object_fixture.py first."
    return path


@pytest.fixture
def tracking_pipeline(yolo_model_path):
    container = VerzaContainer()
    container.config.vision.yolo_model.override(yolo_model_path)
    # Give it a safe threshold
    container.config.vision.iou_threshold.override(0.30)
    
    return {
        "yolo": container.yolo_provider(),
        "tracker": container.iou_tracker_provider()
    }


def test_real_object_tracking_pipeline(tracking_pipeline, object_fixture_path):
    """
    Phase 6: Real M2 Object Tracking Execution (E2E).
    Verifies that YOLOObjectDetector stream correctly flows into IoUObjectTracker,
    producing valid TrackedObject entities preserving temporal trajectory.
    """
    yolo = tracking_pipeline["yolo"]
    tracker = tracking_pipeline["tracker"]
    
    # 1. Execute YOLO Detection
    detections = yolo.detect_objects(object_fixture_path)
    assert len(detections) > 0, "YOLO should have detected at least one object in the fixture."
    
    # 2. Execute Tracker
    tracked_objects = tracker.track_objects(detections)
    
    # 3. Structural Tracking Assertions
    assert tracked_objects is not None
    assert isinstance(tracked_objects, list)
    assert len(tracked_objects) > 0, "Tracker should have yielded at least one tracked object."
    
    for obj in tracked_objects:
        assert obj.track_id.startswith("track-")
        assert isinstance(obj.class_name, str)
        assert isinstance(obj.trajectory, list)
        assert len(obj.trajectory) > 0, "Every track must have at least one appearance."
        
        for appearance in obj.trajectory:
            assert isinstance(appearance.frame, int)
            assert isinstance(appearance.timestamp_s, float)
            assert isinstance(appearance.bounding_box, list)
            assert len(appearance.bounding_box) == 4
    
    # 4. Temporal Fidelity Assertions
    # We expect at least one trajectory to span multiple frames because the fixture has stationary/slow-moving objects
    multi_frame_tracks = [t for t in tracked_objects if len(t.trajectory) > 1]
    assert len(multi_frame_tracks) > 0, "Expected at least one object to be tracked across multiple frames."
