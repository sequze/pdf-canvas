import json
import logging
import pathlib
from typing import TYPE_CHECKING, Optional

from shared import (
    AbstractRabbitConsumer,
    TaskMessage,
    TasksRedisClient,
    JobsRedisClient,
    StatusEnum,
    JobStage,
)
from src.s3.utils import FileUploadService

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage

from src.convert import PdfConverter

logger = logging.getLogger(__name__)


class RabbitWorker(AbstractRabbitConsumer):

    def __init__(
        self,
        tasks_redis_cli: TasksRedisClient,
        job_redis_cli: JobsRedisClient,
        md_worker: PdfConverter,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        max_retries: int = 3,
        dlx: str | None = None,
        last_resort_queue: str | None = None,
    ):
        super().__init__(host, port, login, password, max_retries, dlx, last_resort_queue)
        self.tasks_redis_cli = tasks_redis_cli
        self.job_redis_cli = job_redis_cli
        self.md_worker = md_worker

    async def process_message(self, message: "AbstractIncomingMessage"):
        try:
            # deserialize message
            task_msg = TaskMessage.model_validate(
                json.loads(message.body.decode(encoding="utf-8"))
            )

            # get data from redis
            job = await self.job_redis_cli.get_job(task_msg.id)
            task = await self.tasks_redis_cli.get_task(task_msg.id)

            # Ignore request if data in Redis not exists
            if not (task and job):
                logger.warning(
                    f"Task #{task_msg.id} has no Job or Task in Redis. Skipping."
                )
                return
            logger.debug(f"Received task #{task.id}")

            # convert file and save
            pdf_bytes = await self.md_worker.convert_file_to_pdf(job.markdown)
            # upload file to S3
            link = await FileUploadService.upload_file(pdf_bytes, str(task_msg.id))
            # update task and job status
            task.pdf_url = link
            task.status = StatusEnum.READY
            job.result_pdf_url = task.pdf_url
            await self.tasks_redis_cli.create_task(task)
            await self.job_redis_cli.put_job(job)
            logger.debug(f"Processed task: Task #{task.id}")
            await message.ack()
            # TODO: send message
        except Exception as e:
            await message.nack(requeue=False)
            logger.exception(f"Error processing message")
