from capabilities.base import BaseCapability
from capabilities.cognitive.memory_indexer import MemoryIndexerCapability
from capabilities.cognitive.semantic_retrieval import SemanticRetrievalCapability
from capabilities.cognitive.synthesis import SynthesisCapability
from contracts.schemas.context import AIContext, ExecutionContext
from core.state.journal import DeltaJournal
from core.state.merger import DeltaMerger
from core.telemetry.logging import get_logger

logger = get_logger("core.workflow.adapters.memory_synthesis")

class MemorySynthesisWorkflowCapability(BaseCapability):
    """
    Adapter bridging the M4 Runtime to the M3.3 Memory & Synthesis layer.
    Orchestrates MemoryIndexer -> SemanticRetrieval -> SynthesisCapability.
    """
    def __init__(
        self, 
        indexer: MemoryIndexerCapability, 
        retrieval: SemanticRetrievalCapability, 
        synthesis: SynthesisCapability,
        merger: DeltaMerger,
        journal: DeltaJournal
    ):
        self._indexer = indexer
        self._retrieval = retrieval
        self._synthesis = synthesis
        self._merger = merger
        self._journal = journal

    @property
    def name(self) -> str:
        return "MemorySynthesisWorkflowCapability"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        exec_ctx = ExecutionContext(
            trace_id=trace_id,
            workflow_id=context.workflow_id,
            tenant_id=context.tenant_id
        )

        current_state = context.world

        # 1. Index current WorldState into Memory
        logger.info("Starting memory indexing", trace_id=trace_id)
        self._indexer.execute(current_state, {
            "run_id": exec_ctx.workflow_id,
            "stage_run_id": exec_ctx.trace_id,
            "tenant_id": exec_ctx.tenant_id
        })

        # 2. Derive synthesis query
        query_text = context.metadata.get(
            "synthesis_query", 
            "Provide a cohesive narrative summary of the key events, relationships, and intents in the current context."
        )

        # 3. Retrieve relevant memory fragments
        logger.info("Starting semantic retrieval", trace_id=trace_id, query=query_text)
        from contracts.schemas.memory import RetrievalQuery
        query_obj = RetrievalQuery(query=query_text, limit=10, min_confidence=0.3)
        retrieved_memories = self._retrieval.execute(query_obj, None)

        # 4. Synthesize narrative
        logger.info("Starting synthesis", trace_id=trace_id)
        synthesis_result = self._synthesis.execute(
            world_state=current_state,
            retrieved_memories=retrieved_memories,
            query_text=query_text
        )

        if not synthesis_result.success:
            logger.error("Synthesis failed", trace_id=trace_id)
            return context

        # 5. Attach synthesis result to context metadata (Synthesis does not mutate WorldState)
        context.metadata["synthesis"] = {
            "narrative": synthesis_result.narrative,
            "key_events": synthesis_result.key_events,
            "citations": synthesis_result.memory_citations,
            "confidence": synthesis_result.confidence
        }

        return context
