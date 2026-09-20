# 04. CURRENT STATE

## CURRENT MILESTONE:
- **Current Phase:** M2: Media Understanding (Partially Real - Whisper, EasyOCR, PySceneDetect verified)
- **Current Branch:** `feature/m2-shot-detection`
- **Active Focus:** Implementing real provider logic behind capability boundaries, using DI and physical fixtures.

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

## CURRENT LIMITATION:
- M2 remains partially implemented (FFmpeg and Whisper paths are verified, but other providers like EasyOCR are mocked or incomplete).
- M3.1 remains partially mocked.
- M3.2 remains partially mocked.

## NEXT DEVELOPMENT AREA:
M2 Real Media Understanding: Phase 2 (e.g., EasyOCR / Vision capabilities).

## DO NOT:
Start M3.3 before the agreed M2/M3 integration baseline is established.
