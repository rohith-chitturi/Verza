from collections import defaultdict

from contracts.schemas.world import DetectedObject, TrackedAppearance, TrackedObject
from core.telemetry.logging import get_logger
from interfaces.vision.object_tracker import ObjectTrackingProvider
from providers.vision.tracking.iou_matcher import match_detections_to_tracks

logger = get_logger("providers.vision.tracking.iou")


class IoUObjectTracker(ObjectTrackingProvider):
    """
    Real tracking provider implementing zero-dependency greedy IoU (Intersection over Union).
    """

    __version__: str = "1.0"

    def __init__(self, iou_threshold: float = 0.30):
        self.iou_threshold = iou_threshold

    def track_objects(self, detections: list[DetectedObject]) -> list[TrackedObject]:
        logger.info("iou_tracking_started", detection_count=len(detections))
        
        # 1. Group detections by frame
        frames_dict: dict[int, list[DetectedObject]] = defaultdict(list)
        for d in detections:
            frames_dict[d.frame].append(d)
            
        all_tracks: list[TrackedObject] = []
        active_tracks: list[TrackedObject] = []
        next_track_id = 1
        
        # 2. Iterate through frames deterministically
        for frame_idx in sorted(frames_dict.keys()):
            current_detections = frames_dict[frame_idx]
            
            # Sort detections deterministically to prevent subtle non-determinism during ties
            # Sort detections deterministically (by class_name, then confidence (descending), then x1, y1)
            current_detections.sort(key=lambda d: (d.class_name, -d.confidence, d.bounding_box[0], d.bounding_box[1]))
            
            next_active_tracks = []
            
            # 3. For each active track, find the highest-IoU eligible detection
            matches, unmatched_det_indices = match_detections_to_tracks(
                active_tracks=active_tracks,
                unmatched_detections=current_detections,
                get_track_last_bbox=lambda t: t.trajectory[-1].bounding_box,
                get_det_bbox=lambda d: d.bounding_box,
                is_eligible_match=lambda t, d: t.class_name == d.class_name,
                iou_threshold=self.iou_threshold,
            )

            # Process matches
            matched_track_indices = set()
            for track_idx, det_idx in matches:
                matched_track_indices.add(track_idx)
                track = active_tracks[track_idx]
                matched_det = current_detections[det_idx]
                
                appearance = TrackedAppearance(
                    frame=matched_det.frame,
                    timestamp_s=matched_det.timestamp_s,
                    bounding_box=matched_det.bounding_box
                )
                updated_track = TrackedObject(
                    track_id=track.track_id,
                    class_name=track.class_name,
                    trajectory=track.trajectory + [appearance]
                )
                next_active_tracks.append(updated_track)

            # Process unmatched tracks (they terminate immediately in this simple lifecycle)
            for i, track in enumerate(active_tracks):
                if i not in matched_track_indices:
                    all_tracks.append(track)
                    
            # 4. Unmatched detections -> new tracks
            for idx in unmatched_det_indices:
                det = current_detections[idx]
                appearance = TrackedAppearance(
                    frame=det.frame,
                    timestamp_s=det.timestamp_s,
                    bounding_box=det.bounding_box
                )
                new_track = TrackedObject(
                    track_id=f"track-{next_track_id}",
                    class_name=det.class_name,
                    trajectory=[appearance]
                )
                next_track_id += 1
                next_active_tracks.append(new_track)
                
            active_tracks = next_active_tracks
            
        # Add remaining active tracks to all_tracks
        all_tracks.extend(active_tracks)
        
        # Sort output deterministically
        all_tracks.sort(key=lambda t: (t.trajectory[0].frame, t.track_id))
        
        logger.info("iou_tracking_completed", tracked_objects_count=len(all_tracks))
        return all_tracks
