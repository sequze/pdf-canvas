import asyncio
from src.config import settings
from src.llm import LLMHelper, PromptHelper
from shared import configure_logging, JobsRedisClient
from .broker import LLMRabbitWorker


async def main():
    configure_logging()
    llm = LLMHelper(
        api_key=settings.llm.yandex_cloud_api_key,
        base_url=settings.llm.base_url,
        folder=settings.llm.yandex_cloud_folder,
        model=settings.llm.model,
        instruction=PromptHelper.get_main_prompt(),
        temperature=settings.llm.temperature,
    )
    redis = JobsRedisClient(settings.redis)
    async with LLMRabbitWorker(
        llm_worker=llm,
        jobs_redis_cli=redis,
        producer_queue=settings.rmq.producer_queue,
        host=settings.rmq.host,
        port=settings.rmq.port,
        login=settings.rmq.user,
        password=settings.rmq.password,
    ) as broker:
        await broker.start_consuming(settings.rmq.consumer_queue)


if __name__ == "__main__":
    asyncio.run(main())
