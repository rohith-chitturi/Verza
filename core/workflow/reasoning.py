from concurrent.futures import ThreadPoolExecutor

from contracts.schemas.context import ExecutionContext
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import WorldState
from core.prompts.registry import PromptRegistry
from core.state.consistency import ConsistencyChecker, ConsistencyState
from core.state.journal import DeltaJournal
from core.state.merger import DeltaMerger
from core.state.validator import DeltaValidator
from core.telemetry.logging import get_logger
from interfaces.cognitive.inference import InferenceProvider
from interfaces.cognitive.reasoner import BaseReasoner

logger = get_logger("core.workflow.reasoning")


class ReasoningEngine:
    """
    Orchestrates the Reasoning layer.
    Executes Intent and Relationship reasoners in parallel,
    then executes Event reasoner sequentially.
    """

    def __init__(
        self,
        inference_provider: InferenceProvider,
        intent_reasoner: BaseReasoner,
        relationship_reasoner: BaseReasoner,
        event_reasoner: BaseReasoner,
        validator: DeltaValidator,
        consistency_checker: ConsistencyChecker,
        merger: DeltaMerger,
        journal: DeltaJournal,
        prompt_registry: PromptRegistry,
    ):
        self._inference = inference_provider
        self._intent_reasoner = intent_reasoner
        self._relationship_reasoner = relationship_reasoner
        self._event_reasoner = event_reasoner

        self._validator = validator
        self._consistency_checker = consistency_checker
        self._merger = merger
        self._journal = journal
        self._prompt_registry = prompt_registry

    def run(self, initial_state: WorldState, context: ExecutionContext) -> WorldState:
        current_state = initial_state
        logger.info("Starting Reasoning Engine", trace_id=context.trace_id)

        try:
            intent_prompt = self._prompt_registry.get_prompt("intent_reasoner", "1.0")
        except ValueError:
            intent_prompt = PromptAsset(
                id="intent_reasoner",
                version="1.0",
                system_prompt="mock",
                user_prompt_template="mock",
                output_schema_version="1.0",
            )

        try:
            relationship_prompt = self._prompt_registry.get_prompt(
                "relationship_reasoner", "1.0"
            )
        except ValueError:
            relationship_prompt = PromptAsset(
                id="relationship_reasoner",
                version="1.0",
                system_prompt="mock",
                user_prompt_template="mock",
                output_schema_version="1.0",
            )

        try:
            event_prompt = self._prompt_registry.get_prompt("event_reasoner", "1.0")
        except ValueError:
            event_prompt = PromptAsset(
                id="event_reasoner",
                version="1.0",
                system_prompt="mock",
                user_prompt_template="mock",
                output_schema_version="1.0",
            )

        # Step 1: Parallel Execution for Intent & Relationship
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_intent = executor.submit(
                self._intent_reasoner.reason,
                current_state,
                intent_prompt,
                context,
                self._inference,
            )
            future_relationship = executor.submit(
                self._relationship_reasoner.reason,
                current_state,
                relationship_prompt,
                context,
                self._inference,
            )

            intent_delta = future_intent.result()
            relationship_delta = future_relationship.result()

        # Process deltas (Intent)
        current_state = self._process_delta(intent_delta, current_state)
        # Process deltas (Relationship)
        current_state = self._process_delta(relationship_delta, current_state)

        # Step 2: Sequential Execution for Event (depends on Intents)
        event_delta = self._event_reasoner.reason(
            current_state, event_prompt, context, self._inference
        )
        current_state = self._process_delta(event_delta, current_state)

        logger.info("Reasoning Engine Completed", trace_id=context.trace_id)
        return current_state

    def _process_delta(self, delta, state: WorldState) -> WorldState:
        # Validate schema and semantics
        is_valid = self._validator.validate(delta, state)
        if not is_valid:
            logger.error(f"Delta {delta.id} validation failed")
            return state

        # Check consistency
        consistency = self._consistency_checker.check(delta, state)
        if consistency.state in [
            ConsistencyState.CONFLICTING,
            ConsistencyState.DUPLICATE,
        ]:
            logger.warning(
                f"Delta {delta.id} consistency issue: {consistency.state} - {consistency.reason}"
            )
            # In a real app we might still merge, or drop it. We'll drop duplicates here.
            if consistency.state == ConsistencyState.DUPLICATE:
                return state

        # Merge
        new_state = self._merger.merge(state, delta)

        # Journal
        # Normally target_world_state_id is set before journaling
        # Hack for immutability: just journal it.
        self._journal.append(delta)

        return new_state
