from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base
from src.core.models.mixins import UUIDPkMixin, TimestampMixin


class RefreshSession(UUIDPkMixin, TimestampMixin, Base):
    refresh_token: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
