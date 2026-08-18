import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WorkflowDefinitionModel(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowVersionModel(Base):
    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow_definitions.id"))
    version: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON)  # The parsed YAML
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_version_id: Mapped[str] = mapped_column(ForeignKey("workflow_versions.id"))
    parent_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=True
    )  # For replay lineage
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    stage_runs: Mapped[list["StageRunModel"]] = relationship(
        back_populates="workflow_run"
    )


class StageRunModel(Base):
    __tablename__ = "stage_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"))
    stage_id: Mapped[str] = mapped_column(String, nullable=False)  # ID from YAML
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    workflow_run: Mapped["WorkflowRunModel"] = relationship(back_populates="stage_runs")
    attempts: Mapped[list["TaskAttemptModel"]] = relationship(
        back_populates="stage_run"
    )


class TaskAttemptModel(Base):
    __tablename__ = "task_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    stage_run_id: Mapped[str] = mapped_column(ForeignKey("stage_runs.id"))
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    stage_run: Mapped["StageRunModel"] = relationship(back_populates="attempts")


class CheckpointModel(Base):
    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"))
    stage_run_id: Mapped[str] = mapped_column(ForeignKey("stage_runs.id"))
    world_state_snapshot_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExecutionEventModel(Base):
    __tablename__ = "execution_events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"))
    event_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g. STAGE_STARTED, RUN_PAUSED
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
