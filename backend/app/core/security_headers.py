from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that injects standard security hardening headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        if getattr(settings, "SECURITY_HEADERS_ENABLED", True):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

            # If running in production or HSTS explicitly enabled, add Strict-Transport-Security
            if (settings.is_production or settings.HSTS_ENABLED) and (request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"):
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response

