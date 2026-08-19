import typer
import yaml
from pathlib import Path

from contracts.schemas.workflow import Workflow
from core.workflow.runtime import WorkflowRuntime
from storage.catalog.sql_repository import RunSqlRepository
from bootstrap.container import VerzaContainer

app = typer.Typer(help="Verza Platform CLI")

# Global container init (mocked here, should be proper DI)
container = VerzaContainer()

@app.command()
def run(
    workflow_path: Path = typer.Argument(..., help="Path to workflow YAML"),
    resume_from: str = typer.Option(None, "--resume-from", help="Run ID to resume from")
):
    """Executes a workflow definition."""
    if not workflow_path.exists():
        typer.secho(f"Workflow file not found: {workflow_path}", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    with open(workflow_path, "r") as f:
        data = yaml.safe_load(f)
        definition = Workflow(**data)
        
    typer.secho(f"Loaded workflow: {definition.name} (v{definition.version})", fg=typer.colors.GREEN)
    
    # Normally we'd fetch this from container
    # runtime = container.workflow_runtime()
    from storage.catalog.sql_repository import BaseSqlRepository
    # Dummy session factory for prototype
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("sqlite:///:memory:")
    from storage.models.runtime import Base
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    repo = RunSqlRepository(SessionLocal)
    runtime = WorkflowRuntime(capability_registry=container.capability_registry(), run_repository=repo)
    
    if resume_from:
        typer.secho(f"Resuming from Run ID: {resume_from}", fg=typer.colors.YELLOW)
        # Logic to resume
        run_id = runtime.start_run(definition, parent_run_id=resume_from)
    else:
        typer.secho("Starting new workflow execution...", fg=typer.colors.BLUE)
        run_id = runtime.start_run(definition)
        
    typer.secho(f"Workflow dispatched. Run ID: {run_id}", fg=typer.colors.GREEN)

@app.command()
def status(run_id: str):
    """Gets the status of a workflow run."""
    typer.secho(f"Fetching status for {run_id}...", fg=typer.colors.BLUE)
    # repo.get_run(run_id)
    typer.secho(f"Status: RUNNING", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
