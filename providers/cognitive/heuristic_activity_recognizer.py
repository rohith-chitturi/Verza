import math

from contracts.schemas.world import (
    Activity,
    AudioContext,
    Evidence,
    Provenance,
    TrackedFace,
    TrackedObject,
    VisualContext,
)
from core.telemetry.logging import get_logger

logger = get_logger("providers.cognitive.heuristic_activity_recognizer")


class HeuristicActivityRecognizer:
    """
    M2 Phase 8: Heuristic Activity Recognizer.
    
    Extracts high-level Activity concepts via rule-based synthesis of WorldState signals,
    satisfying the M2 zero-dependency philosophy.
    """

    def __init__(self, motion_threshold: float = 0.05):
        self.motion_threshold = motion_threshold

    def recognize_activities(
        self,
        visual_context: VisualContext,
        audio_context: AudioContext,
    ) -> list[Activity]:
        
        logger.info("heuristic_activity_recognition_started")
        activities: list[Activity] = []

        activities.extend(self._extract_moving_activities(visual_context.tracked_objects))
        activities.extend(self._extract_audio_active_on_screen(visual_context.faces, audio_context))

        logger.info("heuristic_activity_recognition_completed", count=len(activities))
        return activities

    def _extract_moving_activities(self, tracked_objects: list[TrackedObject]) -> list[Activity]:
        """
        Rule 1: Movement.
        Analyzes consecutive bounding box centroids. If the normalized displacement
        exceeds the configured threshold, the object is considered moving.
        Contiguous moving frames form a single Moving activity interval.
        """
        activities: list[Activity] = []

        for obj in tracked_objects:
            if len(obj.trajectory) < 2:
                continue

            is_moving = False
            start_time = 0.0
            last_time = 0.0

            for i in range(1, len(obj.trajectory)):
                prev = obj.trajectory[i - 1]
                curr = obj.trajectory[i]

                # Bounding boxes are [x, y, w, h]
                px, py, pw, ph = prev.bounding_box
                cx, cy, cw, ch = curr.bounding_box

                prev_center = (px + pw / 2.0, py + ph / 2.0)
                curr_center = (cx + cw / 2.0, cy + ch / 2.0)

                # Use the diagonal of the previous bounding box as normalization factor
                diagonal = math.hypot(pw, ph)
                if diagonal == 0:
                    continue

                displacement = math.hypot(curr_center[0] - prev_center[0], curr_center[1] - prev_center[1])
                normalized_motion = displacement / diagonal

                moved = normalized_motion >= self.motion_threshold

                if moved and not is_moving:
                    # Start of movement
                    is_moving = True
                    start_time = prev.timestamp_s
                elif not moved and is_moving:
                    # End of movement
                    is_moving = False
                    activities.append(
                        Activity(
                            type="Moving",
                            participants=[obj.track_id],
                            start_time_s=start_time,
                            end_time_s=last_time,
                            confidence=None,  # Heuristic inference
                        )
                    )
                
                if is_moving:
                    last_time = curr.timestamp_s

            # Close open interval if object was still moving at the end of its trajectory
            if is_moving:
                activities.append(
                    Activity(
                        type="Moving",
                        participants=[obj.track_id],
                        start_time_s=start_time,
                        end_time_s=last_time,
                        confidence=None,
                    )
                )

        return activities

    def _extract_audio_active_on_screen(
        self, faces: list[TrackedFace], audio_context: AudioContext
    ) -> list[Activity]:
        """
        Rule 2: AudioActiveOnScreen.
        If a tracked face is visible on screen during an ACTIVE_AUDIO segment,
        we emit an AudioActiveOnScreen activity hypothesis.
        """
        activities: list[Activity] = []
        
        active_clips = []
        for track in audio_context.speech_tracks:
            for seg in track.segments:
                for clip in seg.clips:
                    if clip.content == "ACTIVE_AUDIO":
                        active_clips.append(clip)
                        
        if not active_clips or not faces:
            return activities

        for face in faces:
            if not face.trajectory:
                continue
                
            # Determine overall lifespan of this face
            face_start = face.trajectory[0].timestamp_s
            face_end = face.trajectory[-1].timestamp_s

            for clip in active_clips:
                seg_start = clip.start_s
                seg_end = clip.end_s

                # Check for temporal overlap
                overlap_start = max(face_start, seg_start)
                overlap_end = min(face_end, seg_end)

                if overlap_start < overlap_end:
                    activities.append(
                        Activity(
                            type="AudioActiveOnScreen",
                            participants=[face.track_id],
                            start_time_s=overlap_start,
                            end_time_s=overlap_end,
                            confidence=None,
                        )
                    )

        return activities
