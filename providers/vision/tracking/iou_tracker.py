from collections import defaultdict

from contracts.schemas.world import DetectedObject, TrackedAppearance, TrackedObject
from core.telemetry.logging import get_logger
from interfaces.vision.object_tracker import ObjectTrackingProvider

logger = get_logger("providers.vision.tracking.iou")


def compute_iou(boxA: list[float], boxB: list[float]) -> float:
    # box format: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    if interArea == 0.0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


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
            # Sort by class_name, then confidence (descending), then x1, y1
            current_detections.sort(key=lambda d: (d.class_name, -d.confidence, d.bounding_box[0], d.bounding_box[1]))
            
            unmatched_detections = list(current_detections)
            next_active_tracks = []
            
            # 3. For each active track, find the highest-IoU eligible detection
            for track in active_tracks:
                best_match_idx = -1
                best_iou = -1.0
                
                last_appearance = track.trajectory[-1]
                
                for i, det in enumerate(unmatched_detections):
                    # Class-aware matching: person -> person, bus -> bus
                    if det.class_name != track.class_name:
                        continue
                        
                    iou = compute_iou(last_appearance.bounding_box, det.bounding_box)
                    if iou >= self.iou_threshold and iou > best_iou:
                        best_iou = iou
                        best_match_idx = i
                
                if best_match_idx != -1:
                    # Accept match
                    matched_det = unmatched_detections.pop(best_match_idx)
                    appearance = TrackedAppearance(
                        frame=matched_det.frame,
                        timestamp_s=matched_det.timestamp_s,
                        bounding_box=matched_det.bounding_box
                    )
                    # We are treating the track as mutable during creation, 
                    # but Pydantic BaseModel with frozen=True prevents direct list append 
                    # if we mutate the object. Wait, Pydantic 2 frozen=True prevents assignment, 
                    # but lists are inherently mutable. We can append to trajectory.
                    # Or we can recreate the object. 
                    # To be perfectly safe with frozen=True, we recreate the object.
                    updated_track = TrackedObject(
                        track_id=track.track_id,
                        class_name=track.class_name,
                        trajectory=track.trajectory + [appearance]
                    )
                    next_active_tracks.append(updated_track)
                else:
                    # Unmatched track terminates immediately in this simple lifecycle
                    all_tracks.append(track)
                    
            # 4. Unmatched detections -> new tracks
            for det in unmatched_detections:
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
