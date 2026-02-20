import asyncio
from prometheus_client import start_http_server, Gauge, Counter, Histogram

from src.config import settings


class PrometheusClient:

    def __init__(self, port: int = 8000):
        self.port = port
        self.llm_heartbeat = None
        self.llm_tasks_in_progress = None
        self.llm_tasks_processed = None
        self.llm_tasks_failed = None
        self.llm_task_duration = None

    async def heartbeat_task(self):
        while True:
            self.llm_heartbeat.set(1)
            await asyncio.sleep(5)

    def start(self):
        start_http_server(self.port)

        self.llm_heartbeat = Gauge(
            "llm_worker_heartbeat",
            "Llm worker heartbeat metric",
        )

        self.llm_tasks_in_progress = Gauge(
            "llm_tasks_in_progress", "Tasks currently being processed"
        )

        self.llm_tasks_processed = Counter(
            "llm_tasks_processed_total", "Total processed LLM tasks"
        )

        self.llm_tasks_failed = Counter(
            "llm_tasks_failed_total", "Total failed LLM tasks"
        )
        self.llm_task_duration = Histogram(
            "llm_task_duration_total",
            "Task duration in seconds",
            buckets=(0.5, 1, 2, 5, 10, 30, 60),
            labelnames=("result",)
        )
        asyncio.create_task(self.heartbeat_task())

prometheus_client = PrometheusClient(settings.prometheus.port)