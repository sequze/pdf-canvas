from fastapi import Request, Response, HTTPException

from src.core.exceptions import (
    AppError,
    NotFoundError,
    ConflictError,
    ForbiddenError,
    AuthError,
    EntityTooLargeError,
)
from src.core.logger import logger
from .core.utils import get_time, get_uuid
from fastapi.responses import JSONResponse


async def request_handler(request: Request, call_next):
    """Middleware used by FastAPI to process each request, featuring:

    - Contextualize request logs with an unique Request ID (UUID4) for each unique request.
    - Catch exceptions during the request handling. Translate custom API exceptions into responses,
      or treat (and log) unexpected exceptions.
    """
    start_time = get_time(seconds_precision=False)
    request_id = get_uuid()

    with logger.contextualize(request_id=request_id):
        logger.bind(url=str(request.url), method=request.method).debug(
            "Request started"
        )

        try:
            response: Response = await call_next(request)

        except AppError as exc:
            response = ErrorProcessor.process_app_exception(exc)

        except HTTPException as exc:
            response = ErrorProcessor.process_http_exception(exc)

        except Exception:
            logger.opt(exception=True).error("Request failed due to unexpected error")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )

        end_time = get_time(seconds_precision=False)
        time_elapsed = round(end_time - start_time, 5)
        logger.bind(
            time_elapsed=time_elapsed, response_status=response.status_code
        ).debug("Request ended")
        return response


class ErrorProcessor:
    @classmethod
    def log_exception(cls, exc: Exception, status_code: int) -> None:
        if status_code < 500:
            logger.bind(exception=str(exc)).info(
                "Request did not succeed due to client-side error"
            )
        else:
            logger.opt(exception=True).warning(
                "Request did not succeed due to server-side error"
            )

    @classmethod
    def process_app_exception(cls, exc: AppError) -> JSONResponse:
        if isinstance(exc, ForbiddenError):
            status_code = 403
        elif isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, ConflictError):
            status_code = 409
        elif isinstance(exc, AuthError):
            status_code = 401
        elif isinstance(exc, EntityTooLargeError):
            status_code = 413
        else:
            status_code = 400

        cls.log_exception(exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.detail},
        )

    @classmethod
    def process_http_exception(cls, exc: HTTPException) -> JSONResponse:
        status_code = exc.status_code
        detail = exc.detail
        cls.log_exception(exc, status_code)
        return JSONResponse(status_code=status_code, content={"detail": detail})
