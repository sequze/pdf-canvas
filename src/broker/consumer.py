import logging
import time
from typing import TYPE_CHECKING


from src.core.config import configure_logging, settings
from .broker import get_connection

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic, BasicProperties


def process_new_message(
    ch: "BlockingChannel",
    method: "Basic.Deliver",
    properties: "BasicProperties",
    body: bytes,
):
    logging.info("New message received from broker: %r", body)
    is_odd = int(body[-2:]) % 2
    time.sleep(0.5 + 2 * is_odd)
    logging.info("Finished proccessing message.")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume_messages(channel: "BlockingChannel") -> None:
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=settings.rmq.routing_key,
        on_message_callback=process_new_message,
        # auto_ack=True,
    )
    channel.start_consuming()


if __name__ == "__main__":
    configure_logging()
    with get_connection() as connection:
        with connection.channel() as channel:
            consume_messages(channel)
