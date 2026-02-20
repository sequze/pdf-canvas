import asyncio
from prometheus_client import start_http_server, Gauge, Counter, Histogram

from src.config import settings


class PrometheusClient:

    def __init__(self, port: int = 8000):
        self.port = port
        self.pdf_heartbeat = None
        self.pdf_tasks_in_progress = None
        self.pdf_tasks_processed = None
        self.pdf_tasks_failed = None
        self.pdf_task_duration = None

    async def heartbeat_task(self):
        while True:
            self.pdf_heartbeat.set(1)
            await asyncio.sleep(5)

    def start(self):
        start_http_server(self.port)

        self.pdf_heartbeat = Gauge(
            "pdf_worker_heartbeat",
            "pdf worker heartbeat metric",
        )

        self.pdf_tasks_in_progress = Gauge(
            "pdf_tasks_in_progress", "Tasks currently being processed"
        )

        self.pdf_tasks_processed = Counter(
            "pdf_tasks_processed_total", "Total processed pdf tasks"
        )

        self.pdf_tasks_failed = Counter(
            "pdf_tasks_failed_total", "Total failed pdf tasks"
        )
        self.pdf_task_duration = Histogram(
            "pdf_task_duration_total",
            "Task duration in seconds",
            buckets=(0.5, 1, 2, 5, 10, 30, 60),
            labelnames=("result",)
        )
        asyncio.create_task(self.heartbeat_task())

prometheus_client = PrometheusClient(settings.prometheus.port)