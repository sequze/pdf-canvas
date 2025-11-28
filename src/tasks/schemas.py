from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class StatusEnum(str, Enum):
    PROCESSING = "processing"
    FAILED = "failed"
    READY = "ready"


class TaskSchema(BaseModel):
    id: UUID
    status: StatusEnum
    pdf_url: str | None = None
