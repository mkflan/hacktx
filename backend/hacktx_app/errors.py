"""One error envelope for every failure: {"error": {"code", "message", "retryable"}}."""

import logging

from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("hacktx_app")


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        *,
        retryable: bool = False,
        details: list | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable
        self.details = details


def not_found(kind: str, item_id: str) -> AppError:
    return AppError(f"{kind.upper()}_NOT_FOUND", f"No {kind} with id {item_id!r}.", 404)


def error_response(
    code: str, message: str, status: int, *, retryable: bool = False, details: list | None = None
):
    body: dict = {"error": {"code": code, "message": message, "retryable": retryable}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def validation_details(exc: ValidationError) -> list[dict]:
    """Pydantic errors without the rejected input values (they may be large or sensitive)."""
    return [
        {"loc": [str(p) for p in err["loc"]], "msg": err["msg"], "type": err["type"]}
        for err in exc.errors(include_url=False, include_input=False)
    ]


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _app_error(exc: AppError):
        return error_response(
            exc.code, exc.message, exc.status, retryable=exc.retryable, details=exc.details
        )

    @app.errorhandler(ValidationError)
    def _validation_error(exc: ValidationError):
        return error_response(
            "VALIDATION_ERROR", "Request failed validation.", 422, details=validation_details(exc)
        )

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        code = (exc.name or "HTTP_ERROR").upper().replace(" ", "_")
        return error_response(code, exc.description or exc.name, exc.code or 500)

    @app.errorhandler(Exception)
    def _unexpected(exc: Exception):
        logger.exception("Unhandled error")
        return error_response("INTERNAL_ERROR", "Unexpected server error.", 500, retryable=True)
