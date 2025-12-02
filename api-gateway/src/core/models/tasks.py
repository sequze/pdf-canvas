import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from src.core.models.base import Base
from src.core.models.mixins import UUIDPkMixin, TimestampMixin

if TYPE_CHECKING:
    from src.core.models import User


class Task(UUIDPkMixin, TimestampMixin, Base):
    """Task model"""

    pdf_url: Mapped[str | None]
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(back_populates="tasks")
