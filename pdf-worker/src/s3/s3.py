import logging
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from src.config import settings
from shared import AwsError

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
        domain: str,
        folder: str | None = None,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
        }

        self.bucket_name = bucket_name
        self.session = get_session()
        self.folder = folder
        self.domain = domain

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(self, data: bytes, filename: str, ttl: int) -> str:
        file_path = f"{self.folder}/{filename}" if self.folder else filename
        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name, Key=file_path, Body=data
                )
                return f"{self.domain}/{file_path}"
        except ClientError as e:
            raise AwsError("Upload file error") from e

    async def delete_file(self, filename: str) -> None:
        file_path = f"{self.folder}/{filename}" if self.folder else filename
        try:
            async with self.get_client() as client:
                await client.delete_object(Bucket=self.bucket_name, Key=file_path)
        except ClientError as e:
            logger.error(f"Error deleting file {file_path}", exc_info=e)
            raise AwsError("Delete file error") from e


s3 = S3Client(
    access_key=settings.aws.access_key,
    secret_key=settings.aws.secret_key,
    endpoint_url=settings.aws.endpoint_url,
    bucket_name=settings.aws.bucket_name,
    domain=settings.aws.domain,
    folder=settings.aws.folder,
)