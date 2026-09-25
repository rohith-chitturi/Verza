import threading
import time

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from bootstrap.app import app
from bootstrap.container import VerzaContainer
from contracts.schemas.runtime import ExecutionState
from storage.models.runtime import Base
from tools.cli import app as cli_app

runner = CliRunner()


class ControlledWaitCapability:
    def __init__(self, event: threading.Event):
        self.event = event

    def execute(self, context=None, trace_id=None, exec_context=None, **kwargs):
        from contracts.schemas.execution import PauseRequested, CancelledError
        # Block until the test sets the event, but cooperatively check tokens
        start_time = time.time()
        while not self.event.is_set():
            if exec_context and exec_context.is_cancelled():
                raise CancelledError()
            if exec_context and exec_context.is_pause_requested():
                raise PauseRequested()
            if time.time() - start_time > 5.0:
                break
            time.sleep(0.1)
        return context


@pytest.fixture
def sync_db_engine():
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def container(sync_db_engine):
    container = VerzaContainer()
    container.db_engine.override(sync_db_engine)
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=sync_db_engine)
    container.db_session_factory.override(SessionLocal)
    
    return container


@pytest.fixture
def test_client(container):
    app.container = container
    from control_plane.api.routers import workflow
    container.wire(modules=[workflow])
    with TestClient(app) as client:
        yield client


def test_api_lifecycle_with_pause_resume(test_client, container):
    # Setup test workflow with wait capability
    wait_event = threading.Event()
    wait_cap = ControlledWaitCapability(wait_event)
    
    registry = container.capability_registry()
    def resolve_wait_cap_api():
        return wait_cap
    # Temporarily add our test capability
    registry._resolvers["wait_stage"] = resolve_wait_cap_api

    workflow_payload = {
        "workflow": {
            "id": "test_pause_resume_wf",
            "name": "test_pause_resume",
            "version": "1.0",
            "stages": [
                {
                    "id": "stage1",
                    "capability": "wait_stage",
                    "provider_policy": {"primary": "wait_stage"},
                    "depends_on": []
                },
                {
                    "id": "stage2",
                    "capability": "wait_stage",
                    "provider_policy": {"primary": "wait_stage"},
                    "depends_on": ["stage1"]
                }
            ]
        }
    }

    # 1. Register Workflow
    response = test_client.post("/api/v1/workflows", json=workflow_payload)
    assert response.status_code == 201, f"Validation failed: {response.text}"
    assert response.json()["name"] == "test_pause_resume"

    # 2. Start Run (202 Accepted)
    response = test_client.post("/api/v1/runs", json={
        "workflow_name": "test_pause_resume",
        "version": "1.0"
    })
    assert response.status_code == 202, f"Failed to start run: {response.text}"
    run_id = response.json()["run_id"]

    # At this point, the thread is started and blocked in stage1
    time.sleep(0.1) # Yield slightly for thread to enter stage1

    # 3. Status should be RUNNING
    response = test_client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["status"] == ExecutionState.RUNNING.value

    # 4. Request Pause
    response = test_client.post(f"/api/v1/runs/{run_id}/pause")
    assert response.status_code == 202

    # Now unblock stage1
    wait_event.set()
    
    # Wait for the workflow thread to complete stage1, check DB, and halt
    time.sleep(0.2)

    # 5. Status should be PAUSED
    response = test_client.get(f"/api/v1/runs/{run_id}")
    assert response.json()["status"] == ExecutionState.PAUSED.value

    # 6. Resume
    wait_event.clear() # Reset for stage2
    response = test_client.post(f"/api/v1/runs/{run_id}/resume")
    assert response.status_code == 202

    time.sleep(0.1) # Yield slightly for thread to enter stage2
    
    # Unblock stage2
    wait_event.set()
    
    # Wait for completion
    time.sleep(0.2)
    
    # 7. Status should be COMPLETED
    response = test_client.get(f"/api/v1/runs/{run_id}")
    assert response.json()["status"] == ExecutionState.COMPLETED.value


def test_cli_lifecycle_commands(container, tmp_path):
    wait_event = threading.Event()
    wait_cap = ControlledWaitCapability(wait_event)
    registry = container.capability_registry()
    def resolve_wait_cap():
        return wait_cap
    registry._resolvers["wait_stage"] = resolve_wait_cap

    # This is a bit tricky as CLI creates its own container by default,
    # but we can monkey-patch tools.cli.VerzaContainer to return ours
    import tools.cli
    def mock_container():
        return container
    tools.cli.VerzaContainer = mock_container
    
    # Create dummy workflow file
    workflow_yaml = """
id: cli_test_wf
name: cli_test
version: '1.0'
stages:
  - id: stage1
    capability: wait_stage
    provider_policy:
      primary: wait_stage
"""
    wf_file = tmp_path / "cli_workflow.yaml"
    wf_file.write_text(workflow_yaml)
    
    # Validate
    result = runner.invoke(cli_app, ["validate", str(wf_file)], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Workflow is valid" in result.stdout
    
    # Run
    result = runner.invoke(cli_app, ["run", str(wf_file)], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Workflow dispatched" in result.stdout
    
    # Extract run ID from output
    import re
    match = re.search(r"Run ID: (RUN-\w+)", result.stdout)
    assert match
    run_id = match.group(1)
    
    # Give it a moment to start
    import time
    time.sleep(0.1)
    
    # Status
    result = runner.invoke(cli_app, ["status", run_id], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Status:" in result.stdout
    
    # Pause
    result = runner.invoke(cli_app, ["pause", run_id], catch_exceptions=False)
    assert result.exit_code == 0
    
    # Unblock the wait stage so the thread can terminate gracefully
    wait_event.set()
    
    # Cancel
    result = runner.invoke(cli_app, ["cancel", run_id], catch_exceptions=False)
    assert result.exit_code == 0
