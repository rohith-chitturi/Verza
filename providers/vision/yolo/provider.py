import os

import cv2

from typing import Any

from contracts.schemas.world import DetectedObject
from core.telemetry.logging import get_logger
from interfaces.vision.object_detector import ObjectDetectionProvider

logger = get_logger("providers.vision.yolo")


class YOLOObjectDetector(ObjectDetectionProvider):
    """
    Real Provider implementation for Object Detection using YOLO.
    """

    __version__: str = "1.0"

    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self._model = None

        # 1. Python dependency check
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "ENVIRONMENT DEPENDENCY FAILURE: ultralytics is not installed. "
                "Ensure [vision] dependencies are installed."
            )

        # 2. Model artifact provisioning check
        # We enforce that the model file exists locally to prevent arbitrary network downloads during CI.
        # This treats the ML weights as a discrete asset that must be provisioned.
        if not os.path.exists(self.model_path):
            raise RuntimeError(
                f"ENVIRONMENT / MODEL PROVISIONING FAILURE: YOLO model artifact not found at {self.model_path}. "
                "The model must be downloaded/provisioned before execution."
            )

    def _get_model(self):
        if self._model is None:
            # Lazy loading to protect DI bootstrap times
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
        return self._model

    def detect_objects(self, media_path: str, exec_context: Any = None) -> list[DetectedObject]:
        logger.info("yolo_object_detection_started", provider="yolo", media_path=media_path)
        
        # Verify media exists
        if not os.path.exists(media_path):
            raise RuntimeError(f"MEDIA INPUT FAILURE: File not found at {media_path}")

        # Extract FPS for timestamp calculation
        cap = cv2.VideoCapture(media_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        if fps <= 0:
            fps = 30.0  # Fallback

        model = self._get_model()
        
        # We use stream=True to lazily process frames, reducing memory overhead
        results = model(media_path, stream=True, verbose=False)
        
        detected_objects = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if 'cap' in locals() else 0 # actually cap is released
        # Need to reopen cap to get frame count safely
        cap = cv2.VideoCapture(media_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        for frame_idx, r in enumerate(results):
            from contracts.schemas.execution import CancelledError, PauseRequested
            if exec_context and exec_context.is_cancelled():
                raise CancelledError()
            if exec_context and exec_context.is_pause_requested():
                # Perform a checkpoint here if needed, but for YOLO we just raise
                # and assume we will replay the stage entirely.
                raise PauseRequested()
                
            if exec_context and total_frames > 0 and frame_idx % max(1, total_frames // 100) == 0:
                percent = min(100, int((frame_idx / total_frames) * 100))
                exec_context.report_progress(percent, f"Processing frame {frame_idx}/{total_frames}")

            timestamp_s = float(frame_idx) / fps
            
            # Iterate over all bounding boxes detected in this frame
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                class_name = r.names[cls_id]
                conf = float(box.conf[0].item())
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                detected_objects.append(
                    DetectedObject(
                        class_name=class_name,
                        confidence=conf,
                        bounding_box=bbox,
                        frame=frame_idx,
                        timestamp_s=timestamp_s
                    )
                )

        logger.info("yolo_object_detection_completed", extracted_count=len(detected_objects))
        return detected_objects

    def health(self) -> bool:
        try:
            import ultralytics  # noqa
            return os.path.exists(self.model_path)
        except ImportError:
            return False
