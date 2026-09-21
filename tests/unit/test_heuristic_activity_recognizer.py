import pytest

from contracts.schemas.world import (
    AudioClip,
    AudioContext,
    AudioSegment,
    AudioTrack,
    TrackedAppearance,
    TrackedFace,
    TrackedFaceAppearance,
    TrackedObject,
    VisualContext,
)
from providers.cognitive.heuristic_activity_recognizer import HeuristicActivityRecognizer


def test_moving_activity():
    recognizer = HeuristicActivityRecognizer(motion_threshold=0.05)
    
    # Simulating a TrackedObject moving significantly
    obj = TrackedObject(
        track_id="obj-1",
        class_name="person",
        trajectory=[
            TrackedAppearance(frame=0, timestamp_s=0.0, bounding_box=[10.0, 10.0, 100.0, 100.0]),
            TrackedAppearance(frame=1, timestamp_s=0.1, bounding_box=[10.0, 10.0, 100.0, 100.0]),  # Still
            TrackedAppearance(frame=2, timestamp_s=0.2, bounding_box=[25.0, 25.0, 100.0, 100.0]),  # Moved slightly (sqrt(15^2+15^2)=21.2)
            TrackedAppearance(frame=3, timestamp_s=0.3, bounding_box=[40.0, 40.0, 100.0, 100.0]),  # Moved more
            TrackedAppearance(frame=4, timestamp_s=0.4, bounding_box=[40.0, 40.0, 100.0, 100.0]),  # Still again
        ]
    )
    # Diagonal of 100x100 is 141.4. Displacement 15 is 15/141.4 = 0.106 > 0.05. So it moves.
    
    visual_context = VisualContext(tracked_objects=[obj])
    audio_context = AudioContext()
    
    activities = recognizer.recognize_activities(visual_context, audio_context)
    
    # Expected: 1 Moving activity from 0.1s to 0.4s (or end of move)
    assert len(activities) == 1
    assert activities[0].type == "Moving"
    assert activities[0].participants == ["obj-1"]
    # The movement started between frame 1 and 2, so it begins at prev.timestamp = 0.1
    # It ended between frame 3 and 4, so last_time was 0.3, then interval closed
    assert activities[0].start_time_s == 0.1
    assert activities[0].end_time_s == 0.3


def test_below_threshold_no_moving_activity():
    recognizer = HeuristicActivityRecognizer(motion_threshold=0.05)
    
    obj = TrackedObject(
        track_id="obj-2",
        class_name="person",
        trajectory=[
            TrackedAppearance(frame=0, timestamp_s=0.0, bounding_box=[10.0, 10.0, 100.0, 100.0]),
            TrackedAppearance(frame=1, timestamp_s=0.1, bounding_box=[11.0, 11.0, 100.0, 100.0]),  # Below threshold
            TrackedAppearance(frame=2, timestamp_s=0.2, bounding_box=[12.0, 12.0, 100.0, 100.0]),  # Below threshold
        ]
    )
    
    activities = recognizer.recognize_activities(VisualContext(tracked_objects=[obj]), AudioContext())
    assert len(activities) == 0


def test_audio_active_on_screen():
    recognizer = HeuristicActivityRecognizer()
    
    face = TrackedFace(
        track_id="face-1",
        trajectory=[
            TrackedFaceAppearance(frame=0, timestamp_s=2.0, bounding_box=[0.0, 0.0, 10.0, 10.0]),
            TrackedFaceAppearance(frame=10, timestamp_s=4.0, bounding_box=[0.0, 0.0, 10.0, 10.0]),
        ]
    )
    
    audio = AudioContext(
        speech_tracks=[
            AudioTrack(
                segments=[
                    AudioSegment(
                        clips=[
                            AudioClip(start_s=0.0, end_s=1.5, content="ACTIVE_AUDIO"),
                            AudioClip(start_s=2.5, end_s=3.5, content="ACTIVE_AUDIO"),  # Overlaps face (2.0 to 4.0)
                            AudioClip(start_s=5.0, end_s=6.0, content="ACTIVE_AUDIO"),
                        ]
                    )
                ]
            )
        ]
    )
    
    activities = recognizer.recognize_activities(VisualContext(faces=[face]), audio)
    
    assert len(activities) == 1
    assert activities[0].type == "AudioActiveOnScreen"
    assert activities[0].participants == ["face-1"]
    assert activities[0].start_time_s == 2.5
    assert activities[0].end_time_s == 3.5


def test_no_face_no_audio_activity():
    recognizer = HeuristicActivityRecognizer()
    audio = AudioContext(
        speech_tracks=[
            AudioTrack(
                segments=[
                    AudioSegment(
                        clips=[
                            AudioClip(start_s=2.5, end_s=3.5, content="ACTIVE_AUDIO"),
                        ]
                    )
                ]
            )
        ]
    )
    # Face doesn't overlap
    face = TrackedFace(
        track_id="face-1",
        trajectory=[
            TrackedFaceAppearance(frame=0, timestamp_s=0.0, bounding_box=[0.0, 0.0, 10.0, 10.0]),
            TrackedFaceAppearance(frame=10, timestamp_s=1.0, bounding_box=[0.0, 0.0, 10.0, 10.0]),
        ]
    )
    
    activities = recognizer.recognize_activities(VisualContext(faces=[face]), audio)
    assert len(activities) == 0
