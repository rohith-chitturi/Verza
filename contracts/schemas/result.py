from typing import Any, Dict
from pydantic import BaseModel

class SpeechRecognitionResult(BaseModel):
    transcript: str
    confidence: float
    words: list[dict[str, Any]] = []
    
class TranslationResult(BaseModel):
    translated_text: str
    source_language: str
    target_language: str

class TTSResult(BaseModel):
    audio_uri: str
    duration_ms: int
    
class EvaluationResult(BaseModel):
    score: float
    metrics: Dict[str, float]
    passed: bool
