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
    async def publish_message(self, routing_key: str, exchange: str, message: bytes):
        exchange = await self._channel.get_exchange(exchange)
        logger.debug(f"Sending message {message} to #{routing_key} queue")
        await exchange.publish(aio_pika.Message(message), routing_key=routing_key)


class AbstractRabbitConsumer(RabbitHelper, ABC):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        max_retries: int = 3,
        dlx: str | None = None,
        last_resort_queue: str | None = None,
    ):
        super().__init__(host, port, login, password)
        self.max_retries = max_retries
        self.dlx = dlx
        self.last_resort_queue = last_resort_queue

    @abstractmethod
    async def process_message(
        self,
        message: "AbstractIncomingMessage",
    ): ...

    @staticmethod
    def get_message_deaths_count(message: "AbstractIncomingMessage") -> int:
        x_death_headers = message.headers.get("x-death")
        if x_death_headers:
            for props in x_death_headers:
                if isinstance(props, dict) and "count" in props:
                    return int(props["count"])
        return 0

    async def check_and_process_message(
        self,
        message: "AbstractIncomingMessage",
    ):
        deaths_count = self.get_message_deaths_count(message)
        # If deaths_count exceeds max_retries, send message to last resort queue
        if deaths_count > self.max_retries:
            logger.info(
                f"[-] Message failed after {self.max_retries} retries."
                f" Sending message to last resort queue."
            )
            if self.dlx and self.last_resort_queue:
                dlx = await self.channel.get_exchange(self.dlx)
                await dlx.publish(message, routing_key=self.last_resort_queue)
            await message.ack()
            return None
        return await self.process_message(message)

    async def start_consuming(self, queue_name: str):
        await self.channel.set_qos(prefetch_count=1)
        queue = await self.channel.get_queue(queue_name)

        # Start listening the queue
        await queue.consume(self.check_and_process_message)

        await asyncio.Future()


class AbstractRabbitWorker(AbstractRabbitConsumer, RabbitPublisher, ABC):
    """
    Consumer class that can send messages to queues
    """

    pass
