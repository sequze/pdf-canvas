from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from src.core.broker import rabbit
from src.core.config import settings
from src.core.db import db_helper
from src.core.redis import redis_client
from src.middlewares import request_handler
from src.routers import router
from src.core.limiter import limiter
from shared import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rabbit:
        # startup
        yield
        # shutdown
        await db_helper.dispose()
        await redis_client.close()


app = FastAPI(
    title=settings.docs.title,
    version=settings.docs.version,
    lifespan=lifespan,
)
app.middleware("http")(request_handler)

app.include_router(router)
app.state.limiter = limiter


if __name__ == "__main__":
    configure_logging()
    """Run the API using Uvicorn"""
    uvicorn.run(
        "src.main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
