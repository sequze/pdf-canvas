from shared import RabbitPublisher
from src.core.config import settings

rabbit = RabbitPublisher(
    host=settings.rmq.host,
    port=settings.rmq.port,
    login=settings.rmq.user,
    password=settings.rmq.password,
)
