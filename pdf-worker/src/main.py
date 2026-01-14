import asyncio
from redis.asyncio import Redis
from shared import (
    configure_logging,
    JobsRedisClient,
    TasksRedisClient,
    TopologyConfig,
    setup_rabbitmq_topology,
)
from src.config import settings

from src.convert import PdfConverter
from .broker import RabbitWorker

if __name__ == "__main__":
    configure_logging()

    async def main():
        # Create topology config for PDF worker
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
            max_retries=3,
            dlx=settings.rmq.dlx,
            last_resort_queue=topology_config.last_resort_queue,
        ) as rabbit:
            # Start consuming messages
            await rabbit.start_consuming(settings.rmq.consumer_queue)

    asyncio.run(main())
