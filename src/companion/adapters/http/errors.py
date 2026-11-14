from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from companion.core.errors import (
    ConflictError,
    CoreError,
    InvalidError,
    NotAllowedError,
    NotFoundError,
    OutsideServiceError,
)

type CoreErrorHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

STATUS_BY_ERROR_KIND: dict[type[CoreError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    NotAllowedError: status.HTTP_403_FORBIDDEN,
    InvalidError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ConflictError: status.HTTP_409_CONFLICT,
    OutsideServiceError: status.HTTP_502_BAD_GATEWAY,
}


def add_core_error_handlers(app: FastAPI) -> None:
    """Answer every core error with the status code of its kind.

    The body is `{"detail": <message>}`, the same shape as FastAPI's own
    errors, so routes never catch core errors themselves.

    Args:
        app: The app to add the handlers to.
    """
    for error_kind, status_code in STATUS_BY_ERROR_KIND.items():
        app.add_exception_handler(error_kind, core_error_handler(status_code))


def core_error_handler(status_code: int) -> CoreErrorHandler:
    """Build a handler that answers a core error with one status code.

    Args:
        status_code: The HTTP status code to answer with.

    Returns:
        The handler.
    """

    async def handle(request: Request, error: Exception) -> JSONResponse:
        """Answer a core error with its message.

        Args:
            request: The request that raised it.
            error: The core error.

        Returns:
            The error response.
        """
        message = error.message() if isinstance(error, CoreError) else str(error)
        return JSONResponse(status_code=status_code, content={"detail": message})

    return handle
