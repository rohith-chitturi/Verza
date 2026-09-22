import pytest

from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import ProviderPolicy, Stage, Workflow
from core.registry.capability import CapabilityRegistry
from core.workflow.runtime import WorkflowRuntime


# We need a mocked registry just for testing the M4 engine's persistence logic independent of M2.
class PersistenceMockCapability:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        
    def execute(self, context=None, trace_id=None, **kwargs):
        if self.should_fail:
            raise RuntimeError("Intentional failure for rollback test")
        return context

@pytest.fixture
def persistence_registry():
    return CapabilityRegistry({
        "mock_success": lambda: PersistenceMockCapability(should_fail=False),
        "mock_fail": lambda: PersistenceMockCapability(should_fail=True)
    })

@pytest.fixture
def runtime(persistence_registry, repo):
    return WorkflowRuntime(persistence_registry, repo)

def test_transaction_rollback_on_failure(runtime, repo, workflow_repo, session_factory):
    """
    Phase 3: Verify rollback / transaction scope.
    If a run is being updated but an exception occurs, the DB should rollback.
    The RunSqlRepository creates its own sessions and commits for each atomic update.
    """
    workflow = Workflow(
        id="wf-rollback", version="1.0", name="rollback_test",
        stages=[
            Stage(id="stage_1", capability="mock_fail", provider_policy=ProviderPolicy(primary="mock"))
        ]
    )
    workflow_repo.save_definition(workflow)
    
    run_id = "RUN-ROLLBACK-TEST"
    repo.create_run(run_id, f"{workflow.name}-v{workflow.version}")
    repo.update_run_status(run_id, ExecutionState.QUEUED)
    
    # We attempt to execute it. The stage will fail.
    # The runtime should catch the error, update the state to FAILED, and the DB should remain consistent.
    runtime._execute_run(run_id, workflow)
    
    # Open a fresh session to read back
    with session_factory():
        run = repo.get_run(run_id)
        assert run is not None
        assert run.status == ExecutionState.FAILED.value
        
        stages = repo.get_stage_runs(run_id)
        assert len(stages) == 1
        assert stages[0].status == ExecutionState.FAILED.value

def test_resume_preserves_postgres_state(runtime, repo, workflow_repo):
    """
    Phase 8: Resume with real PostgreSQL.
    Prove that a crashed run can be resumed and it skips completed stages in PostgreSQL.
    """
    workflow = Workflow(
        id="wf-resume", version="1.0", name="resume_pg_test",
        stages=[
            Stage(id="s1", capability="mock_success", provider_policy=ProviderPolicy(primary="mock")),
            Stage(id="s2", capability="mock_success", provider_policy=ProviderPolicy(primary="mock"), depends_on=["s1"])
        ]
    )
    workflow_repo.save_definition(workflow)
    
    run_id = "RUN-RESUME-PG"
    repo.create_run(run_id, f"{workflow.name}-v{workflow.version}")
    repo.update_run_status(run_id, ExecutionState.QUEUED)
    repo.update_run_status(run_id, ExecutionState.RUNNING)
    
    # Manually mark S1 as completed to simulate a crashed run halfway through
    repo.create_stage_run("SR-S1", run_id, "s1")
    repo.update_stage_status("SR-S1", ExecutionState.QUEUED)
    repo.update_stage_status("SR-S1", ExecutionState.RUNNING)
    repo.update_stage_status("SR-S1", ExecutionState.COMPLETED)
    
    # Simulating a crash, we need to transition it to FAILED or PAUSED, but actually in this test, 
    # it crashed. The cleanup task marks it as FAILED, then we resume it.
    repo.update_run_status(run_id, ExecutionState.FAILED)
    repo.update_run_status(run_id, ExecutionState.QUEUED)
    
    # Run the workflow. S1 should be skipped, S2 should execute and complete.
    runtime._execute_run(run_id, workflow)
    
    run = repo.get_run(run_id)
    assert run.status == ExecutionState.COMPLETED.value
    
    stages = {s.stage_id: s for s in repo.get_stage_runs(run_id)}
    assert len(stages) == 2
    assert stages["s1"].status == ExecutionState.COMPLETED.value
    assert stages["s2"].status == ExecutionState.COMPLETED.value

def test_replay_with_postgres(runtime, repo, workflow_repo):
    """
    Phase 9: Replay with PostgreSQL.
    Fork run, reuse state, verify lineage.
    """
    workflow = Workflow(
        id="wf-replay", version="1.0", name="replay_pg_test",
        stages=[
            Stage(id="s1", capability="mock_success", provider_policy=ProviderPolicy(primary="mock")),
            Stage(id="s2", capability="mock_success", provider_policy=ProviderPolicy(primary="mock"), depends_on=["s1"])
        ]
    )
    workflow_repo.save_definition(workflow)
    
    old_run_id = "RUN-OLD-PG"
    repo.create_run(old_run_id, f"{workflow.name}-v{workflow.version}")
    repo.update_run_status(old_run_id, ExecutionState.QUEUED)
    runtime._execute_run(old_run_id, workflow)
    
    assert repo.get_run(old_run_id).status == ExecutionState.COMPLETED.value
    
    new_run_id = "RUN-NEW-PG"
    repo.create_run(new_run_id, f"{workflow.name}-v{workflow.version}", parent_run_id=old_run_id)
    repo.update_run_status(new_run_id, ExecutionState.QUEUED)
    
    # Replay from s2
    runtime._execute_run(new_run_id, workflow, replay_from_stage="s2")
    
    new_run = repo.get_run(new_run_id)
    assert new_run.status == ExecutionState.COMPLETED.value
    assert new_run.parent_run_id == old_run_id
    
    # Both runs should exist in the DB
    assert repo.get_run(old_run_id) is not None
