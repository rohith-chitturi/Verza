import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bootstrap.container import VerzaContainer
from capabilities.cognitive.activity_interpreter import ActivityOutputSchema
from capabilities.cognitive.character_interpreter import CharacterOutputSchema
from capabilities.cognitive.scene_interpreter import SceneOutputSchema
from contracts.schemas.context import AIContext
from contracts.schemas.prompt import PromptAsset
from core.telemetry.logging import get_logger
from core.workflow.interpretation import InterpretationEngine

logger = get_logger("scripts.run_m31")

def seed_registry(registry):
    # Scene Prompt
    registry.register(PromptAsset(
        id="prompt_sceneinterpreter",
        version="1.0.0",
        system_prompt="You are an expert film scene analyzer.",
        user_prompt_template="Analyze this scene.",
        output_schema_version="1.0",
        expected_schema=SceneOutputSchema,
        compatible_models=["gpt-4o", "gemini-1.5-pro"]
    ))
    
    # Character Prompt
    registry.register(PromptAsset(
        id="prompt_characterinterpreter",
        version="1.0.0",
        system_prompt="You are an expert character profiler.",
        user_prompt_template="Identify characters.",
        output_schema_version="1.0",
        expected_schema=CharacterOutputSchema,
        compatible_models=["gpt-4o", "gemini-1.5-pro"]
    ))
    
    # Activity Prompt
    registry.register(PromptAsset(
        id="prompt_activityinterpreter",
        version="1.0.0",
        system_prompt="You are an expert activity recognizer.",
        user_prompt_template="Detect activities.",
        output_schema_version="1.0",
        expected_schema=ActivityOutputSchema,
        compatible_models=["gpt-4o", "gemini-1.5-pro"]
    ))


def run():
    container = VerzaContainer()
    container.init_resources()
    
    # Get components
    interpreters = [
        container.scene_interpreter(),
        container.character_interpreter(),
        container.activity_interpreter()
    ]
    vlm_provider = container.mock_vlm_provider()
    registry = container.prompt_registry()
    validator = container.delta_validator()
    merger = container.delta_merger()
    journal = container.delta_journal()
    
    # Seed prompts
    seed_registry(registry)
    
    engine = InterpretationEngine(
        interpreters=interpreters,
        vlm_provider=vlm_provider,
        prompt_registry=registry,
        validator=validator,
        merger=merger,
        journal=journal
    )
    
    # Run
    context = AIContext(media_id="test_media.mp4", workflow_id="w-m31", language="en")
    logger.info("Executing M3.1 Engine...")
    final_context = engine.execute(context)
    
    # Print Journal
    history = journal.get_history()
    print("\n" + "="*50)
    print(f"M3.1 SUCCESS! DELTA JOURNAL (Count: {len(history)})")
    print("="*50)
    
    for d in history:
        print(f"\nDelta ID: {d.id} | Capability: {d.capability}")
        for op in d.operations:
            print(f"  -> Operation: {op.operation.name} | Domain: {op.domain}")
            print(f"  -> Confidence: {op.confidence.confidence:.2f}")
            print(f"  -> Payload: {op.payload}")
            
    print("\n" + "="*50)
    print("FINAL WORLD STATE PREVIEW:")
    print("Scenes:", final_context.world.visual.scenes)
    print("Characters:", [c.model_dump() for c in final_context.world.visual.characters])
    print("Activities:", [a.model_dump() for a in final_context.world.visual.activities])
    print("="*50)

if __name__ == "__main__":
    run()
