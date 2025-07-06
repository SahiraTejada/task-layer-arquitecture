"""
Custom exception classes for the application.
These exceptions provide specific error handling for different business logic scenarios.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException
from starlette import status


class BaseCustomException(Exception):
    """
    Base exception class for all custom exceptions.
    Provides common functionality for error handling.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class HTTPBaseException(HTTPException):
    """
    Base HTTP exception that extends FastAPI's HTTPException.
    Used for exceptions that should be returned as HTTP responses.
    """
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# ================================
# USER-RELATED EXCEPTIONS
# ================================

class UserNotFoundError(BaseCustomException):
    """
    Raised when a user is not found in the database.
    
    Usage:
        raise UserNotFoundError(f"User with ID {user_id} not found")
    """
    def __init__(self, message: str = "User not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class UserAlreadyExistsError(BaseCustomException):
    """
    Raised when trying to create a user that already exists.
    
    Usage:
        raise UserAlreadyExistsError(f"User with email {email} already exists")
    """
    def __init__(self, message: str = "User already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class InvalidCredentialsError(BaseCustomException):
    """
    Raised when authentication credentials are invalid.
    
    Usage:
        raise InvalidCredentialsError("Invalid email or password")
    """
    def __init__(self, message: str = "Invalid credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class UserInactiveError(BaseCustomException):
    """
    Raised when trying to authenticate an inactive user.
    
    Usage:
        raise UserInactiveError("User account is inactive")
    """
    def __init__(self, message: str = "User account is inactive", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# TASK-RELATED EXCEPTIONS
# ================================

class TaskNotFoundError(BaseCustomException):
    """
    Raised when a task is not found in the database.
    """
    def __init__(self, message: str = "Task not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class TaskAlreadyExistsError(BaseCustomException):
    """
    Raised when trying to create a task that already exists.
    """
    def __init__(self, message: str = "Task already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class TaskPermissionError(BaseCustomException):
    """
    Raised when a user doesn't have permission to access/modify a task.
    """
    def __init__(self, message: str = "Insufficient permissions for this task", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# TAG-RELATED EXCEPTIONS
# ================================

class TagNotFoundError(BaseCustomException):
    """
    Raised when a tag is not found in the database.
    """
    def __init__(self, message: str = "Tag not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class TagAlreadyExistsError(BaseCustomException):
    """
    Raised when trying to create a tag that already exists.
    """
    def __init__(self, message: str = "Tag already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# VALIDATION EXCEPTIONS
# ================================

class ValidationError(BaseCustomException):
    """
    Raised when data validation fails.
    """
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class InvalidDataError(BaseCustomException):
    """
    Raised when provided data is invalid or malformed.
    """
    def __init__(self, message: str = "Invalid data provided", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# AUTHORIZATION EXCEPTIONS
# ================================

class AuthorizationError(BaseCustomException):
    """
    Raised when a user is not authorized to perform an action.
    """
    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class TokenExpiredError(BaseCustomException):
    """
    Raised when an authentication token has expired.
    """
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class InvalidTokenError(BaseCustomException):
    """
    Raised when an authentication token is invalid.
    """
    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# DATABASE EXCEPTIONS
# ================================

class DatabaseError(BaseCustomException):
    """
    Raised when a database operation fails.
    """
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class ConnectionError(BaseCustomException):
    """
    Raised when database connection fails.
    """
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# BUSINESS LOGIC EXCEPTIONS
# ================================

class BusinessLogicError(BaseCustomException):
    """
    Raised when business logic validation fails.
    """
    def __init__(self, message: str = "Business logic validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class ResourceNotFoundError(BaseCustomException):
    """
    Generic exception for when any resource is not found.
    """
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class DuplicateResourceError(BaseCustomException):
    """
    Generic exception for when trying to create a duplicate resource.
    """
    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# ================================
# HTTP EXCEPTIONS (for FastAPI)
# ================================

class HTTPUserNotFoundError(HTTPBaseException):
    """HTTP 404 - User not found"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class HTTPUserAlreadyExistsError(HTTPBaseException):
    """HTTP 409 - User already exists"""
    def __init__(self, detail: str = "User already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class HTTPInvalidCredentialsError(HTTPBaseException):
    """HTTP 401 - Invalid credentials"""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class HTTPUserInactiveError(HTTPBaseException):
    """HTTP 403 - User inactive"""
    def __init__(self, detail: str = "User account is inactive"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class HTTPAuthorizationError(HTTPBaseException):
    """HTTP 403 - Not authorized"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class HTTPValidationError(HTTPBaseException):
    """HTTP 422 - Validation error"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


# ================================
# EXCEPTION MAPPING
# ================================

def map_to_http_exception(exception: BaseCustomException) -> HTTPException:
    """
    Maps custom exceptions to appropriate HTTP exceptions.
    
    Args:
        exception: The custom exception to map
        
    Returns:
        HTTPException: The corresponding HTTP exception
    """
    exception_map = {
        UserNotFoundError: HTTPUserNotFoundError,
        UserAlreadyExistsError: HTTPUserAlreadyExistsError,
        InvalidCredentialsError: HTTPInvalidCredentialsError,
        UserInactiveError: HTTPUserInactiveError,
        AuthorizationError: HTTPAuthorizationError,
        ValidationError: HTTPValidationError,
        TaskNotFoundError: lambda msg: HTTPException(status_code=404, detail=msg),
        TagNotFoundError: lambda msg: HTTPException(status_code=404, detail=msg),
        ResourceNotFoundError: lambda msg: HTTPException(status_code=404, detail=msg),
        DuplicateResourceError: lambda msg: HTTPException(status_code=409, detail=msg),
        BusinessLogicError: lambda msg: HTTPException(status_code=400, detail=msg),
        DatabaseError: lambda msg: HTTPException(status_code=500, detail="Internal server error"),
    }
    
    exception_class = exception_map.get(type(exception))
    if exception_class:
        if isinstance(exception_class, type) and issubclass(exception_class, HTTPBaseException):
            return exception_class(exception.message)
        else:
            return exception_class(exception.message)
    
    # Default to 500 Internal Server Error
    return HTTPException(status_code=500, detail="Internal server error")