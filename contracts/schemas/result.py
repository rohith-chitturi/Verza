from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExecutionResult(BaseModel):
    success: bool
    duration_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provider: str
    model: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class SpeechRecognitionResult(ExecutionResult):
    transcript: str
    confidence: float
    words: list[dict[str, Any]] = Field(default_factory=list)
    
class TranslationResult(ExecutionResult):
    translated_text: str
    source_language: str
    target_language: str

class TTSResult(ExecutionResult):
    audio_uri: str
    
class EvaluationResult(ExecutionResult):
    score: float
    metrics: Dict[str, float]
    passed: bool
