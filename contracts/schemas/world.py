import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    DERIVED = "DERIVED"
    USER_CONFIRMED = "USER_CONFIRMED"


# ---------------------------------------------------------
# Core Abstractions
# ---------------------------------------------------------
class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str
    version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Certainty(BaseModel):
    model_config = ConfigDict(frozen=True)
    confidence: float
    source: str


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    frames: list[int] = Field(default_factory=list)
    shots: list[str] = Field(default_factory=list)


# ---------------------------------------------------------
# Media Context
# ---------------------------------------------------------
class MediaContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    resolution: str | None = None
    framerate: float | None = None
    duration_s: float | None = None
    codecs: dict[str, str] = Field(default_factory=dict)
    provenance: Provenance | None = None


# ---------------------------------------------------------
# Visual Context
# ---------------------------------------------------------
class Character(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: f"character-{uuid.uuid4().hex[:8]}")
    face_id: str | None = None
    voice_id: str | None = None
    embeddings: list[float] = Field(default_factory=list)
    appearances: list[str] = Field(default_factory=list)  # Frame IDs or Shot IDs
    emotion_history: list[dict[str, Any]] = Field(default_factory=list)
    provenance: Provenance | None = None


class Activity(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: str  # e.g., "Walking", "Talking"
    participants: list[str] = Field(default_factory=list)  # Entity IDs
    objects: list[str] = Field(default_factory=list)  # Entity IDs
    location: str | None = None
    evidence: Evidence | None = None


class Camera(BaseModel):
    model_config = ConfigDict(frozen=True)
    shot_type: str | None = None  # Wide, Close-up, etc.
    movement: str | None = None  # Pan, Tilt, etc.
    angle: str | None = None  # High, Low
    lens: str | None = None  # Wide, Normal, Telephoto


class Motion(BaseModel):
    model_config = ConfigDict(frozen=True)
    camera_motion: str | None = None
    object_motion: dict[str, str] = Field(default_factory=dict)
    character_motion: dict[str, str] = Field(default_factory=dict)


class DocumentUnderstanding(BaseModel):
    model_config = ConfigDict(frozen=True)
    detected_text: str
    language: str
    location: list[int] = Field(default_factory=list)  # Bounding box
    certainty: Certainty | None = None


class VisualContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    sequences: list[dict[str, Any]] = Field(default_factory=list)
    scenes: list[dict[str, Any]] = Field(default_factory=list)
    shots: list[dict[str, Any]] = Field(default_factory=list)
    frames: list[dict[str, Any]] = Field(default_factory=list)
    characters: list[Character] = Field(default_factory=list)
    faces: list[dict[str, Any]] = Field(default_factory=list)
    objects: list[dict[str, Any]] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    motion: Motion | None = None
    camera: Camera | None = None
    documents: list[DocumentUnderstanding] = Field(default_factory=list)


# ---------------------------------------------------------
# Audio Context
# ---------------------------------------------------------
class AudioClip(BaseModel):
    model_config = ConfigDict(frozen=True)
    start_s: float
    end_s: float
    content: str | None = None


class AudioSegment(BaseModel):
    model_config = ConfigDict(frozen=True)
    clips: list[AudioClip] = Field(default_factory=list)


class AudioTrack(BaseModel):
    model_config = ConfigDict(frozen=True)
    segments: list[AudioSegment] = Field(default_factory=list)


class AudioContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    speech_tracks: list[AudioTrack] = Field(default_factory=list)
    music_tracks: list[AudioTrack] = Field(default_factory=list)
    effects: list[AudioTrack] = Field(default_factory=list)
    ambience: list[AudioTrack] = Field(default_factory=list)
    silence: list[AudioTrack] = Field(default_factory=list)


# ---------------------------------------------------------
# Semantic & Others
# ---------------------------------------------------------
class KnowledgeGraphNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float


class KnowledgeGraphEdge(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: f"edge-{uuid.uuid4().hex[:8]}")
    source: str
    target: str
    relation: str
    properties: dict[str, Any] = Field(default_factory=dict)
    valid_from: str | None = None
    valid_until: str | None = None
    confidence: float
    evidence: Evidence | None = None


class KnowledgeGraph(BaseModel):
    model_config = ConfigDict(frozen=True)
    nodes: list[KnowledgeGraphNode] = Field(default_factory=list)
    edges: list[KnowledgeGraphEdge] = Field(default_factory=list)


class StructuredEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: f"event-{uuid.uuid4().hex[:8]}")
    type: str
    start: str | None = None
    end: str | None = None
    participants: list[str] = Field(default_factory=list)
    causes: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    evidence: Evidence | None = None
    confidence: float
    provenance: Provenance | None = None


class TemporalIntent(BaseModel):
    model_config = ConfigDict(frozen=True)
    actor: str
    target: str | None = None
    intent: str
    start: str | None = None
    end: str | None = None
    confidence: float


class SemanticContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    relationships: list[KnowledgeGraphEdge] = Field(default_factory=list)
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    events: list[StructuredEvent] = Field(default_factory=list)
    intentions: list[TemporalIntent] = Field(default_factory=list)
    scene_moods: dict[str, str] = Field(default_factory=dict)


class TemporalContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class SpatialContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    environment: str | None = None


class QualityContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    confidence_visual: float = 0.0
    confidence_audio: float = 0.0
    confidence_ocr: float = 0.0
    confidence_scene: float = 0.0
    confidence_overall: float = 0.0
    missing_data: list[str] = Field(default_factory=list)


# ---------------------------------------------------------
# World State (Immutable)
# ---------------------------------------------------------
class WorldState(BaseModel):
    model_config = ConfigDict(frozen=True)

    media: MediaContext = Field(default_factory=MediaContext)
    visual: VisualContext = Field(default_factory=VisualContext)
    audio: AudioContext = Field(default_factory=AudioContext)
    semantic: SemanticContext = Field(default_factory=SemanticContext)
    temporal: TemporalContext = Field(default_factory=TemporalContext)
    spatial: SpatialContext = Field(default_factory=SpatialContext)
    quality: QualityContext = Field(default_factory=QualityContext)

    def with_media(self, media: MediaContext) -> "WorldState":
        return WorldState(
            media=media,
            visual=self.visual,
            audio=self.audio,
            semantic=self.semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality,
        )

    def with_visual(self, visual: VisualContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=visual,
            audio=self.audio,
            semantic=self.semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality,
        )

    def with_audio(self, audio: AudioContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=self.visual,
            audio=audio,
            semantic=self.semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality,
        )

    def with_semantic(self, semantic: SemanticContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=self.visual,
            audio=self.audio,
            semantic=semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality,
        )
