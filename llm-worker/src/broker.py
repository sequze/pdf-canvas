import json
import logging
from typing import TYPE_CHECKING

from shared import (
    AbstractRabbitWorker,
    TaskMessage,
    JobsRedisClient,
    JobStage,
)
from src.llm import LLMHelper

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class LLMRabbitWorker(AbstractRabbitWorker):

    def __init__(
        self,
        llm_worker: LLMHelper,
        jobs_redis_cli: JobsRedisClient,
        producer_queue: str,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
    ):
        super().__init__(host, port, login, password)
        self.producer_queue = producer_queue
        self.jobs_redis_cli = jobs_redis_cli
        self.llm = llm_worker

    async def process_message(self, message: "AbstractIncomingMessage"):
        # TODO: добавить DLQ
        async with message.process():
            try:
                # Deserialize message
                task = TaskMessage.model_validate(json.loads(message.body.decode()))

                # Get data from Redis
                job = await self.jobs_redis_cli.get_job(task.id)
                job.stage = JobStage.MARKDOWN
                logger.debug(
                    f"Received task: Task #{id}. Processing text: {job.input_text[:50]}..."
                )

                # Make request to LLM
                # TODO: move to a separate function
                #  and raise 503 error if empty response
                res = await self.llm.make_request(job.input_text)
                md_text = res.output[0].content[0].text

                if md_text:
                    # Save result to Redis and send to next worker
                    job.markdown = md_text
                    await self.jobs_redis_cli.put_job(job)
                    await self.publish_message(
                        routing_key=self.producer_queue,
                        message=json.dumps(task.model_dump()).encode(),
                    )
                    logger.debug(
                        f"Processed task: Task #{id}. Sent message to PDF-Worker."
                    )
            except Exception as e:
                logger.error(f"Failed to process task: {e}", exc_info=True)
                try:
                    job.markdown = ""
                    job.error = str(e)
                    await self.jobs_redis_cli.put_job(job)
                except Exception:
                    logger.exception("Failed to persist error state")
