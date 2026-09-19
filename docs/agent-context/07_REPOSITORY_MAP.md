# REPOSITORY MAP

- `alembic/`: Database schema migrations (Alembic). Modifying the DB schema requires a new revision here.
- `bootstrap/`: Dependency Injection (`container.py`) and Application initialization.
- `capabilities/`: Interface implementations of cognitive or media tasks that compose workflows (e.g., `SceneInterpreter`, `SpeechRecognitionCapability`). Must not hardcode vendor APIs.
- `contracts/`: Pydantic domain schemas. `workflow.py`, `runtime.py`, `result.py`. Represents the API boundaries.
- `core/`: The heart of Verza. Contains `workflow/` (M4 runtime engine), `state/` (WorldState delta/validation/merging), `event_bus/`, and `registry/`.
- `interfaces/`: Abstract base classes for Providers (e.g. `VLMProvider`, `SpeechRecognizer`).
- `providers/`: Concrete integrations for third-party libraries/APIs (`whisper`, `pyscenedetect`, `easyocr`).
- `storage/`: Database models (`models/runtime.py`) and repositories (`sql_repository.py`) abstracting SQLAlchemy.
- `tests/`: Integration and Unit tests. Uses `pytest`. Note: Currently heavily relies on mocks and SQLite.
