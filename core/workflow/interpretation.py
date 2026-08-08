from contracts.schemas.context import AIContext, ExecutionContext
from contracts.schemas.world import Evidence
from core.prompts.registry import PromptRegistry
from core.state.journal import DeltaJournal
from core.state.merger import DeltaMerger
from core.state.validator import DeltaValidator
from core.telemetry.logging import get_logger
from interfaces.cognitive.interpreter import BaseInterpreter
from interfaces.cognitive.vlm_provider import VLMProvider

logger = get_logger("workflow.interpretation")

class InterpretationEngine:
    """
    Executes M3.1: Interpretation Phase.
    Pipeline: Interpreter -> Delta -> Validator -> Merger -> Journal -> WorldState
    """
    def __init__(
        self,
        interpreters: list[BaseInterpreter],
        vlm_provider: VLMProvider,
        prompt_registry: PromptRegistry,
        validator: DeltaValidator,
        merger: DeltaMerger,
        journal: DeltaJournal
    ):
        self.interpreters = interpreters
        self.vlm_provider = vlm_provider
        self.prompt_registry = prompt_registry
        self.validator = validator
        self.merger = merger
        self.journal = journal
        
    def execute(self, initial_context: AIContext) -> AIContext:
        trace_id = f"trace-m31-{initial_context.id[:8]}"
        logger.info("m31_interpretation_workflow_starting", trace_id=trace_id)
        
        exec_ctx = ExecutionContext(
            trace_id=trace_id,
            workflow_id=initial_context.workflow_id,
            tenant_id=initial_context.tenant_id
        )
        
        current_state = initial_context.world
        
        # Simple evidence for demo
        evidence = Evidence(frames=[0, 100], shots=["shot-001"])
        
        for interpreter in self.interpreters:
            # 1. Load corresponding prompt
            prompt_id = f"prompt_{interpreter.name.lower()}"
            try:
                prompt = self.prompt_registry.get_prompt(prompt_id, "1.0.0")
            except ValueError as e:
                logger.error(f"Missing prompt for {interpreter.name}: {e}")
                continue
                
            # 2. Interpret -> Generate Delta
            try:
                delta = interpreter.interpret(
                    world_state=current_state,
                    evidence=evidence,
                    prompt=prompt,
                    context=exec_ctx,
                    vlm_provider=self.vlm_provider
                )
            except Exception as e:
                logger.error(f"Interpreter {interpreter.name} failed: {e}")
                continue
            
            # 3. Validate Delta
            is_valid = self.validator.validate(delta, current_state)
            if not is_valid:
                logger.warning(f"Delta from {interpreter.name} failed validation, skipping.")
                continue
                
            # 4. Merge Delta
            current_state = self.merger.merge(current_state, delta)
            
            # 5. Journal accepted Delta
            self.journal.append(delta)
            
            logger.info(f"Successfully applied delta from {interpreter.name}")
            
        final_context = initial_context.with_world(current_state)
        logger.info("m31_interpretation_workflow_completed", trace_id=trace_id, journal_size=len(self.journal.get_history()))
        
        return final_context
