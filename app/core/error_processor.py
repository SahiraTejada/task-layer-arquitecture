# ============================================================================
# app/core/error_processor.py - ENTERPRISE ERROR PROCESSING SYSTEM
# ============================================================================

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Type, Union
import uuid
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import BaseError, ErrorCode
from app.schemas.error import ErrorResponseSchema, ValidationErrorResponseSchema, ValidationErrorDetail

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Niveles de severidad para clasificación automática"""
    INFO = "info"
    WARNING = "warning"  
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ErrorContext:
    """Contexto inmutable del error - Value Object"""
    request_id: str
    correlation_id: str
    path: str
    method: str
    timestamp: datetime
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    query_params: Optional[str] = None

    @classmethod
    def from_request(cls, request: Request, request_id: str, correlation_id: str) -> 'ErrorContext':
        """Factory method para crear contexto desde request"""
        return cls(
            request_id=request_id,
            correlation_id=correlation_id,
            path=str(request.url.path),
            method=request.method,
            timestamp=datetime.now(timezone.utc),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            query_params=str(request.query_params) if request.query_params else None
        )


@dataclass
class ErrorProcessingResult:
    """Resultado del procesamiento de errores"""
    schema: Union[ErrorResponseSchema, ValidationErrorResponseSchema]
    severity: ErrorSeverity
    should_alert: bool = False
    metrics_tags: Dict[str, str] = field(default_factory=dict)


class ErrorProcessor(ABC):
    """Interface para procesadores de errores específicos"""
    
    @abstractmethod
    def can_process(self, exc: Exception) -> bool:
        """Determina si este procesador puede manejar la excepción"""
        pass
    
    @abstractmethod
    def process(self, exc: Exception, context: ErrorContext) -> ErrorProcessingResult:
        """Procesa la excepción y retorna el resultado"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Prioridad del procesador (menor número = mayor prioridad)"""
        pass


class ValidationErrorProcessor(ErrorProcessor):
    """Procesador especializado para errores de validación"""
    
    @property
    def priority(self) -> int:
        return 1
    
    def can_process(self, exc: Exception) -> bool:
        return isinstance(exc, RequestValidationError)
    
    def process(self, exc: RequestValidationError, context: ErrorContext) -> ErrorProcessingResult:
        validation_errors = self._extract_validation_errors(exc)
        
        schema = ValidationErrorResponseSchema(
            error=ErrorCode.VALIDATION_ERROR.value.code,
            message="Invalid input data provided",
            status_code=ErrorCode.VALIDATION_ERROR.value.status_code,
            timestamp=context.timestamp,
            request_id=context.request_id,
            path=context.path,
            method=context.method,
            correlation_id=context.correlation_id,
            trace_id=str(uuid.uuid4()),
            validation_errors=validation_errors,
            suggestions=self._generate_suggestions(validation_errors)
        )
        
        return ErrorProcessingResult(
            schema=schema,
            severity=ErrorSeverity.INFO,
            metrics_tags={"error_type": "validation", "field_count": str(len(validation_errors))}
        )
    
    def _extract_validation_errors(self, exc: RequestValidationError) -> List[ValidationErrorDetail]:
        """Extrae y convierte errores de validación a formato amigable"""
        errors = []
        
        for error in exc.errors():
            field = self._extract_field_name(error.get('loc', []))
            message = self._humanize_message(error, field)
            
            errors.append(ValidationErrorDetail(
                field=field,
                message=message,
                invalid_value=error.get('input'),
                constraint=error.get('type'),
                expected_type=self._map_expected_type(error.get('type', ''))
            ))
        
        return errors
    
    def _extract_field_name(self, location: list) -> str:
        """Extrae nombre de campo limpio de la ubicación del error"""
        if not location:
            return "root"
        
        # Omitir 'body' y otros prefijos técnicos
        clean_path = [str(loc) for loc in location if str(loc) not in ('body', '__root__')]
        return ".".join(clean_path) if clean_path else "root"
    
    def _humanize_message(self, error: dict, field: str) -> str:
        """Convierte mensajes técnicos en mensajes amigables"""
        error_type = error.get('type', '')
        error_msg = error.get('msg', '')
        
        # Mapeo directo de tipos comunes
        message_map = {
            'value_error.email': "Please provide a valid email address",
            'string_type': f"{field.title()} must be text",
            'int_type': f"{field.title()} must be a whole number",
            'float_type': f"{field.title()} must be a number",
            'bool_type': f"{field.title()} must be true or false",
            'missing': f"{field.title()} is required",
            'string_too_short': f"{field.title()} is too short",
            'string_too_long': f"{field.title()} is too long"
        }
        
        # Buscar mensaje amigable exacto
        if error_type in message_map:
            return message_map[error_type]
        
        # Si es un error de email específico
        if 'email' in error_type.lower() or 'email' in error_msg.lower():
            return "Please provide a valid email address"
        
        # Casos especiales basados en el mensaje
        if "value is not a valid email" in error_msg:
            return "Please provide a valid email address"
        elif "ensure this value has at least" in error_msg:
            return f"{field.title()} is too short"
        elif "ensure this value has at most" in error_msg:
            return f"{field.title()} is too long"
        elif "field required" in error_msg:
            return f"{field.title()} is required"
        elif "not a valid" in error_msg:
            return f"{field.title()} format is invalid"
        
        # Fallback al mensaje original pero mejorado
        return f"{field.title()} has an invalid value"
    
    def _map_expected_type(self, error_type: str) -> str:
        """Mapea tipos de error a tipos esperados legibles"""
        type_map = {
            'string_type': 'text',
            'int_type': 'number',
            'float_type': 'decimal',
            'bool_type': 'boolean',
            'value_error.email': 'email',
            'list_type': 'list',
            'dict_type': 'object'
        }
        return type_map.get(error_type, 'valid value')
    
    def _generate_suggestions(self, validation_errors: List[ValidationErrorDetail]) -> List[str]:
        """Genera sugerencias específicas basadas en los errores"""
        suggestions = set()
        
        for error in validation_errors:
            field_lower = error.field.lower()
            
            if 'email' in field_lower:
                suggestions.add("Ensure email includes @ symbol and valid domain")
            elif 'password' in field_lower:
                suggestions.add("Password must meet security requirements")
            elif 'phone' in field_lower:
                suggestions.add("Use correct phone number format")
            
        suggestions.add("Check API documentation for field requirements")
        return list(suggestions)[:3]


class HttpErrorProcessor(ErrorProcessor):
    """Procesador para errores HTTP estándar"""
    
    @property
    def priority(self) -> int:
        return 2
    
    def can_process(self, exc: Exception) -> bool:
        return isinstance(exc, HTTPException)
    
    def process(self, exc: HTTPException, context: ErrorContext) -> ErrorProcessingResult:
        error_code = self._map_status_to_error_code(exc.status_code)
        severity = ErrorSeverity.ERROR if exc.status_code >= 500 else ErrorSeverity.WARNING
        
        schema = ErrorResponseSchema(
            error=error_code.value.code,
            message=str(exc.detail),
            status_code=exc.status_code,
            timestamp=context.timestamp,
            request_id=context.request_id,
            path=context.path,
            method=context.method,
            correlation_id=context.correlation_id,
            trace_id=str(uuid.uuid4())
        )
        
        return ErrorProcessingResult(
            schema=schema,
            severity=severity,
            should_alert=exc.status_code >= 500,
            metrics_tags={"error_type": "http", "status_code": str(exc.status_code)}
        )
    
    def _map_status_to_error_code(self, status_code: int) -> ErrorCode:
        """Mapea códigos HTTP a error codes internos"""
        mapping = {
            401: ErrorCode.INVALID_CREDENTIALS,
            403: ErrorCode.ACCESS_DENIED,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.DUPLICATE_RESOURCE,
            429: ErrorCode.QUOTA_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE,
            504: ErrorCode.TIMEOUT_ERROR
        }
        return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)


class DatabaseErrorProcessor(ErrorProcessor):
    """Procesador para errores de base de datos"""
    
    @property
    def priority(self) -> int:
        return 3
    
    def can_process(self, exc: Exception) -> bool:
        return isinstance(exc, (IntegrityError, SQLAlchemyError))
    
    def process(self, exc: Exception, context: ErrorContext) -> ErrorProcessingResult:
        error_code, message, suggestions = self._analyze_database_error(exc)
        
        schema = ErrorResponseSchema(
            error=error_code.value.code,
            message=message,
            status_code=error_code.value.status_code,
            timestamp=context.timestamp,
            request_id=context.request_id,
            path=context.path,
            method=context.method,
            correlation_id=context.correlation_id,
            trace_id=str(uuid.uuid4()),
            suggestions=suggestions
        )
        
        return ErrorProcessingResult(
            schema=schema,
            severity=ErrorSeverity.ERROR,
            should_alert=True,
            metrics_tags={"error_type": "database", "db_error": type(exc).__name__}
        )
    
    def _analyze_database_error(self, exc: Exception) -> tuple[ErrorCode, str, List[str]]:
        """Analiza el error de BD y retorna información estructurada"""
        error_str = str(exc).lower()
        
        if isinstance(exc, IntegrityError):
            if any(word in error_str for word in ['duplicate', 'unique']):
                return (
                    ErrorCode.DUPLICATE_RESOURCE,
                    "Resource already exists",
                    ["Use unique values", "Check existing data"]
                )
            else:
                return (
                    ErrorCode.DATABASE_ERROR,
                    "Data constraint violation",
                    ["Verify data integrity", "Check required relationships"]
                )
        
        return (
            ErrorCode.DATABASE_ERROR,
            "Database operation failed",
            ["Try again", "Contact support if persistent"]
        )


class CustomErrorProcessor(ErrorProcessor):
    """Procesador para errores personalizados del sistema"""
    
    @property
    def priority(self) -> int:
        return 0  # Máxima prioridad
    
    def can_process(self, exc: Exception) -> bool:
        return isinstance(exc, BaseError)
    
    def process(self, exc: BaseError, context: ErrorContext) -> ErrorProcessingResult:
        # Actualizar contexto en la excepción
        exc.request_id = context.request_id
        exc.path = context.path
        exc.method = context.method
        exc.correlation_id = context.correlation_id
        
        return ErrorProcessingResult(
            schema=exc.to_schema(),
            severity=self._map_severity(exc.error_code.severity),
            should_alert=exc.error_code.severity.value in ('high', 'critical'),
            metrics_tags={"error_type": "custom", "error_code": exc.error_code.code}
        )
    
    def _map_severity(self, error_severity) -> ErrorSeverity:
        """Mapea severidad de error a severidad de logging"""
        mapping = {
            'low': ErrorSeverity.INFO,
            'medium': ErrorSeverity.WARNING,
            'high': ErrorSeverity.ERROR,
            'critical': ErrorSeverity.CRITICAL
        }
        return mapping.get(error_severity.value, ErrorSeverity.ERROR)


class FallbackErrorProcessor(ErrorProcessor):
    """Procesador de respaldo para errores no manejados"""
    
    @property
    def priority(self) -> int:
        return 999  # Prioridad más baja
    
    def can_process(self, exc: Exception) -> bool:
        return True  # Maneja cualquier excepción
    
    def process(self, exc: Exception, context: ErrorContext) -> ErrorProcessingResult:
        schema = ErrorResponseSchema(
            error=ErrorCode.INTERNAL_ERROR.value.code,
            message="An unexpected error occurred",
            status_code=ErrorCode.INTERNAL_ERROR.value.status_code,
            timestamp=context.timestamp,
            request_id=context.request_id,
            path=context.path,
            method=context.method,
            correlation_id=context.correlation_id,
            trace_id=str(uuid.uuid4()),
            suggestions=["Try again later", "Contact support if problem persists"]
        )
        
        return ErrorProcessingResult(
            schema=schema,
            severity=ErrorSeverity.CRITICAL,
            should_alert=True,
            metrics_tags={"error_type": "unexpected", "exception": type(exc).__name__}
        )


class ErrorLoggerService:
    """Servicio especializado para logging de errores"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_error(self, exc: Exception, context: ErrorContext, result: ErrorProcessingResult):
        """Log error con nivel apropiado y contexto completo"""
        log_data = {
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "path": context.path,
            "method": context.method,
            "error_type": type(exc).__name__,
            "error_code": getattr(result.schema, 'error', 'unknown'),
            **result.metrics_tags
        }
        
        message = f"Error in {context.method} {context.path}"
        
        if result.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(message, extra=log_data, exc_info=True)
        elif result.severity == ErrorSeverity.ERROR:
            self.logger.error(message, extra=log_data, exc_info=True)
        elif result.severity == ErrorSeverity.WARNING:
            self.logger.warning(message, extra=log_data)
        else:
            self.logger.info(message, extra=log_data)


class EnterpriseErrorHandler:
    """
    Handler de errores enterprise con arquitectura limpia.
    
    Características:
    - Chain of Responsibility pattern para procesadores
    - Separation of Concerns (logging, processing, response)
    - Inmutable context objects
    - Extensible sin modificar código existente
    """
    
    def __init__(self, debug: bool = False, enable_cors: bool = True):
        self.debug = debug
        self.enable_cors = enable_cors
        self.logger_service = ErrorLoggerService(logger)
        
        # Registrar procesadores en orden de prioridad
        self._processors: List[ErrorProcessor] = [
            CustomErrorProcessor(),
            ValidationErrorProcessor(),
            HttpErrorProcessor(),
            DatabaseErrorProcessor(),
            FallbackErrorProcessor()
        ]
        
        # Ordenar por prioridad
        self._processors.sort(key=lambda p: p.priority)
    
    async def handle_error(
        self,
        request: Request,
        exc: Exception,
        request_id: str,
        correlation_id: str
    ) -> JSONResponse:
        """
        Maneja cualquier excepción usando el patrón Chain of Responsibility.
        """
        # Crear contexto inmutable
        context = ErrorContext.from_request(request, request_id, correlation_id)
        
        # Encontrar procesador apropiado
        processor = self._find_processor(exc)
        
        # Procesar error
        result = processor.process(exc, context)
        
        # Log con servicio especializado
        self.logger_service.log_error(exc, context, result)
        
        # Alertas si es necesario (implementar según necesidades)
        if result.should_alert:
            await self._send_alert(exc, context, result)
        
        # Crear respuesta HTTP
        return self._create_response(result.schema, context)
    
    def _find_processor(self, exc: Exception) -> ErrorProcessor:
        """Encuentra el primer procesador que puede manejar la excepción"""
        for processor in self._processors:
            if processor.can_process(exc):
                return processor
        
        # Esto nunca debería pasar por el FallbackErrorProcessor
        raise RuntimeError("No error processor found")
    
    async def _send_alert(self, exc: Exception, context: ErrorContext, result: ErrorProcessingResult):
        """Envía alertas para errores críticos (implementar según necesidades)"""
        # Aquí podrías integrar con Slack, PagerDuty, etc.
        pass
    
    def _create_response(self, schema: Union[ErrorResponseSchema, ValidationErrorResponseSchema], context: ErrorContext) -> JSONResponse:
        """Crea respuesta HTTP estandarizada"""
        content = schema.model_dump(exclude_none=True, by_alias=True)
        
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": context.request_id,
            "X-Correlation-ID": context.correlation_id,
            "X-Trace-ID": getattr(schema, 'trace_id', ''),
        }
        
        if self.enable_cors:
            headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "X-Request-ID, X-Correlation-ID, X-Trace-ID"
            })
        
        return JSONResponse(
            status_code=schema.status_code,
            content=content,
            headers=headers
        )