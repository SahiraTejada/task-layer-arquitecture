from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime, timezone
import uuid
import logging

from app.core.constants import HTTPStatus, ErrorSeverity, ErrorCodeData
from app.core.messages import ValidationMessages, ErrorMessages, SuggestionMessages
from app.schemas.error import (
    ErrorResponseSchema, ValidationErrorResponseSchema, 
    ValidationErrorDetail, BusinessErrorResponseSchema
)

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes with improved dataclass"""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = ErrorCodeData("AUTH001", HTTPStatus.UNAUTHORIZED, ErrorMessages.INVALID_CREDENTIALS, ErrorSeverity.MEDIUM)
    USER_NOT_FOUND = ErrorCodeData("AUTH002", HTTPStatus.NOT_FOUND, ErrorMessages.USER_NOT_FOUND, ErrorSeverity.LOW)
    USER_INACTIVE = ErrorCodeData("AUTH003", HTTPStatus.FORBIDDEN, ErrorMessages.ACCOUNT_INACTIVE, ErrorSeverity.MEDIUM)
    ACCESS_DENIED = ErrorCodeData("AUTH004", HTTPStatus.FORBIDDEN, ErrorMessages.ACCESS_DENIED, ErrorSeverity.MEDIUM)
    TOKEN_EXPIRED = ErrorCodeData("AUTH005", HTTPStatus.UNAUTHORIZED, "Token expired", ErrorSeverity.LOW)
    TOKEN_INVALID = ErrorCodeData("AUTH006", HTTPStatus.UNAUTHORIZED, "Invalid token", ErrorSeverity.MEDIUM)
    
    # Validation
    VALIDATION_ERROR = ErrorCodeData("VAL001", HTTPStatus.UNPROCESSABLE_ENTITY, "Validation error", ErrorSeverity.LOW)
    REQUIRED_FIELD = ErrorCodeData("VAL002", HTTPStatus.BAD_REQUEST, "Required field", ErrorSeverity.LOW)
    INVALID_FORMAT = ErrorCodeData("VAL003", HTTPStatus.BAD_REQUEST, "Invalid format", ErrorSeverity.LOW)
    OUT_OF_RANGE = ErrorCodeData("VAL004", HTTPStatus.BAD_REQUEST, "Value out of range", ErrorSeverity.LOW)
    
    # Resources
    RESOURCE_NOT_FOUND = ErrorCodeData("RES001", HTTPStatus.NOT_FOUND, "Resource not found", ErrorSeverity.LOW)
    DUPLICATE_RESOURCE = ErrorCodeData("RES002", HTTPStatus.CONFLICT, "Resource already exists", ErrorSeverity.LOW)
    RESOURCE_LOCKED = ErrorCodeData("RES003", HTTPStatus.CONFLICT, "Resource is locked", ErrorSeverity.MEDIUM)
    
    # Business Logic
    BUSINESS_RULE_VIOLATION = ErrorCodeData("BIZ001", HTTPStatus.BAD_REQUEST, "Business rule violation", ErrorSeverity.MEDIUM)
    INSUFFICIENT_PERMISSIONS = ErrorCodeData("BIZ002", HTTPStatus.FORBIDDEN, "Insufficient permissions", ErrorSeverity.MEDIUM)
    OPERATION_NOT_ALLOWED = ErrorCodeData("BIZ003", HTTPStatus.FORBIDDEN, "Operation not allowed", ErrorSeverity.MEDIUM)
    QUOTA_EXCEEDED = ErrorCodeData("BIZ004", HTTPStatus.TOO_MANY_REQUESTS, "Quota exceeded", ErrorSeverity.HIGH)
    
    # System
    DATABASE_ERROR = ErrorCodeData("SYS001", HTTPStatus.INTERNAL_SERVER_ERROR, ErrorMessages.DATABASE_ERROR, ErrorSeverity.CRITICAL)
    EXTERNAL_SERVICE_ERROR = ErrorCodeData("SYS002", HTTPStatus.BAD_GATEWAY, ErrorMessages.EXTERNAL_SERVICE_ERROR, ErrorSeverity.HIGH)
    INTERNAL_ERROR = ErrorCodeData("SYS003", HTTPStatus.INTERNAL_SERVER_ERROR, ErrorMessages.INTERNAL_ERROR, ErrorSeverity.CRITICAL)
    SERVICE_UNAVAILABLE = ErrorCodeData("SYS004", HTTPStatus.SERVICE_UNAVAILABLE, "Service unavailable", ErrorSeverity.HIGH)
    TIMEOUT_ERROR = ErrorCodeData("SYS005", HTTPStatus.GATEWAY_TIMEOUT, "Timeout", ErrorSeverity.HIGH)


class ValidationErrorCollector:
    """IMPROVEMENT 2: Enhanced collector that handles multiple errors correctly"""
    
    def __init__(self):
        self.errors: List[ValidationErrorDetail] = []
    
    def add_error(self, field: str, message: str, invalid_value: Any = None, 
                  constraint: str = None, expected_type: str = None, 
                  allowed_values: List[str] = None):
        """Add a validation error"""
        self.errors.append(ValidationErrorDetail(
            field=field,
            message=message,
            invalid_value=invalid_value,
            constraint=constraint,
            expected_type=expected_type,
            allowed_values=allowed_values
        ))
    
    def add_validation_error(self, validation_error: 'ValidationError'):
        """IMPROVEMENT 2: Add errors from existing ValidationError"""
        for err in validation_error.validation_errors:
            # Use model_dump() to get dict and unpack
            self.errors.append(ValidationErrorDetail(**err.model_dump()))
    
    def has_errors(self) -> bool:
        """Check if there are errors"""
        return len(self.errors) > 0
    
    def raise_if_errors(self, **kwargs):
        """Raise ValidationError if there are accumulated errors"""
        if self.has_errors():
            raise ValidationError.from_multiple(self.errors, **kwargs)


class BaseError(Exception):
    """Optimized base class"""
    
    def __init__(self, error_code: ErrorCode, message: str = None, **kwargs):
        self.error_code = error_code.value  # Access to dataclass
        self.message = message or self.error_code.message
        
        # Automatic metadata
        self.request_id = kwargs.get('request_id', str(uuid.uuid4()))
        self.path = kwargs.get('path')
        self.method = kwargs.get('method')
        self.correlation_id = kwargs.get('correlation_id')
        self.trace_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        
        # Specific fields
        self.field = kwargs.get('field')
        self.resource_id = kwargs.get('resource_id')
        self.resource_type = kwargs.get('resource_type')
        self.details = kwargs.get('details', {})
        self.suggestions = kwargs.get('suggestions', [])
        
        # Automatic logging
        self._auto_log()
        
        # Error code in message for debugging
        debug_message = f"[{self.error_code.code}] {self.message}"
        super().__init__(debug_message)
    
    def _auto_log(self):
        """Automatic logging based on severity"""
        log_data = {
            "error_code": self.error_code.code,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "field": self.field,
            "resource_id": self.resource_id,
            "severity": self.error_code.severity.value
        }
        
        message = f"[{self.error_code.code}] {self.message}"
        
        if self.error_code.severity == ErrorSeverity.CRITICAL:
            logger.critical(message, extra=log_data)
        elif self.error_code.severity == ErrorSeverity.HIGH:
            logger.error(message, extra=log_data)
        elif self.error_code.severity == ErrorSeverity.MEDIUM:
            logger.warning(message, extra=log_data)
        else:
            logger.info(message, extra=log_data)
    
    def to_schema(self) -> ErrorResponseSchema:
        """Base schema"""
        return ErrorResponseSchema(
            error=self.error_code.code,
            message=self.message,
            status_code=self.error_code.status_code,
            timestamp=self.timestamp,
            request_id=self.request_id,
            path=self.path,
            method=self.method,
            field=self.field,
            resource_id=self.resource_id,
            resource_type=self.resource_type,
            details=self.details if self.details else None,
            suggestions=self.suggestions if self.suggestions else None,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id
        )
    
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Schema dict for serialization"""
        return self.to_schema().model_dump(exclude_none=True)
    
    @property
    def as_response(self) -> Dict[str, Any]:
        """Semantic alias for HTTP responses"""
        return self.as_dict


class ValidationError(BaseError):
    """Enhanced validation error"""
    
    def __init__(self, field: str = None, message: str = None, invalid_value: Any = None, 
                 constraint: str = None, expected_type: str = None, 
                 allowed_values: List[str] = None, validation_errors: List[ValidationErrorDetail] = None, **kwargs):
        
        if validation_errors:
            self.validation_errors = validation_errors
            message = message or f"Found {len(validation_errors)} validation errors"
        else:
            self.validation_errors = [ValidationErrorDetail(
                field=field,
                message=message,
                invalid_value=invalid_value,
                constraint=constraint,
                expected_type=expected_type,
                allowed_values=allowed_values
            )]
        
        super().__init__(ErrorCode.VALIDATION_ERROR, message, field=field, **kwargs)
    
    @classmethod
    def from_multiple(cls, validation_errors: List[ValidationErrorDetail], **kwargs):
        """Create ValidationError with multiple errors"""
        return cls(validation_errors=validation_errors, **kwargs)
    
    def to_schema(self) -> ValidationErrorResponseSchema:
        """Specific schema for validation"""
        base_schema = super().to_schema()
        return ValidationErrorResponseSchema(
            **base_schema.model_dump(),
            validation_errors=self.validation_errors
        )


class ResourceNotFoundError(BaseError):
    """Resource not found error with centralized messages"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = ErrorMessages.format_message(
            ErrorMessages.RESOURCE_NOT_FOUND, 
            resource_type=resource_type
        )
        suggestions = [SuggestionMessages.get_verify_id_suggestion(resource_type)]
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, 
                        resource_type=resource_type, resource_id=resource_id, 
                        suggestions=suggestions, **kwargs)


class DuplicateResourceError(BaseError):
    """Duplicate resource error with centralized messages"""
    
    def __init__(self, resource_type: str, field: str, value: str, **kwargs):
        message = ErrorMessages.format_message(
            ErrorMessages.RESOURCE_DUPLICATE,
            resource_type=resource_type,
            field=field,
            value=value
        )
        suggestions = [f"Use a different {field}"]
        details = {"field": field, "value": value}
        super().__init__(ErrorCode.DUPLICATE_RESOURCE, message,
                        resource_type=resource_type, field=field,
                        suggestions=suggestions, details=details, **kwargs)


class BusinessRuleError(BaseError):
    """Business rule error"""
    
    def __init__(self, rule_name: str, message: str, rule_description: str = None,
                 context_data: Dict[str, Any] = None, suggestions: List[str] = None, **kwargs):
        self.rule_name = rule_name
        self.rule_description = rule_description
        self.context_data = context_data or {}
        details = {"rule": rule_name, "context": self.context_data}
        super().__init__(ErrorCode.BUSINESS_RULE_VIOLATION, message,
                        details=details, suggestions=suggestions or [], **kwargs)
    
    def to_schema(self) -> BusinessErrorResponseSchema:
        base_schema = super().to_schema()
        return BusinessErrorResponseSchema(
            **base_schema.model_dump(),
            rule_name=self.rule_name,
            rule_description=self.rule_description,
            context_data=self.context_data
        )


class AuthenticationError(BaseError):
    """Authentication error"""
    
    def __init__(self, message: str = ErrorMessages.INVALID_CREDENTIALS, field: str = None, **kwargs):
        super().__init__(ErrorCode.INVALID_CREDENTIALS, message, field=field, **kwargs)


class AuthorizationError(BaseError):
    """Authorization error"""
    
    def __init__(self, message: str = ErrorMessages.ACCESS_DENIED, resource_type: str = None, 
                 suggestions: List[str] = None, **kwargs):
        default_suggestions = [SuggestionMessages.CHECK_PERMISSIONS, SuggestionMessages.CONTACT_ADMIN]
        super().__init__(ErrorCode.ACCESS_DENIED, message, 
                        resource_type=resource_type, 
                        suggestions=suggestions or default_suggestions, **kwargs)


class DatabaseError(BaseError):
    """Database error"""
    
    def __init__(self, operation: str = None, details: Dict[str, Any] = None, **kwargs):
        message = ErrorMessages.DATABASE_ERROR
        suggestions = [SuggestionMessages.TRY_AGAIN, SuggestionMessages.CONTACT_SUPPORT]
        all_details = {"operation": operation, **(details or {})}
        super().__init__(ErrorCode.DATABASE_ERROR, message,
                        details=all_details, suggestions=suggestions, **kwargs)