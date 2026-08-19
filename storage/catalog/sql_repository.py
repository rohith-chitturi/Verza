from abc import ABC
from collections.abc import Sequence

from sqlalchemy import select

from contracts.schemas.runtime import (
    VALID_TRANSITIONS,
    ExecutionState,
    IllegalStateTransitionError,
)
from contracts.schemas.workflow import Workflow
from storage.models.runtime import (
    StageRunModel,
    WorkflowDefinitionModel,
    WorkflowRunModel,
    WorkflowVersionModel,
)


class BaseSqlRepository(ABC):
    def __init__(self, session_factory):
        self._session_factory = session_factory

class WorkflowSqlRepository(BaseSqlRepository):
    def save_definition(self, definition: Workflow) -> None:
        with self._session_factory() as session:
            # Upsert definition
            db_def = session.execute(
                select(WorkflowDefinitionModel).where(WorkflowDefinitionModel.name == definition.name)
            ).scalar_one_or_none()
            
            if not db_def:
                db_def = WorkflowDefinitionModel(id=definition.name, name=definition.name)
                session.add(db_def)
                session.flush()
                
            # Upsert version
            db_version = session.execute(
                select(WorkflowVersionModel).where(
                    WorkflowVersionModel.workflow_id == db_def.id,
                    WorkflowVersionModel.version == definition.version
                )
            ).scalar_one_or_none()
            
            if not db_version:
                db_version = WorkflowVersionModel(
                    id=f"{db_def.id}-v{definition.version}",
                    workflow_id=db_def.id,
                    version=definition.version,
                    definition=definition.model_dump()
                )
                session.add(db_version)
            session.commit()

    def get_version(self, name: str, version: str) -> WorkflowVersionModel | None:
        with self._session_factory() as session:
            return session.execute(
                select(WorkflowVersionModel)
                .join(WorkflowDefinitionModel)
                .where(WorkflowDefinitionModel.name == name, WorkflowVersionModel.version == version)
            ).scalar_one_or_none()

class RunSqlRepository(BaseSqlRepository):
    def create_run(self, run_id: str, version_id: str, parent_run_id: str | None = None) -> WorkflowRunModel:
        with self._session_factory() as session:
            run = WorkflowRunModel(
                id=run_id,
                workflow_version_id=version_id,
                parent_run_id=parent_run_id,
                status=ExecutionState.PENDING.value
            )
            session.add(run)
            session.commit()
            return run

    def update_run_status(self, run_id: str, status: ExecutionState) -> None:
        with self._session_factory() as session:
            run = session.execute(select(WorkflowRunModel).where(WorkflowRunModel.id == run_id)).scalar_one_or_none()
            if run:
                current_state = ExecutionState(run.status)
                if status not in VALID_TRANSITIONS[current_state] and status != current_state:
                    raise IllegalStateTransitionError(f"Cannot transition run from {current_state} to {status}")
                run.status = status.value
                session.commit()

    def get_run(self, run_id: str) -> WorkflowRunModel | None:
        with self._session_factory() as session:
            return session.execute(select(WorkflowRunModel).where(WorkflowRunModel.id == run_id)).scalar_one_or_none()

    def get_stage_runs(self, run_id: str) -> Sequence[StageRunModel]:
        with self._session_factory() as session:
            return session.execute(select(StageRunModel).where(StageRunModel.workflow_run_id == run_id)).scalars().all()

    def create_stage_run(self, stage_run_id: str, run_id: str, stage_id: str) -> StageRunModel:
        with self._session_factory() as session:
            stage_run = StageRunModel(
                id=stage_run_id,
                workflow_run_id=run_id,
                stage_id=stage_id,
                status=ExecutionState.PENDING.value
            )
            session.add(stage_run)
            session.commit()
            return stage_run

    def update_stage_status(self, stage_run_id: str, status: ExecutionState) -> None:
        with self._session_factory() as session:
            stage_run = session.execute(select(StageRunModel).where(StageRunModel.id == stage_run_id)).scalar_one_or_none()
            if stage_run:
                current_state = ExecutionState(stage_run.status)
                if status not in VALID_TRANSITIONS[current_state] and status != current_state:
                    raise IllegalStateTransitionError(f"Cannot transition stage from {current_state} to {status}")
                stage_run.status = status.value
                session.commit()
