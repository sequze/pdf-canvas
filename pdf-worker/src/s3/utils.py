from uuid import uuid4

from shared import AwsError
from .s3 import s3
from src.config import settings


class FileUploadService:
    """Сервис для загрузки изображений."""

    @staticmethod
    async def upload_file(file_data: bytes, task_id: str) -> str:
        filename = f"{task_id}.pdf"
        return await s3.upload_file(file_data, filename)

    @staticmethod
    async def delete_file(url: str) -> None:
        if not url:
            raise AwsError("Empty URL")
        if not url.startswith(settings.aws.domain):
            raise AwsError("Invalid URL")
        domain = settings.aws.domain.rstrip("/")
        prefix = domain + "/"
        filepath = url.removeprefix(prefix)
        await s3.delete_file(filepath)
