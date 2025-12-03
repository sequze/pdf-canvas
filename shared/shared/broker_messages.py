from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class TaskMessage(BaseModel):
    id: str


class StatusEnum(str, Enum):
    PROCESSING = "processing"
    FAILED = "failed"
    READY = "ready"


class TaskSchema(BaseModel):
    id: UUID
    status: StatusEnum
    pdf_url: str | None = None


class JobStage(str, Enum):
    INPUT = "input"
    MARKDOWN = "markdown"
    PDF = "pdf"
    ERROR = "error"


class Job(BaseModel):
    id: UUID
    stage: JobStage
    input_text: str
    markdown: str
    result_pdf_url: str
    error: str
