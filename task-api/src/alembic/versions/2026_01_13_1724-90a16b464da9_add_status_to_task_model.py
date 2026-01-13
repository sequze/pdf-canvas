"""Add status to task model

Revision ID: 90a16b464da9
Revises: 4b8d1cd60fe4
Create Date: 2026-01-13 17:24:08.268058

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90a16b464da9"
down_revision: Union[str, Sequence[str], None] = "4b8d1cd60fe4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type
    taskfinishedstatus = sa.Enum("FAILED", "READY", name="taskfinishedstatus")
    taskfinishedstatus.create(op.get_bind())

    op.add_column(
        "tasks",
        sa.Column(
            "status",
            sa.Enum("FAILED", "READY", name="taskfinishedstatus"),
            nullable=False,
        ),
    )
    op.add_column("tasks", sa.Column("error", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "error")
    op.drop_column("tasks", "status")

    # Drop enum type
    taskfinishedstatus = sa.Enum("FAILED", "READY", name="taskfinishedstatus")
    taskfinishedstatus.drop(op.get_bind())
