"""Initial schema with runtime, memory and pgvector

Revision ID: abcdef123456
Revises: 
Create Date: 2026-08-20 00:00:00.000000

"""
import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'abcdef123456'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Runtime Schema
    op.create_table(
        'workflow_definitions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workflow_versions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('workflow_id', sa.String(), sa.ForeignKey('workflow_definitions.id'), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('definition', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('workflow_version_id', sa.String(), sa.ForeignKey('workflow_versions.id'), nullable=False),
        sa.Column('parent_run_id', sa.String(), sa.ForeignKey('workflow_runs.id'), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )

    op.create_table(
        'stage_runs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('workflow_run_id', sa.String(), sa.ForeignKey('workflow_runs.id'), nullable=False),
        sa.Column('stage_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )

    op.create_table(
        'task_attempts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('stage_run_id', sa.String(), sa.ForeignKey('stage_runs.id'), nullable=False),
        sa.Column('idempotency_key', sa.String(), unique=True, nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )

    op.create_table(
        'checkpoints',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('workflow_run_id', sa.String(), sa.ForeignKey('workflow_runs.id'), nullable=False),
        sa.Column('stage_run_id', sa.String(), sa.ForeignKey('stage_runs.id'), nullable=False),
        sa.Column('world_state_snapshot_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'execution_events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('workflow_run_id', sa.String(), sa.ForeignKey('workflow_runs.id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False)
    )

    # 3. Memory Schema
    op.create_table(
        'episodic_memory',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('lifecycle', sa.String(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column('embedding_model', sa.String(), nullable=True),
        sa.Column('embedding_version', sa.String(), nullable=True),
        sa.Column('embedding_dimension', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('workflow_run_id', sa.String(), nullable=True),
        sa.Column('stage_run_id', sa.String(), nullable=True),
        sa.Column('world_state_id', sa.String(), nullable=True),
        sa.Column('source_entity_id', sa.String(), nullable=True),
        sa.Column('source_event_id', sa.String(), nullable=True),
        sa.Column('source_timestamp', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('entities', sa.JSON(), nullable=True)
    )

    op.create_table(
        'semantic_memory',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('lifecycle', sa.String(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column('embedding_model', sa.String(), nullable=True),
        sa.Column('embedding_version', sa.String(), nullable=True),
        sa.Column('embedding_dimension', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('workflow_run_id', sa.String(), nullable=True),
        sa.Column('stage_run_id', sa.String(), nullable=True),
        sa.Column('world_state_id', sa.String(), nullable=True),
        sa.Column('source_entity_id', sa.String(), nullable=True),
        sa.Column('source_event_id', sa.String(), nullable=True),
        sa.Column('source_timestamp', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('fact_type', sa.String(), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('semantic_memory')
    op.drop_table('episodic_memory')
    op.drop_table('execution_events')
    op.drop_table('checkpoints')
    op.drop_table('task_attempts')
    op.drop_table('stage_runs')
    op.drop_table('workflow_runs')
    op.drop_table('workflow_versions')
    op.drop_table('workflow_definitions')
    
    op.execute("DROP EXTENSION IF EXISTS vector;")
