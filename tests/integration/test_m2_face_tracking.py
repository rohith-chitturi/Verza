import os

import pytest

from bootstrap.container import VerzaContainer


@pytest.fixture
def face_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "face_fixture.mp4")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_face_fixture.py first."
    return path

@pytest.fixture
def tracking_pipeline():
    container = VerzaContainer()
    container.config.vision.iou_threshold.override(0.30)
    
    # We might fail fast if Haar cascade XML is missing, but Verza Container initialization should succeed.
    return {
        "detector": container.opencv_face_detector_provider(),
        "tracker": container.iou_face_tracker_provider()
    }

def test_real_face_detection_and_tracking_pipeline(tracking_pipeline, face_fixture_path):
    """
    Phase 7: Real M2 Face Tracking Execution (E2E).
    Verifies that OpenCVFaceDetector correctly yields FaceDetection instances,
    and IoUFaceTracker natively bounds them into TrackedFace entities.
    """
    detector = tracking_pipeline["detector"]
    tracker = tracking_pipeline["tracker"]
    
    # 1. Execute Face Detection
    detections = detector.detect_faces(face_fixture_path)
    
    assert detections is not None
    assert isinstance(detections, list)
    assert len(detections) > 0, "OpenCV should have detected at least one face in the fixture."
    
    for det in detections:
        assert getattr(det, "confidence", False) is None, "Haar Cascade shouldn't hallucinate confidence scores"
    
    # 2. Execute Face Tracker
    tracked_faces = tracker.track_faces(detections)
    
    # 3. Structural Tracking Assertions
    assert tracked_faces is not None
    assert isinstance(tracked_faces, list)
    assert len(tracked_faces) > 0, "Tracker should have yielded at least one tracked face."
    
    for face in tracked_faces:
        assert face.track_id.startswith("face-")
        assert not hasattr(face, "class_name"), "Faces do not have class_name, they are inherently faces"
        assert isinstance(face.trajectory, list)
        assert len(face.trajectory) > 0, "Every track must have at least one appearance."
        
        for appearance in face.trajectory:
            assert isinstance(appearance.frame, int)
            assert isinstance(appearance.timestamp_s, float)
            assert isinstance(appearance.bounding_box, list)
            assert len(appearance.bounding_box) == 4

    # 4. Temporal Fidelity Assertions
    # We expect at least one face trajectory to span multiple frames since the fixture pans across a face
    multi_frame_tracks = [t for t in tracked_faces if len(t.trajectory) > 1]
    assert len(multi_frame_tracks) > 0, "Expected at least one face to be tracked across multiple frames."
