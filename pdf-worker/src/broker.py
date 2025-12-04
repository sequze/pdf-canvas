import json
import logging
import pathlib
from typing import TYPE_CHECKING

from shared import (
    AbstractRabbitConsumer,
    TaskMessage,
    TasksRedisClient,
    JobsRedisClient,
    StatusEnum,
    JobStage,
)

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
    ):
        super().__init__(host, port, login, password)
        self.tasks_redis_cli = tasks_redis_cli
        self.job_redis_cli = job_redis_cli
        self.md_worker = md_worker

    async def process_message(self, message: "AbstractIncomingMessage"):
        async with message.process():
            try:
                # deserialize message
                task_msg = TaskMessage.model_validate(
                    json.loads(message.body.decode(encoding="utf-8"))
                )

                # get data from redis
                job = await self.job_redis_cli.get_job(task_msg.id)
                task = await self.tasks_redis_cli.get_task(task_msg.id)

                logger.debug(f"Received task #{task.id}")

                # TODO: add S3 upload
                # convert file and save
                path = (
                    pathlib.Path(__file__).parent.parent.parent
                    / f"tmp/pdf_{task.id}.pdf"
                )
                await self.md_worker.convert_file_to_pdf(job.markdown, str(path))

                # update task and job status
                task.pdf_url = str(path)
                task.status = StatusEnum.READY
                job.result_pdf_url = task.pdf_url
                await self.tasks_redis_cli.create_task(task)
                await self.job_redis_cli.put_job(job)
                logger.debug(f"Processed task: Task #{task.id}")
            except Exception as e:
                logger.exception(f"Error processing message")

                # update job and task status
                job.error = str(e)
                job.stage = JobStage.ERROR
                task.status = StatusEnum.FAILED
                # TODO: message to DLQ
                try:
                    job.error = str(e)
                    job.stage = JobStage.ERROR
                    task.status = StatusEnum.FAILED

                    await self.job_redis_cli.put_job(job)
                    await self.tasks_redis_cli.create_task(task)

                except Exception:
                    logger.exception("Failed to persist error state")
