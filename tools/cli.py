from pathlib import Path

import typer
import yaml
from dependency_injector.wiring import Provide, inject

from bootstrap.container import VerzaContainer
from contracts.schemas.workflow import Workflow
from control_plane.application.errors import DomainError
from control_plane.application.workflow_service import WorkflowService
from storage.models.runtime import Base

app = typer.Typer(help="Verza Platform CLI")


def get_service() -> WorkflowService:
    container = VerzaContainer()
    # For CLI prototype, ensure models are created if using a local DB
    # (If using real postgres, alembic handles this, but we'll do this just in case)
    engine = container.db_engine()
    Base.metadata.create_all(engine)
    return container.workflow_service()


@app.command()
def validate(
    workflow_path: Path = typer.Argument(..., help="Path to workflow YAML"),  # noqa: B008
):
    """Validates a workflow definition without executing it."""
    if not workflow_path.exists():
        typer.secho(f"Workflow file not found: {workflow_path}", fg=typer.colors.RED)
        raise typer.Exit(1)

    with open(workflow_path) as f:
        data = yaml.safe_load(f)
        try:
            definition = Workflow(**data)
            typer.secho(f"Workflow is valid: {definition.name} (v{definition.version})", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"Validation failed: {e}", fg=typer.colors.RED)
            raise typer.Exit(1)


@app.command()
def run(
    workflow_path: Path = typer.Argument(..., help="Path to workflow YAML"),  # noqa: B008
):
    """Registers and starts a workflow execution."""
    if not workflow_path.exists():
        typer.secho(f"Workflow file not found: {workflow_path}", fg=typer.colors.RED)
        raise typer.Exit(1)

    with open(workflow_path) as f:
        data = yaml.safe_load(f)
        definition = Workflow(**data)

    service = get_service()
    
    try:
        # Register definition if not exists
        try:
            service.register_workflow(definition)
            typer.secho(f"Registered workflow: {definition.name} (v{definition.version})", fg=typer.colors.GREEN)
        except DomainError:
            typer.secho(f"Workflow {definition.name} (v{definition.version}) already registered.", fg=typer.colors.YELLOW)
            
        typer.secho("Starting workflow execution...", fg=typer.colors.BLUE)
        run_id = service.start_run(definition.name, definition.version)
        typer.secho(f"Workflow dispatched. Run ID: {run_id}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Failed to start run: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def status(
    run_id: str = typer.Argument(..., help="Run ID to check"),  # noqa: B008
):
    """Gets the status of a workflow run."""
    service = get_service()
    try:
        typer.secho(f"Fetching status for {run_id}...", fg=typer.colors.BLUE)
        status_info = service.get_run_status(run_id)
        typer.secho(f"Status: {status_info['status']}", fg=typer.colors.GREEN)
        typer.secho(f"Workflow: {status_info['workflow_version_id']}")
    except DomainError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def pause(
    run_id: str = typer.Argument(..., help="Run ID to pause"),  # noqa: B008
):
    """Requests a cooperative pause for a workflow run."""
    service = get_service()
    try:
        service.pause_run(run_id)
        typer.secho(f"Pause requested for run {run_id}.", fg=typer.colors.YELLOW)
    except DomainError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def resume(
    run_id: str = typer.Argument(..., help="Run ID to resume"),  # noqa: B008
):
    """Resumes a paused workflow run."""
    service = get_service()
    try:
        service.resume_run(run_id)
        typer.secho(f"Resume requested for run {run_id}.", fg=typer.colors.GREEN)
    except DomainError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def cancel(
    run_id: str = typer.Argument(..., help="Run ID to cancel"),  # noqa: B008
):
    """Cancels a workflow run."""
    service = get_service()
    try:
        service.cancel_run(run_id)
        typer.secho(f"Cancel requested for run {run_id}.", fg=typer.colors.RED)
    except DomainError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def replay(
    run_id: str = typer.Argument(..., help="Run ID to replay"),  # noqa: B008
    from_stage: str = typer.Option(..., "--from-stage", help="Stage to replay from"),
):
    """Forks a run and restarts from a specific stage."""
    service = get_service()
    try:
        new_run_id = service.replay_run(run_id, from_stage)
        typer.secho(f"Replay dispatched. New Run ID: {new_run_id}", fg=typer.colors.GREEN)
    except DomainError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
