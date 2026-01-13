"""add refresh session model

Revision ID: 4b8d1cd60fe4
Revises: f1f7b83e4546
Create Date: 2025-12-07 15:35:02.070716

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b8d1cd60fe4"
down_revision: Union[str, Sequence[str], None] = "f1f7b83e4546"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_sessions",
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_sessions")),
        sa.UniqueConstraint(
            "refresh_token", name=op.f("uq_refresh_sessions_refresh_token")
        ),
    )
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_verified")
    op.drop_table("refresh_sessions")
