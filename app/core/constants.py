# app/core/constants.py - COMPLETE CONSTANTS FILE

from enum import Enum
from dataclasses import dataclass


class HTTPStatus(Enum):
    """HTTP Status codes for consistent usage across the application"""
    
    # Success responses
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Redirection responses
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304
    
    # Client error responses
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    IM_A_TEAPOT = 418  # RFC 2324
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    TOO_EARLY = 425
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    UNAVAILABLE_FOR_LEGAL_REASONS = 451
    
    # Server error responses
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511


class ErrorSeverity(Enum):
    """
    Error severity levels with clear usage guidelines.
    
    Usage:
    - LOW: Normal user errors, validation issues
    - MEDIUM: Business rule violations, auth issues
    - HIGH: System issues that affect functionality
    - CRITICAL: System failures requiring immediate attention
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ErrorCodeData:
    """
    Immutable dataclass containing error code information.
    
    This is a Value Object that ensures error codes are consistent
    and contain all necessary metadata.
    """
    code: str
    status: HTTPStatus
    message: str
    severity: ErrorSeverity
    
    @property
    def status_code(self) -> int:
        """Get HTTP status code as integer"""
        return self.status.value
    
    @property
    def is_client_error(self) -> bool:
        """Check if this is a client error (4xx)"""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if this is a server error (5xx)"""
        return 500 <= self.status_code < 600
    
    @property
    def requires_alert(self) -> bool:
        """Check if this error should trigger an alert"""
        return self.severity in (ErrorSeverity.HIGH, ErrorSeverity.CRITICAL)


# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

class AppConstants:
    """Application-wide constants for configuration and limits"""
    
    # API Configuration
    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1
    
    # String length limits
    MAX_STRING_LENGTH = 1000
    MAX_TEXT_LENGTH = 10000
    MAX_URL_LENGTH = 2048
    
    # Username and email constraints
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 254
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # File upload limits
    MAX_FILE_SIZE_MB = 10
    MAX_FILES_PER_UPLOAD = 5
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = "100/hour"
    STRICT_RATE_LIMIT = "10/minute"
    
    # Timeout settings
    DEFAULT_TIMEOUT_SECONDS = 30
    LONG_TIMEOUT_SECONDS = 300
    
    # Encoding
    DEFAULT_ENCODING = "utf-8"
    
    # Date formats
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    DATETIME_FORMAT_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================================
# REGEX PATTERNS FOR VALIDATION
# ============================================================================

class RegexPatterns:
    """Common regex patterns for validation"""

    # Email pattern (RFC 5322 compliant)
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Username pattern (alphanumeric + underscore, 3-50 characters)
    USERNAME = r'^[a-zA-Z0-9_]{3,50}$'

    # Password pattern (at least 8 chars, with uppercase, lowercase, digit, special char)
    PASSWORD = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

    # US phone number pattern (e.g., +12345678900)
    PHONE_US = r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$'

    # International phone number pattern (E.164 format)
    PHONE_INTERNATIONAL = r'^\+?[1-9]\d{1,14}$'

    # URL pattern (http or https)
    URL = r'^https?:\/\/(?:[-\w.]+)(?:\:[0-9]+)?(?:\/[\w\/_.-]*)?(?:\?(?:[\w&=%.+-]*)?)?(?:\#(?:[\w.-]*)?)?$'

    # UUID pattern (version 4 UUIDs)
    UUID = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'

    # Alphanumeric only
    ALPHANUMERIC = r'^[a-zA-Z0-9]+$'

    # Slug pattern (lowercase words separated by hyphens)
    SLUG = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'