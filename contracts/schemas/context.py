
from pydantic import BaseModel


class AIContext(BaseModel):
    """
    Strongly typed AI Context Layer.
    Passed to every capability to ensure cross-pipeline consistency.
    """
    tenant_id: str
    workflow_id: str
    language: str
    scene: str | None = None
    characters: list[str] = []
    glossary: dict[str, str] = {}
    emotion: str | None = None
    timeline_start_ms: int = 0
    timeline_end_ms: int | None = None
