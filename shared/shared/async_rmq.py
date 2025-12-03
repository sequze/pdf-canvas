import asyncio
import logging
import aio_pika

from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from .exceptions import RabbitError

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage, AbstractRobustChannel


logger = logging.getLogger(__name__)


class RabbitHelper:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
    ) -> None:
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self._channel: "AbstractRobustChannel" = None

    async def __aenter__(
        self,
    ):
        self._connection = await aio_pika.connect_robust(
            host=self.host,
            port=self.port,
            login=self.login,
            password=self.password,
        )
        self._channel = await self._connection.channel()
        return self

    @property
    def channel(self):
        if self._channel is None:
            raise RabbitError("Please call RabbitHelper from context manager")
        return self._channel

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if not self._connection.is_closed:
            await self._connection.close()


class RabbitPublisher(RabbitHelper):

    async def publish_message(self, routing_key: str, message: bytes):
        await self.channel.declare_queue(routing_key, durable=True)

        logger.debug(f"Sending message {message} to #{routing_key} queue")
        await self.channel.default_exchange.publish(
            aio_pika.Message(message), routing_key=routing_key
        )


class AbstractRabbitConsumer(RabbitHelper, ABC):

    @abstractmethod
    async def process_message(
        self,
        message: "AbstractIncomingMessage",
    ): ...

    async def start_consuming(self, queue_name: str):
        await self.channel.set_qos(prefetch_count=1)

        # Declaring queue
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
        )

        # Start listening the queue
        await queue.consume(self.process_message)

        await asyncio.Future()


class AbstractRabbitWorker(AbstractRabbitConsumer, RabbitPublisher, ABC):
    """
    Consumer class that can send messages to queues
    """

    pass
