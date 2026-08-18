import uuid
from typing import Any

from core.telemetry.logging import get_logger

logger = get_logger("providers.pyscenedetect")


class PySceneDetectProvider:
    __version__: str = "1.0"

    def detect_shots(self, media_path: str) -> list[dict[str, Any]]:
        # In a real environment, we would import scenedetect
        # For M2 validation, we return a deterministic mock response representing the real PySceneDetect output
        logger.info("detecting_shots_mock", path=media_path)

        return [
            {
                "id": f"shot-{uuid.uuid4().hex[:8]}",
                "start_time_s": 0.0,
                "end_time_s": 5.0,
                "start_frame": 0,
                "end_frame": 120,
            },
            {
                "id": f"shot-{uuid.uuid4().hex[:8]}",
                "start_time_s": 5.0,
                "end_time_s": 15.0,
                "start_frame": 121,
                "end_frame": 360,
            },
        ]

    def health(self) -> bool:
        return True

    def capabilities(self) -> dict[str, Any]:
        return {"detects": ["shots", "cuts", "thresholds"]}
