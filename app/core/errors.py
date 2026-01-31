"""Error handling - unified error format per rules/api.mdc"""
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# =============================================================================
# Error Models (matching openapi.yaml ErrorResponse schema)
# =============================================================================


class ErrorDetail(BaseModel):
    """Individual error detail"""

    field: Optional[str] = None
    code: str
    message: str


class ErrorBody(BaseModel):
    """Error body structure"""

    code: str
    message: str
    details: List[ErrorDetail] = []


class ErrorResponse(BaseModel):
    """Unified error response format"""

    error: ErrorBody


# =============================================================================
# Error Codes (matching rules/api.mdc Section 3.2)
# =============================================================================


class ErrorCode:
    """Error code constants"""

    # 400
    VALIDATION_ERROR = "validation_error"
    INVALID_REQUEST = "invalid_request"
    IDEMPOTENCY_KEY_REQUIRED = "idempotency_key_required"
    CONFIRMATION_REQUIRED = "confirmation_required"

    # 401
    UNAUTHENTICATED = "unauthenticated"
    TOKEN_EXPIRED = "token_expired"
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"

    # 403
    FORBIDDEN = "forbidden"
    AGE_RESTRICTED = "age_restricted"
    ENTITLEMENT_REQUIRED = "entitlement_required"
    CONSENT_REQUIRED = "consent_required"
    ONBOARDING_REQUIRED = "onboarding_required"
    BLOCKED = "blocked"

    # 404
    NOT_FOUND = "not_found"

    # 408
    REQUEST_TIMEOUT = "request_timeout"

    # 409
    CONFLICT = "conflict"
    ALREADY_PURCHASED = "already_purchased"
    ALREADY_CONSENTED = "already_consented"
    ALREADY_VERIFIED = "already_verified"
    DUPLICATE_REPORT = "duplicate_report"
    REQUEST_IN_PROGRESS = "request_in_progress"
    JOB_IN_PROGRESS = "job_in_progress"

    # 422
    UNPROCESSABLE_ENTITY = "unprocessable_entity"

    # 423
    ACCOUNT_LOCKED = "account_locked"

    # 429
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # 500
    INTERNAL_ERROR = "internal_error"

    # 503
    SERVICE_UNAVAILABLE = "service_unavailable"


# =============================================================================
# Custom Exceptions
# =============================================================================


class APIException(HTTPException):
    """Base API exception with unified error format"""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(status_code=status_code, detail=message)


class ValidationException(APIException):
    """400 - Validation error"""

    def __init__(self, message: str = "リクエストの検証に失敗しました", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
        )


class UnauthenticatedException(APIException):
    """401 - Authentication required"""

    def __init__(self, message: str = "認証が必要です", code: str = ErrorCode.UNAUTHENTICATED):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=message,
        )


class ForbiddenException(APIException):
    """403 - Permission denied"""

    def __init__(self, message: str = "この操作を実行する権限がありません", code: str = ErrorCode.FORBIDDEN):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=code,
            message=message,
        )


class NotFoundException(APIException):
    """404 - Resource not found"""

    def __init__(self, message: str = "リソースが見つかりません"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message=message,
        )


class ConflictException(APIException):
    """409 - Conflict"""

    def __init__(self, message: str = "リソースが既に存在します", code: str = ErrorCode.CONFLICT):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            message=message,
        )


class RateLimitException(APIException):
    """429 - Rate limit exceeded"""

    def __init__(self, message: str = "リクエスト制限を超過しました。しばらく待ってから再試行してください。"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
        )


class ServiceUnavailableException(APIException):
    """503 - Service unavailable"""

    def __init__(self, message: str = "サービスが一時的に利用できません"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
        )


# =============================================================================
# Exception Handlers
# =============================================================================


def create_error_response(
    status_code: int, code: str, message: str, details: Optional[List[Dict[str, Any]]] = None
) -> JSONResponse:
    """Create unified error response"""
    error_details = []
    if details:
        for d in details:
            error_details.append(
                ErrorDetail(
                    field=d.get("field"),
                    code=d.get("code", "error"),
                    message=d.get("message", str(d)),
                )
            )

    response = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=error_details,
        )
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle APIException"""
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append(
            {
                "field": field or None,
                "code": error["type"],
                "message": error["msg"],
            }
        )
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.VALIDATION_ERROR,
        message="リクエストの検証に失敗しました",
        details=details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle generic HTTPException"""
    code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.UNAUTHENTICATED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    return create_error_response(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    # Log the exception here in production
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ErrorCode.INTERNAL_ERROR,
        message="予期しないエラーが発生しました",
    )
