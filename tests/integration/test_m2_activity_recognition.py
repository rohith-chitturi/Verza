import os

import pytest

from bootstrap.container import VerzaContainer
from contracts.schemas.world import VisualContext


@pytest.fixture
def activity_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "activity_fixture.mp4")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_activity_fixture.py first."
    return path


@pytest.fixture
def yolo_model_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "models", "yolov8n.pt")
    assert os.path.exists(path), f"Model missing: {path}."
    return path


def test_real_activity_recognition_pipeline(activity_fixture_path, yolo_model_path):
    """
    Phase 8: Real M2 Activity Recognition Execution (E2E).
    Verifies that the heuristic engine successfully synthesizes signals
    from earlier M2 pipeline stages (face tracking, audio segmentation)
    into Moving and AudioActiveOnScreen activities.
    """
    container = VerzaContainer()
    
    # We lower thresholds slightly to ensure the deterministic 1-second fixture triggers them
    container.config.vision.iou_threshold.override(0.30)
    container.config.vision.activity_motion_threshold.override(0.05)
    container.config.vision.yolo_model.override(yolo_model_path)
    
    face_detector = container.opencv_face_detector_provider()
    face_tracker = container.iou_face_tracker_provider()
    
    object_detector = container.yolo_provider()
    object_tracker = container.iou_tracker_provider()
    
    audio_segmenter = container.ffmpeg_audio_provider()
    activity_recognizer = container.heuristic_activity_recognizer_provider()
    
    # 1. Run Face Pipeline
    face_detections = face_detector.detect_faces(activity_fixture_path)
    tracked_faces = face_tracker.track_faces(face_detections)
    
    # 2. Run Object Pipeline
    object_detections = object_detector.detect_objects(activity_fixture_path)
    tracked_objects = object_tracker.track_objects(object_detections)
    
    visual_context = VisualContext(
        faces=tracked_faces,
        tracked_objects=tracked_objects
    )
    
    # 3. Run Audio Pipeline (ffmpeg can extract audio directly from mp4)
    audio_context = audio_segmenter.segment_audio(activity_fixture_path)
    
    # 3. Synthesize Activities
    activities = activity_recognizer.recognize_activities(
        visual_context=visual_context,
        audio_context=audio_context
    )
    
    assert activities is not None
    assert isinstance(activities, list)
    
    # Check for AudioActiveOnScreen
    audio_active = [a for a in activities if a.type == "AudioActiveOnScreen"]
    # Check for Moving
    moving = [a for a in activities if a.type == "Moving"]
    
    assert len(audio_active) > 0, "Expected an AudioActiveOnScreen activity from sine wave overlapping a tracked face."
    assert len(moving) > 0, "Expected a Moving activity due to significant panning."
    
    # Ensure they point to participants
    for activity in audio_active:
        assert activity.participants, "Activity must have participants"
        assert activity.confidence is None, "Heuristics shouldn't hallucinate confidence"
        
    for activity in moving:
        assert activity.participants, "Moving activity must point to the tracked object/face ID"
        assert activity.confidence is None
