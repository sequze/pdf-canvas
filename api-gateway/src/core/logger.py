import sys

from loguru import logger

from src.core.config import settings

LoggerFormat = (
    "<green>{time:YY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level> | {extra}"
)

logger.remove()
logger.add(
    sys.stderr,
    level=settings.logging.level.upper(),
    format=LoggerFormat,
    serialize=settings.logging.serialize,
    enqueue=True,  # process logs in background
    diagnose=False,  # hide variable values in log backtrace
)
