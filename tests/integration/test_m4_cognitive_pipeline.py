import os

import pytest

from bootstrap.container import VerzaContainer
from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import ProviderPolicy, Stage, Workflow
from core.workflow.runtime import WorkflowRuntime
from storage.catalog.sql_repository import RunSqlRepository
from tests.integration.fixtures.generate_media import generate_test_wav


@pytest.fixture
def real_media_file():
    filepath = "tests/integration/fixtures/test_media.wav"
    generate_test_wav(filepath)
    yield filepath
    if os.path.exists(filepath):
        os.remove(filepath)

@pytest.fixture
def test_container(session_factory):
    container = VerzaContainer()
    
    # We want to mock VLM and Inference for deterministic tests, 
    # but use the real M4 DAG and the real PostgreSQL DB.
    # The container defaults to gemini_vlm_provider, let's override it
    from interfaces.cognitive.mock_vlm import MockVLMProvider
    from providers.inference.mock_inference import MockInferenceProvider
    
    container.vlm_provider.override(container.mock_vlm_provider)
    container.inference_provider.override(container.mock_inference_provider)
    
    # Override the database session to use the pytest fixture
    from dependency_injector import providers
    container.db_session_factory.override(providers.Singleton(lambda: session_factory))
    
    return container

@pytest.fixture
def test_runtime(test_container, session_factory):
    repo = RunSqlRepository(session_factory)
    return WorkflowRuntime(test_container.capability_registry(), repo)

def test_m4_cognitive_pipeline_execution(test_runtime, repo, workflow_repo, test_container, real_media_file):
    """
    Phase 10: Real M4 Workflow execution mapping M2 -> M3.1 -> M3.2 -> M3.3.
    """
    workflow = Workflow(
        id="wf-m4-cognitive", version="1.0", name="m4_cognitive_pipeline",
        stages=[
            Stage(id="metadata", capability="metadata_extraction", provider_policy=ProviderPolicy(primary="ffmpeg")),
            Stage(id="interpretation", capability="interpretation", provider_policy=ProviderPolicy(primary="mock"), depends_on=["metadata"]),
            Stage(id="reasoning", capability="reasoning", provider_policy=ProviderPolicy(primary="mock"), depends_on=["interpretation"]),
            Stage(id="memory_synthesis", capability="memory_synthesis", provider_policy=ProviderPolicy(primary="mock"), depends_on=["reasoning"])
        ]
    )
    workflow_repo.save_definition(workflow)
    
    run_id = "RUN-M4-COGNITIVE"
    repo.create_run(run_id, f"{workflow.name}-v{workflow.version}")
    repo.update_run_status(run_id, ExecutionState.QUEUED)
    
    # Execute the workflow synchronously for testing
    try:
        test_runtime._execute_run(run_id, workflow)
    except Exception as e:
        if "ENVIRONMENT DEPENDENCY FAILURE" in str(e):
            pytest.fail(f"Environment dependency missing for ffmpeg: {e}")
        else:
            raise

    run = repo.get_run(run_id)
    assert run is not None
    assert run.status == ExecutionState.COMPLETED.value
    
    stages = {s.stage_id: s for s in repo.get_stage_runs(run_id)}
    assert len(stages) == 4
    for stage_id in ["metadata", "interpretation", "reasoning", "memory_synthesis"]:
        assert stages[stage_id].status == ExecutionState.COMPLETED.value
        
    # Verify the world state was successfully persisted and hydrated across stages
    world_state = repo.get_world_state(run_id)
    assert world_state is not None
