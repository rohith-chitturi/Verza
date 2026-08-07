from dependency_injector.wiring import Provide, inject

from capabilities.base import BaseCapability
from capabilities.media_understanding.audio import AudioSegmentationCapability
from capabilities.media_understanding.document import DocumentUnderstandingCapability

# Import the actual capabilities
from capabilities.media_understanding.metadata import MetadataExtractionCapability
from capabilities.media_understanding.shot_detector import ShotDetectionCapability
from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger

logger = get_logger("workflow.engine")

# ---------------------------------------------------------
# Mock Capabilities for Pipeline Completeness
# ---------------------------------------------------------
class MockSceneSegmentationCapability(BaseCapability):
    @property
    def name(self) -> str: return "SceneSegmentation(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        scenes = [{"id": "scene-1", "mood": "tense"}]
        return ctx.with_world(ctx.world.with_visual(ctx.world.visual.model_copy(update={"scenes": scenes})))

class MockCharacterTrackingCapability(BaseCapability):
    @property
    def name(self) -> str: return "CharacterTracking(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        from contracts.schemas.world import Character
        chars = [Character()]
        return ctx.with_world(ctx.world.with_visual(ctx.world.visual.model_copy(update={"characters": chars})))

class MockFaceTrackingCapability(BaseCapability):
    @property
    def name(self) -> str: return "FaceTracking(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext: return context

class MockObjectDetectionCapability(BaseCapability):
    @property
    def name(self) -> str: return "ObjectDetection(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext: return context

class MockActivitiesCapability(BaseCapability):
    @property
    def name(self) -> str: return "Activities(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext: return context

class MockSemanticGraphCapability(BaseCapability):
    @property
    def name(self) -> str: return "SemanticGraph(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        kg = {"character-001": {"talking_to": "character-002"}}
        return ctx.with_world(ctx.world.with_semantic(ctx.world.semantic.model_copy(update={"knowledge_graph": kg})))

class MockWorldSynthesisCapability(BaseCapability):
    @property
    def name(self) -> str: return "WorldStateSynthesis(Mock)"
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext: return context

# ---------------------------------------------------------
# The Engine
# ---------------------------------------------------------
class MediaUnderstandingEngine:
    """
    Executes the 12-stage M2 pipeline, constructing the immutable WorldState.
    """
    def __init__(
        self,
        metadata_cap: MetadataExtractionCapability,
        shot_cap: ShotDetectionCapability,
        doc_cap: DocumentUnderstandingCapability,
        audio_cap: AudioSegmentationCapability
    ):
        self.pipeline = [
            metadata_cap,              # 1. Video Metadata
            shot_cap,                  # 2. Frames & Shots
            MockSceneSegmentationCapability(), # 3. Scenes
            MockCharacterTrackingCapability(), # 4. Characters
            MockFaceTrackingCapability(),      # 5. Faces
            MockObjectDetectionCapability(),   # 6. Objects
            doc_cap,                   # 7. Document Understanding (OCR)
            MockActivitiesCapability(),        # 8. Activities
            audio_cap,                 # 9. Audio Segmentation
            MockSemanticGraphCapability(),     # 10. Semantic Graph
            MockWorldSynthesisCapability()     # 11. Synthesis
        ]

    def execute(self, initial_context: AIContext) -> AIContext:
        trace_id = f"trace-{initial_context.id[:8]}"
        logger.info("m2_workflow_starting", trace_id=trace_id)
        
        current_context = initial_context
        
        for capability in self.pipeline:
            # Each capability returns a brand new AIContext with a mutated immutable WorldState
            current_context = capability.execute(current_context, trace_id)
            
        logger.info("m2_workflow_completed", trace_id=trace_id, final_world=current_context.world.model_dump())
        
        return current_context

@inject
def run_m2_engine(
    metadata_cap: MetadataExtractionCapability = Provide["metadata_cap"],
    shot_cap: ShotDetectionCapability = Provide["shot_cap"],
    doc_cap: DocumentUnderstandingCapability = Provide["doc_cap"],
    audio_cap: AudioSegmentationCapability = Provide["audio_cap"]
):
    context = AIContext(media_id="sample_media.mp4", workflow_id="w-123", language="en")
    engine = MediaUnderstandingEngine(metadata_cap, shot_cap, doc_cap, audio_cap)
    
    final_context = engine.execute(context)
    
    # 12. Snapshot (Re-using the M1 logic concept)
    logger.info("snapshot_generated", context_id=final_context.id)
    
    return final_context

if __name__ == "__main__":
    from bootstrap.container import VerzaContainer
    
    container = VerzaContainer()
    container.init_resources()
    container.wire(modules=[__name__])
    
    run_m2_engine()
