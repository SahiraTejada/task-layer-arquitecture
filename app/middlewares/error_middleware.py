from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import logging
import traceback
import uuid
from typing import Any, Dict

from app.core.exceptions import (
    BaseError, ValidationError, ResourceNotFoundError, DuplicateResourceError,
    BusinessRuleError, AuthenticationError, AuthorizationError, DatabaseError,
    ErrorCode
)
from app.schemas.error import ErrorResponseSchema, ValidationErrorResponseSchema, ValidationErrorDetail

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling using new exception system"""
    
    def __init__(self, app, debug: bool = False, enable_cors: bool = True):
        super().__init__(app)
        self.debug = debug
        self.enable_cors = enable_cors
    
    async def dispatch(self, request: Request, call_next):
        """Intercepts and handles all errors"""
        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Add IDs to request state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        try:
            response = await call_next(request)
            
            # Add headers to successful responses
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            return await self._handle_error(request, exc, request_id, correlation_id)
    
    async def _handle_error(
        self, 
        request: Request, 
        exc: Exception, 
        request_id: str, 
        correlation_id: str
    ) -> JSONResponse:
        """Centralized error handling using schemas"""
        
        path = str(request.url.path)
        method = request.method
        
        # Enhanced error logging with context
        self._log_error_context(exc, request, request_id)
        
        # Custom exceptions that already return schemas
        custom_errors = (
            ValidationError, ResourceNotFoundError, DuplicateResourceError,
            BusinessRuleError, AuthenticationError, AuthorizationError, 
            DatabaseError, BaseError
        )
        
        if isinstance(exc, custom_errors):
            # Update metadata and get schema
            exc.request_id = request_id
            exc.path = path
            exc.method = method
            exc.correlation_id = correlation_id
            
            schema = exc.to_schema()
            return self._create_json_response(schema)
        
        # FastAPI validation errors
        elif isinstance(exc, RequestValidationError):
            schema = self._handle_fastapi_validation(exc, path, method, request_id, correlation_id)
            return self._create_json_response(schema)
        
        # Starlette HTTP errors
        elif isinstance(exc, StarletteHTTPException):
            schema = self._handle_http_error(exc, path, method, request_id, correlation_id)
            return self._create_json_response(schema)
        
        # Database errors
        elif isinstance(exc, (IntegrityError, SQLAlchemyError)):
            schema = self._handle_db_error(exc, path, method, request_id, correlation_id)
            return self._create_json_response(schema)
        
        # Unexpected errors
        else:
            schema = self._handle_unexpected_error(exc, path, method, request_id, correlation_id)
            return self._create_json_response(schema)
    
    def _log_error_context(self, exc: Exception, request: Request, request_id: str):
        """Enhanced error logging with full context"""
        logger.error(
            f"Error in {request.method} {request.url.path} - Request ID: {request_id}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            }
        )
    
    def _handle_fastapi_validation(
        self, 
        exc: RequestValidationError, 
        path: str, 
        method: str, 
        request_id: str, 
        correlation_id: str
    ) -> ValidationErrorResponseSchema:
        """Handle FastAPI validation errors"""
        
        validation_errors = []
        
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error.get('loc', []))
            
            validation_errors.append(ValidationErrorDetail(
                field=field_path,
                message=error.get('msg', 'Validation error'),
                invalid_value=error.get('input'),
                constraint=error.get('type'),
                expected_type=self._extract_expected_type(error)
            ))
        
        logger.warning(
            f"Validation error with {len(validation_errors)} issues",
            extra={
                "error_code": ErrorCode.VALIDATION_ERROR.value.code,
                "validation_errors_count": len(validation_errors),
                "request_id": request_id,
                "path": path
            }
        )
        
        return ValidationErrorResponseSchema(
            error=ErrorCode.VALIDATION_ERROR.value.code,
            message="The submitted data contains validation errors",
            status_code=ErrorCode.VALIDATION_ERROR.value.status_code,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            path=path,
            method=method,
            correlation_id=correlation_id,
            trace_id=str(uuid.uuid4()),
            validation_errors=validation_errors,
            suggestions=[
                "Check the fields marked as invalid",
                "Refer to API documentation for expected formats"
            ]
        )
    
    def _handle_http_error(
        self, 
        exc: StarletteHTTPException, 
        path: str, 
        method: str, 
        request_id: str, 
        correlation_id: str
    ) -> ErrorResponseSchema:
        """Handle standard HTTP errors"""
        
        # Map common HTTP status codes to our error codes
        status_mapping = {
            404: ErrorCode.RESOURCE_NOT_FOUND,
            401: ErrorCode.INVALID_CREDENTIALS,
            403: ErrorCode.ACCESS_DENIED,
            409: ErrorCode.DUPLICATE_RESOURCE,
            429: ErrorCode.QUOTA_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE,
            504: ErrorCode.TIMEOUT_ERROR
        }
        
        error_code = status_mapping.get(exc.status_code)
        
        if error_code:
            logger.warning(
                f"HTTP error mapped to {error_code.value.code}",
                extra={
                    "error_code": error_code.value.code,
                    "original_status": exc.status_code,
                    "request_id": request_id
                }
            )
            
            return ErrorResponseSchema(
                error=error_code.value.code,
                message=error_code.value.message,
                status_code=error_code.value.status_code,
                timestamp=datetime.now(timezone.utc),
                request_id=request_id,
                path=path,
                method=method,
                correlation_id=correlation_id,
                trace_id=str(uuid.uuid4())
            )
        else:
            # Generic HTTP error for unmapped status codes
            return ErrorResponseSchema(
                error="HTTP_ERROR",
                message=str(exc.detail),
                status_code=exc.status_code,
                timestamp=datetime.now(timezone.utc),
                request_id=request_id,
                path=path,
                method=method,
                correlation_id=correlation_id,
                trace_id=str(uuid.uuid4())
            )
    
    def _handle_db_error(
        self, 
        exc: Exception, 
        path: str, 
        method: str, 
        request_id: str, 
        correlation_id: str
    ) -> ErrorResponseSchema:
        """Handle database errors with smart detection"""
        
        # Detect specific database error types
        error_str = str(exc).lower()
        if isinstance(exc, IntegrityError):
            if any(keyword in error_str for keyword in ["duplicate", "unique", "already exists"]):
                error_code = ErrorCode.DUPLICATE_RESOURCE
                message = "Resource already exists"
                suggestions = ["Use unique values", "Check the data being submitted"]
            else:
                error_code = ErrorCode.DATABASE_ERROR
                message = "Database constraint violation"
                suggestions = ["Check data integrity", "Contact support if problem persists"]
        else:
            error_code = ErrorCode.DATABASE_ERROR
            message = "Database operation failed"
            suggestions = ["Try again", "Contact support if problem persists"]
        
        details = None
        if self.debug:
            details = {
                "database_error": str(exc),
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        
        logger.error(
            f"Database error: {error_code.value.code}",
            extra={
                "error_code": error_code.value.code,
                "database_error_type": type(exc).__name__,
                "request_id": request_id,
                "operation": "database_operation"
            }
        )
        
        return ErrorResponseSchema(
            error=error_code.value.code,
            message=message,
            status_code=error_code.value.status_code,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            path=path,
            method=method,
            correlation_id=correlation_id,
            trace_id=str(uuid.uuid4()),
            details=details,
            suggestions=suggestions
        )
    
    def _handle_unexpected_error(
        self, 
        exc: Exception, 
        path: str, 
        method: str, 
        request_id: str, 
        correlation_id: str
    ) -> ErrorResponseSchema:
        """Handle unexpected errors with detailed logging"""
        
        # Critical logging for unexpected errors
        logger.critical(
            f"Unexpected error: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "path": path,
                "method": method,
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            },
            exc_info=True
        )
        
        details = None
        if self.debug:
            details = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc()
            }
        
        return ErrorResponseSchema(
            error=ErrorCode.INTERNAL_ERROR.value.code,
            message="Internal server error",
            status_code=ErrorCode.INTERNAL_ERROR.value.status_code,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            path=path,
            method=method,
            correlation_id=correlation_id,
            trace_id=str(uuid.uuid4()),
            details=details,
            suggestions=[
                "Try again in a few minutes",
                "Contact technical support if the problem persists"
            ]
        )
    
    def _create_json_response(self, schema: ErrorResponseSchema) -> JSONResponse:
        """Create JSON response using Pydantic schema"""
        
        # Serialize using Pydantic (guarantees validation)
        content = schema.model_dump(exclude_none=True, by_alias=True)
        
        # Security and CORS headers
        headers = {
            "Content-Type": "application/json",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-Request-ID": schema.request_id,
            "X-Correlation-ID": schema.correlation_id or "",
            "X-Trace-ID": schema.trace_id or ""
        }
        
        # CORS headers if enabled
        if self.enable_cors:
            headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "X-Request-ID, X-Correlation-ID, X-Trace-ID"
            })
        
        return JSONResponse(
            status_code=schema.status_code,
            content=content,
            headers=headers
        )
    
    def _extract_expected_type(self, error: Dict[str, Any]) -> str:
        """Extract expected type from validation error"""
        error_type = error.get('type', '')
        
        type_mapping = {
            'string_type': 'string',
            'int_parsing': 'integer',
            'float_parsing': 'float',
            'bool_parsing': 'boolean',
            'list_type': 'array',
            'dict_type': 'object',
            'email': 'email',
            'url': 'url',
            'uuid_parsing': 'uuid',
            'datetime_parsing': 'datetime'
        }
        
        return type_mapping.get(error_type, error_type)