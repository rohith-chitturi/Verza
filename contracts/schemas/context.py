from typing import List, Optional
from pydantic import BaseModel

class AIContext(BaseModel):
    """
    Strongly typed AI Context Layer.
    Passed to every capability to ensure cross-pipeline consistency.
    """
    tenant_id: str
    workflow_id: str
    language: str
    scene: Optional[str] = None
    characters: List[str] = []
    glossary: dict[str, str] = {}
    emotion: Optional[str] = None
    timeline_start_ms: int = 0
    timeline_end_ms: Optional[int] = None
