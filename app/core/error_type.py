from enum import Enum


class ErrorType(str, Enum):
    VALIDATION = "Validation"
    FAILURE = "Failure"
    PROBLEM = "Problem"
    NOT_FOUND = "NotFound"
    CONFLICT = "Conflict"
    UNAUTHORIZED = "Unauthorized"
    FORBIDDEN = "Forbidden"
    CONCURRENCY = "Concurrency"


ERROR_TYPE_HTTP_STATUS_MAP: dict[ErrorType, int] = {
    ErrorType.VALIDATION: 422,
    ErrorType.FAILURE: 400,
    ErrorType.PROBLEM: 500,
    ErrorType.NOT_FOUND: 404,
    ErrorType.CONFLICT: 409,
    ErrorType.UNAUTHORIZED: 401,
    ErrorType.FORBIDDEN: 403,
    ErrorType.CONCURRENCY: 409,
}
