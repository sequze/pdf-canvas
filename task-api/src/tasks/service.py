import json
import logging
from uuid import UUID
from shared import UnitOfWork, Job, JobStage
from shared import TaskMessage, TaskSchema, StatusEnum
from src.core.exceptions import NotFoundError, ForbiddenError, EntityTooLargeError
from src.tasks.repository import TasksSQLAlchemyRepository
from shared import JobsRedisClient, TasksRedisClient
from uuid_extensions import uuid7
from src.core.broker import rabbit
from src.core.config import settings

logger = logging.getLogger(__name__)


class TasksService:
    def __init__(
        self,
        jobs_redis_cli: JobsRedisClient,
        tasks_redis_cli: TasksRedisClient,
        sqla_repository: TasksSQLAlchemyRepository,
        uow: UnitOfWork,
    ):
        self.tasks_redis_cli = tasks_redis_cli
        self.jobs_redis_cli = jobs_redis_cli
        self.sqla_repository = sqla_repository
        self.uow = uow

    async def create_task(self, data: str, user_id: UUID) -> TaskSchema:
        # Validate input data size
        if len(data.encode("utf-8")) > settings.tasks.max_input_size:
            raise EntityTooLargeError(
                f"Input data too large. Max size: {settings.tasks.max_input_size} bytes"
            )

        # Generate task id
        task_id = uuid7()
        task = TaskSchema(
            id=task_id,
            status=StatusEnum.PROCESSING,
            pdf_url="",
            user_id=user_id,
        )
        job = Job(
            id=task_id,
            stage=JobStage.INPUT,
            input_text=data,
            markdown="",
            result_pdf_url="",
            error="",
        )

        try:
            # put a task to redis
            await self.tasks_redis_cli.create_task(task)

            # create job record in redis
            await self.jobs_redis_cli.put_job(job)

            # create broker message
            msg = TaskMessage(id=str(task_id))

            # publish a message in broker
            logger.debug("Publishing message: %s", msg)
            await rabbit.publish_message(
                settings.rmq.producer_queue,
                settings.rmq.exchange,
                json.dumps(msg.model_dump()).encode(),
            )
            logger.debug(
                "Published message: %s. Exchange: %s, queue: %s",
                msg,
                settings.rmq.producer_queue,
                settings.rmq.exchange,
            )
        except Exception:
            # rollback in case of error
            await self.tasks_redis_cli.delete_task(task_id)
            await self.jobs_redis_cli.delete_job(task_id)
            raise
        return task

    async def _get_task_from_db(self, task_id: UUID) -> TaskSchema:
        async with self.uow as uow:
            task = await self.sqla_repository.get_by_id(uow.session, task_id)
            if not task:
                raise NotFoundError(f"Task with id {task_id} not found")

            return TaskSchema(
                status=StatusEnum.READY,
                id=task.id,
                pdf_url=task.pdf_url,
                user_id=task.user_id,
            )

    async def get_task(
        self, task_id: UUID, user_id: UUID, is_superuser: bool = False
    ) -> TaskSchema:
        # Try to find task in Redis
        task = await self.tasks_redis_cli.get_task(task_id)

        # If not found in Redis, try get from DB with ownership check
        if not task:
            task = await self._get_task_from_db(task_id)

        # Check access
        if not (is_superuser or task.user_id == user_id):
            raise ForbiddenError("Access denied to this task")
        return task

    async def get_user_tasks(self, user_id: UUID) -> list[TaskSchema]:
        """Get all user`s tasks from DB"""
        async with self.uow as uow:
            tasks = await self.sqla_repository.get_by_user_id(uow.session, user_id)
            return [
                TaskSchema(
                    id=task.id,
                    status=StatusEnum.READY,
                    pdf_url=task.pdf_url,
                    user_id=task.user_id,
                )
                for task in tasks
            ]

    async def delete_task(
        self, task_id: UUID, user_id: UUID, is_superuser: bool = False
    ) -> None:
        """Delete task from DB with ownership check"""
        async with self.uow as uow:
            task = await self.sqla_repository.get_by_id(uow.session, task_id)

            # Check access
            if not (is_superuser or task.user_id == user_id):
                raise ForbiddenError("Access denied to this task")

            await self.sqla_repository.delete(uow.session, task_id)
            await uow.commit()
