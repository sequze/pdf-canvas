import logging
import time
from typing import TYPE_CHECKING

from src.core.config import configure_logging, settings
from .broker import get_connection

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel

logger = logging.getLogger(__name__)


def declare_queue(ch: "BlockingChannel"):
    return ch.queue_declare(queue=settings.rmq.routing_key)


def publish_message(channel: "BlockingChannel", idx: int) -> None:
    declare_queue(channel)
    message = f"Message #{idx:02d}"
    channel.basic_publish(
        exchange=settings.rmq.exchange,
        routing_key=settings.rmq.routing_key,
        body=message,
    )
    time.sleep(0.5)
    logger.info("Sent message %r to broker.", message)


if __name__ == "__main__":
    configure_logging()
    with get_connection() as connection:
        with connection.channel() as channel:
            for idx in range(1, 11):
                publish_message(channel, idx)
