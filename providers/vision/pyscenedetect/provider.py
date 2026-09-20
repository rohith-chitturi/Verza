import uuid
from typing import Any

from core.telemetry.logging import get_logger

logger = get_logger("providers.pyscenedetect")


class PySceneDetectProvider:
    """
    Real Provider implementation for Vision/Shot Detection using PySceneDetect.
    """

    __version__: str = "1.0"

    def __init__(self):
        # Enforce fail-fast dependency check per M2 Real Media Understanding architecture
        try:
            import scenedetect  # type: ignore # noqa: F401
        except ImportError:
            raise RuntimeError(
                "ENVIRONMENT DEPENDENCY FAILURE: scenedetect is not installed. "
                "Please install it via the [vision] optional dependency."
            )

    def detect_shots(self, media_path: str) -> list[dict[str, Any]]:
        logger.info("shot_detection_started", provider="pyscenedetect", media_path=media_path)
        
        from scenedetect import SceneManager, open_video  # type: ignore
        from scenedetect.detectors import ContentDetector  # type: ignore
        
        try:
            video = open_video(media_path)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"ENVIRONMENT / MEDIA INPUT FAILURE: Failed to open media at {media_path}. "
                f"Details: {e}"
            )
            
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        
        # Perform scene detection
        scene_manager.detect_scenes(video)
        
        # A scene list is a list of tuples: (start_timecode, end_timecode)
        scene_list = scene_manager.get_scene_list()
        
        shots = []
        for start_timecode, end_timecode in scene_list:
            shots.append({
                "id": f"shot-{uuid.uuid4().hex[:8]}",
                "start_time_s": start_timecode.seconds,
                "end_time_s": end_timecode.seconds,
                "start_frame": start_timecode.frame_num,
                "end_frame": end_timecode.frame_num,
            })
            
        return shots

    def health(self) -> bool:
        try:
            import scenedetect  # noqa: F401
            return True
        except ImportError:
            return False

    def capabilities(self) -> dict[str, Any]:
        return {"detects": ["shots", "cuts", "thresholds"], "real_execution": True}
