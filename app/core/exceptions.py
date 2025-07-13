# app/core/exceptions.py - VERSIÓN SIMPLIFICADA

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
from enum import Enum

from app.core.constants import HTTPStatus, ErrorSeverity, ErrorCodeData
from app.core.messages import ErrorMessages
from app.schemas.error import ErrorResponseSchema, ValidationErrorResponseSchema, ValidationErrorDetail


class ErrorCode(Enum):
    """Códigos de error simplificados"""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = ErrorCodeData("AUTH001", HTTPStatus.UNAUTHORIZED, "Invalid credentials", ErrorSeverity.MEDIUM)
    USER_NOT_FOUND = ErrorCodeData("AUTH002", HTTPStatus.NOT_FOUND, "User not found", ErrorSeverity.LOW)
    ACCESS_DENIED = ErrorCodeData("AUTH004", HTTPStatus.FORBIDDEN, "Access denied", ErrorSeverity.MEDIUM)
    
    # Validation
    VALIDATION_ERROR = ErrorCodeData("VAL001", HTTPStatus.UNPROCESSABLE_ENTITY, "Validation error", ErrorSeverity.LOW)
    
    # Resources
    RESOURCE_NOT_FOUND = ErrorCodeData("RES001", HTTPStatus.NOT_FOUND, "Resource not found", ErrorSeverity.LOW)
    DUPLICATE_RESOURCE = ErrorCodeData("RES002", HTTPStatus.CONFLICT, "Resource already exists", ErrorSeverity.LOW)
    
    # System
    DATABASE_ERROR = ErrorCodeData("SYS001", HTTPStatus.INTERNAL_SERVER_ERROR, "Database error", ErrorSeverity.CRITICAL)
    INTERNAL_ERROR = ErrorCodeData("SYS003", HTTPStatus.INTERNAL_SERVER_ERROR, "Internal error", ErrorSeverity.CRITICAL)


class BaseError(Exception):
    """Clase base simplificada para errores"""
    
    def __init__(self, error_code: ErrorCode, message: str = None, **kwargs):
        self.error_code = error_code.value  # Acceso al dataclass
        self.message = message or self.error_code.message
        
        # Metadatos automáticos
        self.request_id = kwargs.get('request_id', str(uuid.uuid4()))
        self.path = kwargs.get('path')
        self.method = kwargs.get('method')
        self.timestamp = datetime.now(timezone.utc)
        
        # Campos específicos
        self.field = kwargs.get('field')
        self.resource_id = kwargs.get('resource_id')
        self.resource_type = kwargs.get('resource_type')
        self.details = kwargs.get('details', {})
        self.suggestions = kwargs.get('suggestions', [])
        
        super().__init__(f"[{self.error_code.code}] {self.message}")
    
    def to_schema(self) -> ErrorResponseSchema:
        """Convertir a schema para respuesta JSON"""
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
            suggestions=self.suggestions if self.suggestions else None
        )


# ============================================================================
# EXCEPCIONES ESPECÍFICAS SIMPLIFICADAS
# ============================================================================

class ValidationError(BaseError):
    """Error de validación"""
    
    def __init__(self, field: str, message: str, invalid_value: Any = None, 
                 constraint: str = None, expected_type: str = None, **kwargs):
        super().__init__(
            ErrorCode.VALIDATION_ERROR,
            message,
            field=field,
            **kwargs
        )
        self.invalid_value = invalid_value
        self.constraint = constraint
        self.expected_type = expected_type


class DuplicateResourceError(BaseError):
    """Error de recurso duplicado"""
    
    def __init__(self, resource_type: str, field: str, value: str, **kwargs):
        message = f"A {resource_type} with this {field} already exists"
        super().__init__(
            ErrorCode.DUPLICATE_RESOURCE,
            message,
            resource_type=resource_type,
            field=field,
            suggestions=[f"Use a different {field}", f"Check if the {resource_type.lower()} already exists"],
            **kwargs
        )


class ResourceNotFoundError(BaseError):
    """Error de recurso no encontrado"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"{resource_type} not found"
        super().__init__(
            ErrorCode.RESOURCE_NOT_FOUND,
            message,
            resource_type=resource_type,
            resource_id=resource_id,
            suggestions=[f"Verify that the {resource_type.lower()} ID is correct"],
            **kwargs
        )


class AuthenticationError(BaseError):
    """Error de autenticación"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            ErrorCode.INVALID_CREDENTIALS,
            message,
            suggestions=["Check your credentials", "Use 'Forgot Password' if needed"],
            **kwargs
        )


class AuthorizationError(BaseError):
    """Error de autorización"""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            ErrorCode.ACCESS_DENIED,
            message,
            suggestions=["Contact administrator for access"],
            **kwargs
        )


class DatabaseError(BaseError):
    """Error de base de datos"""
    
    def __init__(self, operation: str = "database_operation", **kwargs):
        super().__init__(
            ErrorCode.DATABASE_ERROR,
            "A database error occurred",
            details={"operation": operation},
            suggestions=["Try again", "Contact support if problem persists"],
            **kwargs
        )