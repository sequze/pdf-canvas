import json
import logging
from typing import TYPE_CHECKING, Optional

from sqlalchemy.exc import IntegrityError

from shared import (
    AbstractRabbitConsumer,
    TaskMessage,
    TasksRedisClient,
    configure_logging,
    UnitOfWork,
    TaskSchema,
    StatusEnum,
    TopologyConfig,
    setup_rabbitmq_topology,
)
from src.tasks.repository import TasksSQLAlchemyRepository

from src.core.models.tasks import TaskFinishedStatus

from src.core.db import db_helper

from src.core.config import settings

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage


logger = logging.getLogger(__name__)


class TaskFinishedConsumer(AbstractRabbitConsumer):
    def __init__(
        self,
        tasks_redis_cli: TasksRedisClient,
        uow: UnitOfWork,
        repository: TasksSQLAlchemyRepository,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
    ):
        super().__init__(host, port, login, password)
        self.tasks_redis_cli = tasks_redis_cli
        self.uow = uow
        self.repository = repository

    async def process_message(self, message: "AbstractIncomingMessage"):
        try:
            # deserialize message
            task_msg = TaskMessage.model_validate(
                json.loads(message.body.decode(encoding="utf-8"))
            )

            # get data from redis
            task = await self.tasks_redis_cli.get_task(task_msg.id)

            # Ignore request if data in Redis not exists
            if not task:
                logger.warning(f"Task #{task_msg.id} has no Task in Redis. Skipping.")
                return
            logger.debug(f"Received task #{task.id}")
            await self._process_task_finished(task)
            logger.debug(f"Processed task: Task #{task.id}")
            await message.ack()
        except Exception as e:
            await message.nack(requeue=False)
            logger.exception(f"Error processing message")

    def _prepare_data_to_create(self, result: TaskSchema):
        data = {
            "id": result.id,
            "user_id": result.user_id,
            "pdf_url": result.pdf_url,
        }
        if result.status == StatusEnum.FAILED:
            data.update(status=TaskFinishedStatus.FAILED, error=result.error)
        return data

    async def _process_task_finished(self, result: TaskSchema):
        async with self.uow as uow:
            try:
                await self.repository.save(uow.session, self._prepare_data_to_create(result))
                await uow.commit()
            except IntegrityError as e:
                # Task already processed
                logger.warning(f"Task with id {result.id} already exists in db: {e}")


async def main():
    """Main function to start the task finished consumer"""
    configure_logging()

    # Create topology config for API consumer (if needed)
    topology_config = TopologyConfig.from_queue_name(
        queue_name=settings.rmq.consumer_queue,
        exchange_name=settings.rmq.exchange,
        dlx_name=settings.rmq.dlx,
    )
    await setup_rabbitmq_topology(
        topology_config,
        host=settings.rmq.host,
        port=settings.rmq.port,
        login=settings.rmq.user,
        password=settings.rmq.password,
    )

    uow = UnitOfWork(db_helper.session_factory)
    repository = TasksSQLAlchemyRepository()
    redis_client = TasksRedisClient(settings.redis)

    async with TaskFinishedConsumer(
        tasks_redis_cli=redis_client,
        uow=uow,
        repository=repository,
        host=settings.rmq.host,
        port=settings.rmq.port,
        login=settings.rmq.user,
        password=settings.rmq.password,
    ) as consumer:
        logger.info(f"Starting consumer for queue: {settings.rmq.consumer_queue}")
        await consumer.start_consuming(settings.rmq.consumer_queue)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
