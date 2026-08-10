from capabilities.cognitive.event_reasoner import EventReasoner
from capabilities.cognitive.intent_reasoner import IntentReasoner
from capabilities.cognitive.relationship_reasoner import RelationshipReasoner
from contracts.schemas.context import ExecutionContext
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import WorldState
from providers.inference.mock_inference import MockInferenceProvider


def test_intent_reasoner_contract():
    state = WorldState()
    context = ExecutionContext(workflow_id="w-1", trace_id="t-1", correlation_id="c-1")
    prompt = PromptAsset(id="intent_reasoner", version="1.0", system_prompt="mock", user_prompt_template="mock", output_schema_version="1.0")
    inference = MockInferenceProvider()
    reasoner = IntentReasoner()
    
    delta = reasoner.reason(state, prompt, context, inference)
    
    assert delta.capability == "intent_reasoning"
    assert len(delta.operations) == 1
    assert delta.operations[0].domain == "semantic.intentions"
    assert delta.operations[0].payload["intent"] == "CONFRONT"
    assert delta.operations[0].origin == "inference"
    assert delta.operations[0].reasoner == "intent_reasoner"

def test_relationship_reasoner_contract():
    state = WorldState()
    context = ExecutionContext(workflow_id="w-1", trace_id="t-1", correlation_id="c-1")
    prompt = PromptAsset(id="relationship_reasoner", version="1.0", system_prompt="mock", user_prompt_template="mock", output_schema_version="1.0")
    inference = MockInferenceProvider()
    reasoner = RelationshipReasoner()
    
    delta = reasoner.reason(state, prompt, context, inference)
    
    assert delta.capability == "relationship_reasoning"
    assert len(delta.operations) == 1
    assert delta.operations[0].domain == "semantic.knowledge_graph.edges"
    assert delta.operations[0].payload["relation"] == "HOSTILE_TOWARDS"
    assert delta.operations[0].operation == "LINK"

def test_event_reasoner_contract():
    state = WorldState()
    context = ExecutionContext(workflow_id="w-1", trace_id="t-1", correlation_id="c-1")
    prompt = PromptAsset(id="event_reasoner", version="1.0", system_prompt="mock", user_prompt_template="mock", output_schema_version="1.0")
    inference = MockInferenceProvider()
    reasoner = EventReasoner()
    
    delta = reasoner.reason(state, prompt, context, inference)
    
    assert delta.capability == "event_reasoning"
    assert len(delta.operations) == 1
    assert delta.operations[0].domain == "semantic.events"
    assert delta.operations[0].payload["type"] == "CONFRONTATION"
