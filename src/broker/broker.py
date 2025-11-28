import pika
from src.core.config import settings


def get_connection() -> pika.BlockingConnection:
    return pika.BlockingConnection(parameters=settings.rmq.connection_params)
