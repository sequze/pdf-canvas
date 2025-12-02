import uuid
from datetime import datetime

from sqlalchemy import UUID, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7


class UUIDPkMixin:
    """Mixin to add id Primary key column (UUID)"""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )


class TimestampMixin:
    """Mixin to add timestamp column"""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(),
        nullable=True,
    )
