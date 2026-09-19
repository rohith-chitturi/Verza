# HANDOFF

**What was requested:**
Move Verza integration tests from SQLite/mocks to Real PostgreSQL and Real M2 Provider Execution while preserving mocked M3 boundaries. Construct verifiable persistence logic covering rollbacks, resume, and replay.

**What was inspected:**
- `bootstrap/container.py` (To confirm `FFmpegMetadataProvider` mapping).
- `core/workflow/runtime.py` (To establish true `AIContext` injection).
- `tests/integration/test_m4_verification.py` (To isolate unit-mocked tests).
- `providers/media/ffmpeg/metadata_provider.py` (To strip false-positive fallback data).

**What was changed:**
- **`providers/media/ffmpeg/metadata_provider.py`**: Eradicated the silent fallback mock data when `ffprobe` fails. It now correctly raises a rigorous `ENVIRONMENT DEPENDENCY FAILURE`.
- **`core/workflow/runtime.py`**: Fixed the integration gap where `WorkflowRuntime` blindly executed capabilities without parameters. It now injects an `AIContext` linked to the workflow run and a deterministic physical media ID.
- **`tests/integration/conftest.py`**: Established a PostgreSQL binding fixture (`VERZA_TEST_DATABASE_URL`) that checks connectivity before running integration logic.
- **`tests/integration/test_m4_persistence.py`**: New file. Orchestrates Rollback, Crash Resume, and Fork/Replay execution directly into the Postgres schema.
- **`tests/integration/test_m4_real_execution.py`**: New file. Injects a dynamically generated `.wav` via `generate_media.py` into a workflow consisting of real `FFmpegMetadataProvider` (M2) leading to mocked `SceneInterpreter` (M3).

**Tests run:**
- Integration suite (`pytest tests/integration/test_m4_persistence.py -v`)
- Real E2E suite (`pytest tests/integration/test_m4_real_execution.py -v`)

**Tests passed/failed:**
- Tests purposefully FAIL during startup in this exact environment because PostgreSQL and FFmpeg are absent locally (`ENVIRONMENT DEPENDENCY FAILURE`). This proves the mock barriers have been destroyed and real execution is demanded.

**Next exact task:**
- Environment setup: Install FFmpeg and ensure PostgreSQL operates locally for full green test passing.
- Wire actual VLM (M3.1) reasoning once the environment stabilizes.

**Important warnings:**
- Never run SQLite tests as integration tests again. Unit tests remain fine in memory.
