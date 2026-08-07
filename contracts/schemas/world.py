from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid

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
    frames: List[int] = Field(default_factory=list)
    shots: List[str] = Field(default_factory=list)

# ---------------------------------------------------------
# Media Context
# ---------------------------------------------------------
class MediaContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    resolution: Optional[str] = None
    framerate: Optional[float] = None
    duration_s: Optional[float] = None
    codecs: Dict[str, str] = Field(default_factory=dict)
    provenance: Optional[Provenance] = None

# ---------------------------------------------------------
# Visual Context
# ---------------------------------------------------------
class Character(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: f"character-{uuid.uuid4().hex[:8]}")
    face_id: Optional[str] = None
    voice_id: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    appearances: List[str] = Field(default_factory=list) # Frame IDs or Shot IDs
    emotion_history: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Optional[Provenance] = None

class Activity(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: str # e.g., "Walking", "Talking"
    participants: List[str] = Field(default_factory=list) # Entity IDs
    objects: List[str] = Field(default_factory=list) # Entity IDs
    location: Optional[str] = None
    evidence: Optional[Evidence] = None

class Camera(BaseModel):
    model_config = ConfigDict(frozen=True)
    shot_type: Optional[str] = None # Wide, Close-up, etc.
    movement: Optional[str] = None # Pan, Tilt, etc.
    angle: Optional[str] = None # High, Low
    lens: Optional[str] = None # Wide, Normal, Telephoto

class Motion(BaseModel):
    model_config = ConfigDict(frozen=True)
    camera_motion: Optional[str] = None
    object_motion: Dict[str, str] = Field(default_factory=dict)
    character_motion: Dict[str, str] = Field(default_factory=dict)

class DocumentUnderstanding(BaseModel):
    model_config = ConfigDict(frozen=True)
    detected_text: str
    language: str
    location: List[int] = Field(default_factory=list) # Bounding box
    certainty: Optional[Certainty] = None

class VisualContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    sequences: List[Dict[str, Any]] = Field(default_factory=list)
    scenes: List[Dict[str, Any]] = Field(default_factory=list)
    shots: List[Dict[str, Any]] = Field(default_factory=list)
    frames: List[Dict[str, Any]] = Field(default_factory=list)
    characters: List[Character] = Field(default_factory=list)
    faces: List[Dict[str, Any]] = Field(default_factory=list)
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    motion: Optional[Motion] = None
    camera: Optional[Camera] = None
    documents: List[DocumentUnderstanding] = Field(default_factory=list)

# ---------------------------------------------------------
# Audio Context
# ---------------------------------------------------------
class AudioClip(BaseModel):
    model_config = ConfigDict(frozen=True)
    start_s: float
    end_s: float
    content: Optional[str] = None

class AudioSegment(BaseModel):
    model_config = ConfigDict(frozen=True)
    clips: List[AudioClip] = Field(default_factory=list)

class AudioTrack(BaseModel):
    model_config = ConfigDict(frozen=True)
    segments: List[AudioSegment] = Field(default_factory=list)

class AudioContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    speech_tracks: List[AudioTrack] = Field(default_factory=list)
    music_tracks: List[AudioTrack] = Field(default_factory=list)
    effects: List[AudioTrack] = Field(default_factory=list)
    ambience: List[AudioTrack] = Field(default_factory=list)
    silence: List[AudioTrack] = Field(default_factory=list)

# ---------------------------------------------------------
# Semantic & Others
# ---------------------------------------------------------
class SemanticContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_graph: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    intentions: List[Dict[str, Any]] = Field(default_factory=list)
    scene_moods: Dict[str, str] = Field(default_factory=dict)

class TemporalContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

class SpatialContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    environment: Optional[str] = None

class QualityContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    confidence_visual: float = 0.0
    confidence_audio: float = 0.0
    confidence_ocr: float = 0.0
    confidence_scene: float = 0.0
    confidence_overall: float = 0.0
    missing_data: List[str] = Field(default_factory=list)

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
            quality=self.quality
        )

    def with_visual(self, visual: VisualContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=visual,
            audio=self.audio,
            semantic=self.semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality
        )
        
    def with_audio(self, audio: AudioContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=self.visual,
            audio=audio,
            semantic=self.semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality
        )

    def with_semantic(self, semantic: SemanticContext) -> "WorldState":
        return WorldState(
            media=self.media,
            visual=self.visual,
            audio=self.audio,
            semantic=semantic,
            temporal=self.temporal,
            spatial=self.spatial,
            quality=self.quality
        )
