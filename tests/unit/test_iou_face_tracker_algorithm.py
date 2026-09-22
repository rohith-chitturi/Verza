from contracts.schemas.world import FaceDetection
from providers.vision.tracking.iou_face_tracker import IoUFaceTracker


def test_iou_face_tracker_algorithmic_identity():
    tracker = IoUFaceTracker(iou_threshold=0.30)
    
    # Simulate a face moving slightly across 3 frames
    detections = [
        FaceDetection(frame=0, timestamp_s=0.0, bounding_box=[10, 10, 50, 70], confidence=None),
        FaceDetection(frame=1, timestamp_s=0.1, bounding_box=[12, 10, 52, 70], confidence=None),
        FaceDetection(frame=2, timestamp_s=0.2, bounding_box=[14, 10, 54, 70], confidence=None),
    ]
    
    tracks = tracker.track_faces(detections)
    
    # We expect 1 track representing the same face across 3 frames
    assert len(tracks) == 1
    track = tracks[0]
    assert track.track_id == "face-1"
    assert len(track.trajectory) == 3
    assert track.trajectory[0].frame == 0
    assert track.trajectory[1].frame == 1
    assert track.trajectory[2].frame == 2


def test_iou_face_tracker_low_iou_creates_new_track():
    tracker = IoUFaceTracker(iou_threshold=0.30)
    
    # Two face detections across two frames, but totally non-overlapping
    detections = [
        FaceDetection(frame=0, timestamp_s=0.0, bounding_box=[10, 10, 50, 70], confidence=None),
        FaceDetection(frame=1, timestamp_s=0.1, bounding_box=[200, 200, 250, 270], confidence=None),
    ]
    
    tracks = tracker.track_faces(detections)
    
    # We expect 2 separate tracks because IoU < 0.30
    assert len(tracks) == 2
    assert tracks[0].track_id == "face-1"
    assert tracks[1].track_id == "face-2"


def test_iou_face_tracker_multiple_faces_independent_tracks():
    tracker = IoUFaceTracker(iou_threshold=0.30)
    
    # Two people moving independently
    detections = [
        # Frame 0
        FaceDetection(frame=0, timestamp_s=0.0, bounding_box=[10, 10, 50, 70], confidence=None),
        FaceDetection(frame=0, timestamp_s=0.0, bounding_box=[200, 200, 250, 270], confidence=None),
        
        # Frame 1
        FaceDetection(frame=1, timestamp_s=0.1, bounding_box=[12, 10, 52, 70], confidence=None),
        FaceDetection(frame=1, timestamp_s=0.1, bounding_box=[202, 200, 252, 270], confidence=None),
    ]
    
    tracks = tracker.track_faces(detections)
    
    # Expect 2 tracks, each length 2
    assert len(tracks) == 2
    assert len(tracks[0].trajectory) == 2
    assert len(tracks[1].trajectory) == 2
    
    # Ensure they were grouped correctly
    assert tracks[0].trajectory[0].bounding_box == [10.0, 10.0, 50.0, 70.0]
    assert tracks[0].trajectory[1].bounding_box == [12.0, 10.0, 52.0, 70.0]
    
    assert tracks[1].trajectory[0].bounding_box == [200.0, 200.0, 250.0, 270.0]
    assert tracks[1].trajectory[1].bounding_box == [202.0, 200.0, 252.0, 270.0]
