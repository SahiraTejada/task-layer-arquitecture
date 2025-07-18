"""
Custom exception classes for the application.
"""

class BaseAppException(Exception):
    """Base exception class for all application exceptions."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ServiceError(BaseAppException):
    """General service layer error."""
    pass


class NotFoundError(BaseAppException):
    """Entity not found error."""
    pass


class AppValidationError(BaseAppException):
    """Data validation error - renamed to avoid conflict with Pydantic ValidationError."""
    pass


class DatabaseError(BaseAppException):
    """Database operation error."""
    pass


class AuthenticationError(BaseAppException):
    """Authentication error."""
    pass


class AuthorizationError(BaseAppException):
    """Authorization error."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error."""
    pass


class UserAlreadyExistsError(AppValidationError):
    """User already exists error."""
    pass


class UserNotFoundError(NotFoundError):
    """User not found error."""
    pass


class UserInactiveError(AuthenticationError):
    """User inactive error."""
    pass
