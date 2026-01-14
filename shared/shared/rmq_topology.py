import logging
import aio_pika
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractExchange
from pydantic import BaseModel

if TYPE_CHECKING:
    from .config import TopologyConfig

logger = logging.getLogger(__name__)


@dataclass
class QueueConfig:
    """Queue configuration"""

    name: str
    durable: bool = True
    arguments: dict | None = None


@dataclass
class ExchangeConfig:
    """Exchange configuration"""

    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True


@dataclass
class BindingConfig:
    """Configuration for binding a queue to an exchange"""

    queue_name: str
    exchange_name: str
    routing_key: str


class RabbitConfigurer:
    """
    Manager for queue topology with DLQ pattern support.
    """

    def __init__(
        self,
        channel: AbstractRobustChannel,
        config: "TopologyConfig",
    ):
        self._channel = channel
        self._config = config

        # Exchanges configuration
        self.main_exchange_config = ExchangeConfig(
            name=config.main_exchange,
            type=ExchangeType.DIRECT,
            durable=True,
        )
        self.dlx_config = ExchangeConfig(
            name=config.dlx_name,
            type=ExchangeType.DIRECT,
            durable=True,
        )

        # Queues configuration
        self.main_queue_config = QueueConfig(
            name=config.main_queue,
            durable=True,
            arguments={
                "x-dead-letter-exchange": config.dlx_name,
                "x-dead-letter-routing-key": config.dlq_name,
            },
        )

        self.dlq_config = QueueConfig(
            name=config.dlq_name,
            durable=True,
            arguments={
                "x-message-ttl": config.dlq_timeout,
                "x-dead-letter-exchange": config.main_exchange,
                "x-dead-letter-routing-key": config.main_queue,
            },
        )

        self.last_resort_queue_config = QueueConfig(
            name=config.last_resort_queue,
            durable=True,
        )

        # Bindings configuration
        self.bindings = [
            BindingConfig(config.main_queue, config.main_exchange, config.main_queue),
            BindingConfig(config.dlq_name, config.dlx_name, config.dlq_name),
            BindingConfig(
                config.last_resort_queue, config.dlx_name, config.last_resort_queue
            ),
        ]

        # Cache of declared exchanges
        self._exchanges: dict[str, AbstractExchange] = {}

    async def _declare_exchange(self, config: ExchangeConfig) -> AbstractExchange:
        """Declare an exchange according to configuration"""
        exchange = await self._channel.declare_exchange(
            config.name,
            type=config.type,
            durable=config.durable,
            passive=False,  # Create if doesn't exist
        )
        self._exchanges[config.name] = exchange
        logger.debug(f"Declared exchange: {config.name} (type={config.type.value})")
        return exchange

    async def _declare_queue(self, config: QueueConfig):
        """Declare a queue according to configuration"""
        queue = await self._channel.declare_queue(
            config.name,
            durable=config.durable,
            arguments=config.arguments or {},
            passive=False,  # Create if doesn't exist
        )
        logger.debug(f"Declared queue: {config.name} (args={config.arguments})")
        return queue

    async def _bind_queue(self, binding: BindingConfig):
        """Bind a queue to an exchange"""
        queue = await self._channel.get_queue(binding.queue_name)
        exchange = self._exchanges[binding.exchange_name]
        await queue.bind(exchange, routing_key=binding.routing_key)
        logger.debug(
            f"Bound queue '{binding.queue_name}' to exchange '{binding.exchange_name}' "
            f"with routing key '{binding.routing_key}'"
        )

    async def setup(self):
        """
        Create the full queue topology.

        Order matters:
        1. First exchanges
        2. Then queues
        3. Finally bindings
        """
        logger.info("Setting up queue topology...")

        # Step 1: Declare exchanges
        await self._declare_exchange(self.main_exchange_config)
        await self._declare_exchange(self.dlx_config)

        # Step 2: Declare queues
        await self._declare_queue(self.main_queue_config)
        await self._declare_queue(self.dlq_config)
        await self._declare_queue(self.last_resort_queue_config)

        # Step 3: Create bindings
        for binding in self.bindings:
            await self._bind_queue(binding)

        logger.info("Queue topology setup completed successfully")

    async def verify(self) -> bool:
        """
        Verify that topology exists without modifying it.

        Returns:
            True if all components exist, False otherwise
        """
        try:
            # Check exchanges (passive=True means check only, don't create)
            await self._channel.declare_exchange(
                self.main_exchange_config.name,
                passive=True,
            )
            await self._channel.declare_exchange(
                self.dlx_config.name,
                passive=True,
            )

            # Check queues
            await self._channel.declare_queue(
                self.main_queue_config.name,
                passive=True,
            )
            await self._channel.declare_queue(
                self.dlq_config.name,
                passive=True,
            )
            await self._channel.declare_queue(
                self.last_resort_queue_config.name,
                passive=True,
            )

            logger.info("Topology verification successful")
            return True
        except Exception as e:
            logger.warning(f"Topology verification failed: {e}")
            return False

    def get_exchange(self, name: str) -> AbstractExchange:
        """Get exchange object by name"""
        if name not in self._exchanges:
            raise ValueError(f"Exchange '{name}' not found. Did you call setup()?")
        return self._exchanges[name]

    @property
    def main_exchange(self) -> AbstractExchange:
        """Main exchange for publishing messages"""
        return self.get_exchange(self.main_exchange_config.name)


async def setup_rabbitmq_topology(
    config: "TopologyConfig",
    host: str = "localhost",
    port: int = 5672,
    login: str = "guest",
    password: str = "guest",
) -> None:
    """
    Configure RabbitMQ topology once at application startup.

    Args:
        config: TopologyConfig instance with all topology parameters
        host: RabbitMQ host
        port: RabbitMQ port
        login: Connection login
        password: Connection password
    """

    logger.info("Setting up RabbitMQ topology...")

    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
        login=login,
        password=password,
    )

    try:
        channel = await connection.channel()

        topology_manager = RabbitConfigurer(
            channel=channel,
            config=config,
        )

        await topology_manager.setup()

        logger.info("RabbitMQ topology setup completed successfully")
    finally:
        await connection.close()
