from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import logging

from app.utils.exceptions import (
    AppValidationError,
    BaseAppException,
    ServiceError,
    NotFoundError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserInactiveError,
)
from app.schemas.common import ErrorResponseSchema

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """Setup all exception handlers for the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseSchema(
                error="HTTP Error",
                code=exc.status_code,
                detail=exc.detail,
                error_type="HTTPException"
            ).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        
        # Extract field name from the first error
        field_name = None
        if exc.errors():
            field_path = exc.errors()[0].get('loc', [])
            field_name = field_path[-1] if field_path else None
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponseSchema(
                error="Validation Error",
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid input data",
                error_type="ValidationError",
                field=field_name
            ).model_dump()
        )

    # Custom application exceptions
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        """Handle not found errors."""
        logger.warning(f"Not found: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponseSchema(
                error="Not Found",
                code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
                error_type="NotFoundError"
            ).model_dump()
        )

    @app.exception_handler(AppValidationError)
    async def app_validation_error_handler(request: Request, exc: AppValidationError):
        """Handle custom validation errors."""
        logger.warning(f"App validation error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponseSchema(
                error="Validation Error",
                code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
                error_type="AppValidationError"
            ).model_dump()
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors."""
        logger.warning(f"Authentication error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponseSchema(
                error="Authentication Failed",
                code=status.HTTP_401_UNAUTHORIZED,
                detail=exc.message,
                error_type="AuthenticationError"
            ).model_dump()
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        """Handle authorization errors."""
        logger.warning(f"Authorization error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponseSchema(
                error="Access Forbidden",
                code=status.HTTP_403_FORBIDDEN,
                detail=exc.message,
                error_type="AuthorizationError"
            ).model_dump()
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_error_handler(request: Request, exc: UserAlreadyExistsError):
        """Handle user already exists errors."""
        logger.warning(f"User exists error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponseSchema(
                error="User Already Exists",
                code=status.HTTP_409_CONFLICT,
                detail=exc.message,
                error_type="UserAlreadyExistsError"
            ).model_dump()
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handle database errors."""
        logger.error(f"Database error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseSchema(
                error="Database Error",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred",
                error_type="DatabaseError"
            ).model_dump()
        )

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        """Handle general service errors."""
        logger.error(f"Service error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseSchema(
                error="Service Error",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal service error occurred",
                error_type="ServiceError"
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unexpected exceptions."""
        logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseSchema(
                error="Internal Server Error",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
                error_type="InternalServerError"
            ).model_dump()
        )