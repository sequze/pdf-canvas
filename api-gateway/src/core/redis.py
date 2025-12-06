from src.core.config import settings
from shared import RedisClient


redis_client = RedisClient(settings.redis)
