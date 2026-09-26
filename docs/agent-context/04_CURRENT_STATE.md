# 04. CURRENT STATE

## CURRENT MILESTONE:
- **Current Phase:** M2 (Media Understanding): `100% COMPLETE`. 
  - Metadata, OpenCV, PySceneDetect, Whisper, EasyOCR, FFmpeg audio segmentation.
  - YOLO object detection decoupled from pure-Python greedy IoU tracking.
  - OpenCV Haar face detection decoupled from IoU tracking.
  - **Heuristic Activity Recognition** synthesizes `Moving` and `AudioActiveOnScreen` without heavy ML.
- **M3 (Sensemaking / Context):** `FROZEN`. Complete Interpretation, Reasoning, and Memory DAG nodes.
- **M4.1 (Control Plane):** `FROZEN`. FastAPI, Typer CLI, and ExecutionDispatcher abstraction are cleanly integrated.
- **M4.2 (Lifecycle & Checkpointing):** `FROZEN`. Cooperative lifecycle control with capability-controlled checkpoint boundaries. Capabilities request/observe execution control via `ExecutionContext`, while `WorkflowRuntime` remains authoritative for all lifecycle state transitions and persistence.

## LAST VERIFIED:
27 tests passing against real PostgreSQL and real Whisper inference.

## M4 STATUS:
VERIFIED

## REAL INFRASTRUCTURE:
- PostgreSQL
- Alembic
- M4 persistence
- Rollback
- Resume
- Replay
- Real FFmpeg metadata execution
- Real Whisper speech recognition execution
- Optional dependencies `[speech]` support fail-fast isolation
- **M2 Phase 2 (EasyOCR):** Replaced mock `EasyOCRProvider` with real `easyocr` inference. 
   - Uses `opencv-python-headless` for deterministic, UI-free CI execution.
   - Bounding boxes and confidence intervals are faithfully mapped into `DocumentUnderstanding`.
- **M2 Phase 3 (Shot Detection):** Replaced mock `PySceneDetectProvider` with real `scenedetect` execution.
   - Fail-fast environment isolation preventing integration leakage.
   - Generates and verifies mathematically deterministic `.mp4` video cut points.
   - Direct translation of `scenedetect` structures into the internal shot interface contract.
- **M2 Phase 4 (Audio Segmentation):** Replaced mock `AudioSegmentationProvider` with real `ffmpeg silencedetect` execution.
   - Uses zero ML dependencies, parsing raw FFmpeg subprocess `stderr` for highly deterministic boundary mapping.
   - Generated perfect 3.0s `.wav` (sine/silence/sine) fixture using Python's `wave`.
   - Populates `ACTIVE_AUDIO` into the `speech_tracks` array in the `AudioContext` contract.
- **M2 Phase 5 (Object Detection):** Replaced mock `MockObjectDetectionCapability` with real `YOLOObjectDetector`.
   - Reused DI-configured model provisioning to ensure local `yolov8n.pt` resolves reliably without CI network fetches.
   - Extracted bounding boxes and classes mapped robustly to the `DetectedObject` schema.
   - Preserved frame-level temporal fidelity without introducing tracking logic.
- **M2 Phase 6 (Object Tracking):** Replaced missing logic with a pure-Python `IoUObjectTracker` tied to `ObjectTrackingCapability`.
   - Established `TrackedObject` and `TrackedAppearance` in the `VisualContext` of the `WorldState`.
   - Designed a class-aware, greedy bounding-box Intersection-over-Union mapping without relying on secondary ML packages (avoiding `numpy` conflicts!).
   - Strictly decoupled from media streams—processes the output array from Phase 5 dynamically in memory.

## CURRENT LIMITATION:
- Distributed workers (Celery) are deferred to M4.3. The current ExecutionDispatcher is in-process threading.

## NEXT DEVELOPMENT AREA:
M4.3 Worker Execution / Distribution or M5 (System Observability).

## DO NOT:
Redesign M2 or M3. They are frozen. Focus exclusively on M4.2 control hardening.
