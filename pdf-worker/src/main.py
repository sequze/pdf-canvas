import asyncio
from redis.asyncio import Redis
from shared import configure_logging, JobsRedisClient, TasksRedisClient
from src.config import settings

from src.convert import PdfConverter
from .broker import RabbitWorker

if __name__ == "__main__":
    configure_logging()

    async def main():
        # Create redis instance
        redis = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            decode_responses=True,
        )

        # Create redis clients
        jobs_redis_cli = JobsRedisClient(settings.redis, redis)
        tasks_redis_cli = TasksRedisClient(settings.redis, redis)

        # Create PDF worker and rabbit worker
        pdf_worker = PdfConverter()
        async with RabbitWorker(
            tasks_redis_cli,
            jobs_redis_cli,
            pdf_worker,
            host=settings.rmq.host,
            port=settings.rmq.port,
            login=settings.rmq.user,
            password=settings.rmq.password,
        ) as rabbit:
            # Start consuming messages
            await rabbit.start_consuming(settings.rmq.consumer_queue)

    asyncio.run(main())
