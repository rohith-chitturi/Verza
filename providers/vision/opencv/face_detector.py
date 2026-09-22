import cv2

from contracts.schemas.world import FaceDetection
from core.telemetry.logging import get_logger
from interfaces.vision.face_tracker import FaceDetectionProvider

logger = get_logger("providers.vision.opencv.face_detector")


class OpenCVFaceDetector(FaceDetectionProvider):
    """
    Real face detection provider using OpenCV Haar Cascades.
    This fulfills the zero-dependency requirement for M2.
    """

    __version__: str = "1.0"

    def __init__(self):
        # Fail fast during initialization
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.cascade.empty():
            raise RuntimeError(
                f"ENVIRONMENT DEPENDENCY FAILURE: OpenCV Haar Cascade XML failed to load from {cascade_path}."
            )

    def detect_faces(self, media_path: str) -> list[FaceDetection]:
        logger.info("opencv_face_detection_started", media_path=media_path)
        
        cap = cv2.VideoCapture(media_path)
        if not cap.isOpened():
            raise RuntimeError(f"MEDIA INPUT FAILURE: Could not open video at {media_path}")

        detections = []
        frame_idx = 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0  # Safe default if OpenCV fails to read FPS

        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            timestamp_s = frame_idx / float(fps)
            
            for (x, y, w, h) in faces:
                # bounding_box is [x1, y1, x2, y2]
                bounding_box = [float(x), float(y), float(x + w), float(y + h)]
                
                det = FaceDetection(
                    frame=frame_idx,
                    timestamp_s=timestamp_s,
                    bounding_box=bounding_box,
                    confidence=None  # Haar cascades do not provide calibrated confidence
                )
                detections.append(det)
                
            frame_idx += 1
            
        cap.release()
        
        logger.info("opencv_face_detection_completed", detections_count=len(detections))
        return detections
