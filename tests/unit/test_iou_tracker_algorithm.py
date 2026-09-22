import pytest

from contracts.schemas.world import DetectedObject
from providers.vision.tracking.iou_matcher import compute_iou
from providers.vision.tracking.iou_tracker import IoUObjectTracker


def test_compute_iou():
    # Exactly overlapping
    box1 = [0.0, 0.0, 10.0, 10.0]
    box2 = [0.0, 0.0, 10.0, 10.0]
    assert compute_iou(box1, box2) == 1.0

    # No overlap
    box3 = [20.0, 20.0, 30.0, 30.0]
    assert compute_iou(box1, box3) == 0.0

    # Partial overlap (half)
    box4 = [5.0, 0.0, 15.0, 10.0]
    # Intersection = 5*10 = 50. Union = 100 + 100 - 50 = 150. IoU = 50/150 = 0.333...
    assert compute_iou(box1, box4) == pytest.approx(0.333, abs=1e-2)


def test_iou_tracker_algorithmic_identity():
    tracker = IoUObjectTracker(iou_threshold=0.30)
    
    # We simulate a person walking slightly to the right over 3 frames
    detections = [
        DetectedObject(frame=0, timestamp_s=0.0, class_name="person", confidence=0.9, bounding_box=[10, 10, 50, 100]),
        DetectedObject(frame=1, timestamp_s=0.1, class_name="person", confidence=0.9, bounding_box=[12, 10, 52, 100]),
        DetectedObject(frame=2, timestamp_s=0.2, class_name="person", confidence=0.9, bounding_box=[14, 10, 54, 100]),
    ]
    
    tracks = tracker.track_objects(detections)
    
    # We expect 1 track representing the same person across 3 frames
    assert len(tracks) == 1
    track = tracks[0]
    assert track.track_id == "track-1"
    assert track.class_name == "person"
    assert len(track.trajectory) == 3
    assert track.trajectory[0].frame == 0
    assert track.trajectory[1].frame == 1
    assert track.trajectory[2].frame == 2


def test_iou_tracker_class_aware_matching():
    tracker = IoUObjectTracker(iou_threshold=0.30)
    
    # Frame 0 has a person. Frame 1 has a bus in the exact same location!
    # They should NOT match because class is different.
    detections = [
        DetectedObject(frame=0, timestamp_s=0.0, class_name="person", confidence=0.9, bounding_box=[10, 10, 50, 100]),
        DetectedObject(frame=1, timestamp_s=0.1, class_name="bus", confidence=0.9, bounding_box=[10, 10, 50, 100]),
    ]
    
    tracks = tracker.track_objects(detections)
    
    # We expect 2 separate tracks because the class changed
    assert len(tracks) == 2
    assert tracks[0].class_name == "person"
    assert len(tracks[0].trajectory) == 1
    assert tracks[1].class_name == "bus"
    assert len(tracks[1].trajectory) == 1


def test_iou_tracker_low_iou_creates_new_track():
    tracker = IoUObjectTracker(iou_threshold=0.30)
    
    # Frame 0 and Frame 1 have a person, but they are too far apart (IoU = 0)
    detections = [
        DetectedObject(frame=0, timestamp_s=0.0, class_name="person", confidence=0.9, bounding_box=[10, 10, 50, 100]),
        DetectedObject(frame=1, timestamp_s=0.1, class_name="person", confidence=0.9, bounding_box=[200, 200, 250, 300]),
    ]
    
    tracks = tracker.track_objects(detections)
    
    # We expect 2 separate tracks because IoU < 0.30
    assert len(tracks) == 2
    assert tracks[0].track_id == "track-1"
    assert tracks[1].track_id == "track-2"


def test_iou_tracker_multiple_objects_independent_tracks():
    tracker = IoUObjectTracker(iou_threshold=0.30)
    
    # Two people moving independently
    detections = [
        # Frame 0
        DetectedObject(frame=0, timestamp_s=0.0, class_name="person", confidence=0.9, bounding_box=[10, 10, 50, 100]),
        DetectedObject(frame=0, timestamp_s=0.0, class_name="person", confidence=0.9, bounding_box=[200, 200, 250, 300]),
        
        # Frame 1 (slight movement)
        DetectedObject(frame=1, timestamp_s=0.1, class_name="person", confidence=0.9, bounding_box=[12, 10, 52, 100]),
        DetectedObject(frame=1, timestamp_s=0.1, class_name="person", confidence=0.9, bounding_box=[202, 200, 252, 300]),
    ]
    
    tracks = tracker.track_objects(detections)
    
    # Expect 2 tracks, each length 2
    assert len(tracks) == 2
    assert len(tracks[0].trajectory) == 2
    assert len(tracks[1].trajectory) == 2
    
    # Ensure they were grouped correctly
    assert tracks[0].trajectory[0].bounding_box == [10, 10, 50, 100]
    assert tracks[0].trajectory[1].bounding_box == [12, 10, 52, 100]
    
    assert tracks[1].trajectory[0].bounding_box == [200, 200, 250, 300]
    assert tracks[1].trajectory[1].bounding_box == [202, 200, 252, 300]
