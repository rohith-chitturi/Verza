import os
import sys

# Add parent directory to path to allow running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bootstrap.container import VerzaContainer
from contracts.schemas.context import ExecutionContext
from contracts.schemas.world import Activity, Character, Evidence, WorldState


def run_demo():
    print("Initializing Verza M3.2 Reasoning Engine Demo...\n")

    # 1. Initialize DI Container
    container = VerzaContainer()
    engine = container.reasoning_engine()

    # 2. Seed an initial WorldState with some M3.1 interpretations
    print("Setting up initial WorldState (M3.1 Interpretation Output)...")
    initial_state = WorldState()

    # Mocking what M3.1 would have produced
    john = Character(id="character-john", appearances=["shot-1"])
    sarah = Character(id="character-sarah", appearances=["shot-1"])
    activity = Activity(
        type="Walking Aggressively",
        participants=[john.id],
        evidence=Evidence(shots=["shot-1"]),
    )

    # We mutate for setup purposes
    initial_state.visual.characters.append(john)
    initial_state.visual.characters.append(sarah)
    initial_state.visual.activities.append(activity)

    context = ExecutionContext(
        workflow_id="demo-m32-001",
        trace_id="demo-trace-1",
        correlation_id="demo-corr-1",
    )

    # 3. Run the Reasoning Engine
    print("\nExecuting Reasoning Engine (Intent -> Relationship -> Event)...\n")
    final_state = engine.run(initial_state, context)

    # 4. Display Results
    print("=== M3.2 Reasoning Results ===")

    print("\n[Intents]")
    for intent in final_state.semantic.intentions:
        print(f" - Actor: {intent.actor}")
        print(f"   Target: {intent.target}")
        print(f"   Intent: {intent.intent}")
        print(f"   Confidence: {intent.confidence}")

    print("\n[Knowledge Graph Edges]")
    for edge in final_state.semantic.knowledge_graph.edges:
        print(
            f" - {edge.source} -> {edge.relation} -> {edge.target} (Confidence: {edge.confidence})"
        )

    print("\n[Structured Events]")
    for event in final_state.semantic.events:
        print(f" - Type: {event.type}")
        print(f"   Participants: {event.participants}")
        print(f"   Causes: {event.causes}")
        print(f"   Consequences: {event.consequences}")
        print(f"   Confidence: {event.confidence}")

    print("\nDemo completed successfully.")


if __name__ == "__main__":
    run_demo()
