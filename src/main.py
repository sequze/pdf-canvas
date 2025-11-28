from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.core.config import settings
from src.core.db import db_helper
from src.routers import router

app = FastAPI(
    title=settings.docs.title,
    version=settings.docs.version,
)
# app.middleware("http")(request_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shotdown
    await db_helper.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    """Run the API using Uvicorn"""
    uvicorn.run(
        "src.main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
