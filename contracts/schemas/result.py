from typing import Any

from pydantic import BaseModel, Field

from contracts.schemas.memory import MemoryProvenance


class ExecutionResult(BaseModel):
    success: bool
    duration_ms: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    provider: str
    model: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


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
    metrics: dict[str, float]
    passed: bool


class SynthesisResult(ExecutionResult):
    narrative: str
    key_events: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    memory_citations: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    provenance: MemoryProvenance | None = None

