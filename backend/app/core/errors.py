import logging
import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    content: Dict[str, Any] = {
        "detail": message,  # Backward compatibility for existing clients expecting {"detail": ...}
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        },
    }
    if details is not None:
        content["error"]["details"] = details

    resp_headers = {"X-Request-ID": request_id}
    if headers:
        resp_headers.update(headers)

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=resp_headers,
    )


def register_exception_handlers(app: FastAPI):
    """Registers global exception handlers for consistent API error contracts."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = get_request_id(request)
        code = f"HTTP_{exc.status_code}"
        msg = str(exc.detail) if exc.detail else "An HTTP error occurred."
        return create_error_response(
            status_code=exc.status_code,
            code=code,
            message=msg,
            request_id=req_id,
            headers=getattr(exc, "headers", None),
        )


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = get_request_id(request)
        # Simplify validation error details without leaking internal classes
        sanitized_errors = []
        for err in exc.errors():
            sanitized_errors.append({
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            })

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Data input request tidak valid.",
            request_id=req_id,
            details=sanitized_errors,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = get_request_id(request)
        # Log complete stack trace on server-side only
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path} (request_id={req_id}): {type(exc).__name__} - {str(exc)}",
            exc_info=True,
            extra={"request_id": req_id},
        )

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="Terjadi kesalahan internal pada server. Silakan hubungi administrator.",
            request_id=req_id,
        )
