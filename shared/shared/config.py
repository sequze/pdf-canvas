import logging

import pika
from pydantic import BaseModel


def configure_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(funcName)20s %(module)s:%(lineno)d %(levelname)-8s - %(message)s",
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

    @property
    def connection_params(self) -> pika.ConnectionParameters:
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=pika.PlainCredentials(self.user, self.password),
        )
