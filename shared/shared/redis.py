from typing import TYPE_CHECKING
from uuid import UUID
from .broker_messages import Job, TaskSchema
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .config import RedisConfig


class RedisClient:
    def __init__(
        self,
        redis_config: "RedisConfig",
        redis: Redis | None = None,
    ):
        self.client = (
            redis
            if redis
            else Redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.db,
                decode_responses=True,
            )
        )
        self.config = redis_config

    def get_connection(self) -> Redis:
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()


class JobsRedisClient(RedisClient):
    async def put_job(self, job: Job):
        name = f"job:{job.id}"
        await self.client.hset(
            name,
            mapping=job.model_dump(exclude={"id"}),
        )
        await self.client.expire(name, self.config.jobs_ttl)

    async def get_job(self, id: UUID) -> Job:
        name = f"job:{id}"
        data = await self.client.hgetall(name)
        return Job(id=id, **data)

    async def delete_job(self, task_id: UUID):
        await self.client.delete(f"job:{task_id}")


class TasksRedisClient(RedisClient):
    async def create_task(self, task: TaskSchema):
        return await self._create_task(task.id, task.model_dump(exclude={"id"}))

    async def _create_task(self, task_id: UUID, payload: dict):
        name = f"task:{task_id}"
        await self.client.hset(
            name,
            mapping=payload,
        )
        await self.client.expire(name, self.config.tasks_ttl)

    async def update_task_status(self, task_id: UUID, status: str):
        await self.client.hset(f"task:{task_id}", "status", status)

    async def get_task(self, task_id: UUID) -> TaskSchema | None:
        payload = await self.client.hgetall(f"task:{task_id}")
        if not payload:
            return None
        return TaskSchema(**payload, id=task_id)

    async def delete_task(self, task_id: UUID):
        await self.client.delete(f"task:{task_id}")
