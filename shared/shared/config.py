import logging

import pika
from pydantic import BaseModel


def configure_logging(level: int = logging.DEBUG):
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(funcName)20s %(module)s:%(lineno)d %(levelname)-8s - %(message)s",
    )
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)



class TopologyConfig(BaseModel):
    """RabbitMQ topology configuration"""

    main_exchange: str
    main_queue: str
    dlx_name: str
    dlq_name: str
    dlq_timeout: int
    last_resort_queue: str

    @classmethod
    def from_queue_name(
        cls,
        queue_name: str,
        exchange_name: str,
        dlx_name: str,
        dlq_timeout: int = 60000,  # 60 seconds
    ) -> "TopologyConfig":
        """
        Create topology config from queue name with automatic DLQ naming.

        Args:
            queue_name: Name of the main queue
            exchange_name: Name of the main exchange
            dlx_name: Name of the dead letter exchange
            dlq_timeout: Timeout in milliseconds before retry from DLQ

        Returns:
            TopologyConfig with auto-generated DLQ and last resort queue names
        """
        return cls(
            main_exchange=exchange_name,
            main_queue=queue_name,
            dlx_name=dlx_name,
            dlq_name=f"{queue_name}.dlq",
            dlq_timeout=dlq_timeout,
            last_resort_queue=f"{queue_name}.last_resort",
        )


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    tasks_ttl: int = 3600
    jobs_ttl: int = 900

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class BrokerConfig(BaseModel):
    port: int = 5672
    host: str = "localhost"
    user: str = "guest"
    password: str = "guest"
    exchange: str = ""
    consumer_queue: str
    producer_queue: str
    dlx: str

    @property
    def connection_params(self) -> pika.ConnectionParameters:
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=pika.PlainCredentials(self.user, self.password),
        )
