"""add_world_state_to_workflow_runs

Revision ID: e215f2392e67
Revises: abcdef123456
Create Date: 2026-09-22 12:19:34.120052

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e215f2392e67'
down_revision: str | Sequence[str] | None = 'abcdef123456'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workflow_runs', sa.Column('world_state', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('workflow_runs', 'world_state')
