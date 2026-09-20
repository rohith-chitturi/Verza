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
def yolo_provider(yolo_model_path):
    # We resolve from the real DI container to ensure architecture compliance
    container = VerzaContainer()
    # Override the configured model artifact path to ensure no network calls
    container.config.vision.yolo_model.override(yolo_model_path)
    return container.yolo_provider()


def test_real_object_detection(yolo_provider, object_fixture_path):
    """
    Phase 5: Real M2 Object Detection Execution.
    Verifies that YOLOObjectDetector processes the physical video, yields frame-level detections,
    and maps them strictly to the ObjectDetection contract (DetectedObject).
    """
    # Execute extraction
    objects = yolo_provider.detect_objects(object_fixture_path)
    
    # Structural Assertions
    assert objects is not None
    assert isinstance(objects, list)
    assert len(objects) > 0, "YOLO should have detected at least one object in the fixture."
    
    # Verify semantic contract of the first detected object
    first_obj = objects[0]
    
    # Ensure it implements the DetectedObject schema structure
    assert hasattr(first_obj, "class_name")
    assert hasattr(first_obj, "confidence")
    assert hasattr(first_obj, "bounding_box")
    assert hasattr(first_obj, "frame")
    assert hasattr(first_obj, "timestamp_s")
    
    assert isinstance(first_obj.class_name, str)
    assert isinstance(first_obj.confidence, float)
    assert isinstance(first_obj.bounding_box, list)
    assert len(first_obj.bounding_box) == 4, "Bounding box must be [x1, y1, x2, y2]"
    assert isinstance(first_obj.frame, int)
    assert isinstance(first_obj.timestamp_s, float)
    
    # Verify semantic accuracy (the fixture is the ultralytics 'bus.jpg' stretched to a video)
    # So we expect to find a 'bus' and 'person' somewhere in the detections.
    detected_classes = {obj.class_name for obj in objects}
    assert "bus" in detected_classes or "person" in detected_classes, \
        "Expected the real YOLO model to detect the bus or person in the known physical fixture."
    
    # Verify temporal mapping: ensure not everything collapsed to a single frame
    frames = {obj.frame for obj in objects}
    assert len(frames) > 1, "Expected detections to be mapped across multiple frames temporally."
    
    # Ensure timestamps are logically ordered or present
    assert all(obj.timestamp_s >= 0.0 for obj in objects)
