from collections.abc import Callable
from typing import Any, TypeVar

# T_Det is the generic detection type (e.g., DetectedObject, FaceDetection)
T_Det = TypeVar("T_Det")


def compute_iou(boxA: list[float], boxB: list[float]) -> float:
    """
    Computes Intersection over Union (IoU) between two bounding boxes.
    Boxes must be in [x1, y1, x2, y2] format.
    """
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


def match_detections_to_tracks(
    active_tracks: list[Any],
    unmatched_detections: list[T_Det],
    get_track_last_bbox: Callable[[Any], list[float]],
    get_det_bbox: Callable[[T_Det], list[float]],
    is_eligible_match: Callable[[Any, T_Det], bool],
    iou_threshold: float,
) -> tuple[list[tuple[int, int]], list[int]]:
    """
    Generic greedy IoU matcher.
    
    Args:
        active_tracks: List of current active tracks.
        unmatched_detections: List of new detections in the current frame.
        get_track_last_bbox: Extracts [x1,y1,x2,y2] from a track.
        get_det_bbox: Extracts [x1,y1,x2,y2] from a detection.
        is_eligible_match: Function determining if a track and detection can be matched (e.g., same class).
        iou_threshold: Minimum IoU to consider a match.
        
    Returns:
        matches: List of tuples (track_index, detection_index)
        unmatched_det_indices: List of indices for detections that were not matched
    """
    matches = []
    matched_det_indices = set()

    for track_idx, track in enumerate(active_tracks):
        best_match_idx = -1
        best_iou = -1.0

        track_bbox = get_track_last_bbox(track)

        for det_idx, det in enumerate(unmatched_detections):
            if det_idx in matched_det_indices:
                continue

            if not is_eligible_match(track, det):
                continue

            det_bbox = get_det_bbox(det)
            iou = compute_iou(track_bbox, det_bbox)
            
            if iou >= iou_threshold and iou > best_iou:
                best_iou = iou
                best_match_idx = det_idx

        if best_match_idx != -1:
            matches.append((track_idx, best_match_idx))
            matched_det_indices.add(best_match_idx)

    unmatched_det_indices = [i for i in range(len(unmatched_detections)) if i not in matched_det_indices]
    
    return matches, unmatched_det_indices
