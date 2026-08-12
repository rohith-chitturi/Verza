import pytest
from contracts.schemas.workflow import Workflow, Stage, ProviderPolicy
from core.workflow.validation import WorkflowValidator, WorkflowValidationError

@pytest.fixture
def validator():
    return WorkflowValidator(
        registered_capabilities={"media_understanding", "interpretation"},
        registered_providers={"openai", "google"}
    )

def test_valid_workflow(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(
                id="s1",
                capability="media_understanding",
                provider_policy=ProviderPolicy(primary="openai")
            ),
            Stage(
                id="s2",
                capability="interpretation",
                provider_policy=ProviderPolicy(primary="google", fallback=["openai"]),
                depends_on=["s1"]
            )
        ]
    )
    assert validator.validate(workflow) is True

def test_duplicate_stage_id(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(id="s1", capability="media_understanding", provider_policy=ProviderPolicy(primary="openai")),
            Stage(id="s1", capability="interpretation", provider_policy=ProviderPolicy(primary="openai"))
        ]
    )
    with pytest.raises(WorkflowValidationError, match="Duplicate stage ID found"):
        validator.validate(workflow)

def test_missing_dependency(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(
                id="s2",
                capability="interpretation",
                provider_policy=ProviderPolicy(primary="openai"),
                depends_on=["s1"]
            )
        ]
    )
    with pytest.raises(WorkflowValidationError, match="depends on unknown stage: 's1'"):
        validator.validate(workflow)

def test_circular_dependency(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(id="s1", capability="media_understanding", provider_policy=ProviderPolicy(primary="openai"), depends_on=["s2"]),
            Stage(id="s2", capability="interpretation", provider_policy=ProviderPolicy(primary="openai"), depends_on=["s1"])
        ]
    )
    with pytest.raises(WorkflowValidationError, match="Circular dependency"):
        validator.validate(workflow)

def test_unknown_capability(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(id="s1", capability="unknown_cap", provider_policy=ProviderPolicy(primary="openai"))
        ]
    )
    with pytest.raises(WorkflowValidationError, match="requires unknown capability: 'unknown_cap'"):
        validator.validate(workflow)

def test_unknown_provider(validator):
    workflow = Workflow(
        id="w1",
        version="1.0",
        name="test",
        stages=[
            Stage(id="s1", capability="media_understanding", provider_policy=ProviderPolicy(primary="unknown_provider"))
        ]
    )
    with pytest.raises(WorkflowValidationError, match="requires unknown primary provider: 'unknown_provider'"):
        validator.validate(workflow)
