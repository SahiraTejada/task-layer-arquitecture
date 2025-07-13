class ValidationMessages:
    """
    Standard validation messages for consistent user experience.
    
    These messages are designed to be:
    - User-friendly and non-technical
    - Actionable (tell user what to do)
    - Consistent across the application
    - Easy to internationalize
    """
    
    # General validation messages
    REQUIRED_FIELD = "'{field}' is required"
    INVALID_TYPE = "'{field}' must be {expected_type}"
    INVALID_FORMAT = "'{field}' format is invalid"
    
    # String validation messages
    MIN_LENGTH = "'{field}' must be at least {min_length} characters"
    MAX_LENGTH = "'{field}' cannot exceed {max_length} characters"
    EMPTY_VALUE = "'{field}' cannot be empty"
    
    # Specific field validation messages
    EMAIL_REQUIRED = "Email is required"
    EMAIL_INVALID_FORMAT = "Please provide a valid email address"
    
    USERNAME_REQUIRED = "Username is required"
    USERNAME_INVALID_FORMAT = "Username must be 3-50 characters using letters, numbers, and underscores only"
    
    PASSWORD_REQUIRED = "Password is required"
    PASSWORD_REQUIREMENTS = "Password must contain at least 8 characters with uppercase, lowercase, number, and special character"
    
    # Number validation messages
    NUMBER_TOO_SMALL = "'{field}' must be at least {min_value}"
    NUMBER_TOO_LARGE = "'{field}' cannot exceed {max_value}"
    NUMBER_INVALID = "'{field}' must be a valid number"
    
    # Date validation messages
    DATE_INVALID = "'{field}' must be a valid date"
    DATE_TOO_EARLY = "'{field}' cannot be earlier than {min_date}"
    DATE_TOO_LATE = "'{field}' cannot be later than {max_date}"
    
    # Choice validation messages
    INVALID_CHOICE = "'{field}' must be one of: {choices}"
    
    # Helper methods for dynamic message generation
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """Format message template with provided parameters"""
        return template.format(**kwargs)
    
    @staticmethod
    def get_min_length_message(field: str, min_length: int) -> str:
        """Get formatted minimum length message"""
        return ValidationMessages.format_message(
            ValidationMessages.MIN_LENGTH, 
            field=field, 
            min_length=min_length
        )
    
    @staticmethod
    def get_max_length_message(field: str, max_length: int) -> str:
        """Get formatted maximum length message"""
        return ValidationMessages.format_message(
            ValidationMessages.MAX_LENGTH, 
            field=field, 
            max_length=max_length
        )
    
    @staticmethod
    def get_required_message(field: str) -> str:
        """Get formatted required field message"""
        return ValidationMessages.format_message(
            ValidationMessages.REQUIRED_FIELD, 
            field=field
        )
    
    @staticmethod
    def get_invalid_choice_message(field: str, choices: list) -> str:
        """Get formatted invalid choice message"""
        choices_str = ", ".join(str(choice) for choice in choices)
        return ValidationMessages.format_message(
            ValidationMessages.INVALID_CHOICE,
            field=field,
            choices=choices_str
        )


class ErrorMessages:
    """
    Standard error messages for business logic and system errors.
    
    These messages are designed to be:
    - Professional and clear
    - Non-revealing of internal system details
    - Helpful for troubleshooting
    - Consistent across error types
    """
    
    # Authentication and Authorization
    INVALID_CREDENTIALS = "Invalid email or password"
    USER_NOT_FOUND = "User account not found"
    ACCOUNT_INACTIVE = "Your account has been deactivated"
    ACCOUNT_LOCKED = "Your account has been temporarily locked"
    ACCESS_DENIED = "You don't have permission to access this resource"
    TOKEN_EXPIRED = "Your session has expired, please log in again"
    TOKEN_INVALID = "Invalid authentication token"
    
    # Resource management
    RESOURCE_NOT_FOUND = "{resource_type} not found"
    RESOURCE_DUPLICATE = "A {resource_type} with this {field} already exists"
    RESOURCE_LOCKED = "{resource_type} is currently locked by another user"
    RESOURCE_DELETED = "{resource_type} has been deleted"
    
    # System errors
    DATABASE_ERROR = "A system error occurred while processing your request"
    EXTERNAL_SERVICE_ERROR = "External service is temporarily unavailable"
    INTERNAL_ERROR = "An unexpected error occurred"
    NETWORK_ERROR = "Network connection error"
    TIMEOUT_ERROR = "Request timed out, please try again"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "Operation violates business rules"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions for this operation"
    OPERATION_NOT_ALLOWED = "This operation is not allowed in the current state"
    QUOTA_EXCEEDED = "You have exceeded your usage quota"
    RATE_LIMIT_EXCEEDED = "Too many requests, please slow down"
    
    # Data validation errors
    DATA_INTEGRITY_ERROR = "Data integrity constraint violation"
    FOREIGN_KEY_ERROR = "Referenced resource does not exist"
    UNIQUE_CONSTRAINT_ERROR = "A record with this information already exists"
    
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """Format error message template with provided parameters"""
        return template.format(**kwargs)
    
    @staticmethod
    def get_resource_not_found_message(resource_type: str) -> str:
        """Get formatted resource not found message"""
        return ErrorMessages.format_message(
            ErrorMessages.RESOURCE_NOT_FOUND,
            resource_type=resource_type
        )
    
    @staticmethod
    def get_resource_duplicate_message(resource_type: str, field: str) -> str:
        """Get formatted resource duplicate message"""
        return ErrorMessages.format_message(
            ErrorMessages.RESOURCE_DUPLICATE,
            resource_type=resource_type,
            field=field
        )


class SuggestionMessages:
    """
    Standard suggestion messages to help users resolve errors.
    
    These suggestions are:
    - Actionable and specific
    - Non-technical for end users
    - Helpful for self-service resolution
    - Escalation paths when needed
    """
    
    # General suggestions
    TRY_AGAIN = "Please try again"
    TRY_AGAIN_LATER = "Please try again in a few minutes"
    CONTACT_SUPPORT = "Contact support if the problem persists"
    CHECK_DOCUMENTATION = "Check the API documentation for more information"
    
    # Authentication suggestions
    CHECK_CREDENTIALS = "Please check your email and password"
    USE_FORGOT_PASSWORD = "Use the 'Forgot Password' option if you don't remember your credentials"
    CONTACT_ADMIN = "Contact your administrator for account assistance"
    LOGIN_AGAIN = "Please log in again to continue"
    
    # Validation suggestions
    CHECK_REQUIRED_FIELDS = "Make sure all required fields are filled"
    CHECK_FIELD_FORMAT = "Check that {field} is in the correct format"
    VERIFY_EMAIL_FORMAT = "Make sure the email includes @ symbol and a valid domain"
    CHECK_PASSWORD_REQUIREMENTS = "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
    USE_DIFFERENT_VALUE = "Please use a different value for {field}"
    
    # Resource suggestions
    VERIFY_RESOURCE_ID = "Verify that the {resource_type} ID is correct"
    CHECK_RESOURCE_EXISTS = "Make sure the {resource_type} exists before referencing it"
    USE_UNIQUE_VALUES = "Use unique values for fields that must be unique"
    
    # System suggestions
    CHECK_INTERNET_CONNECTION = "Check your internet connection"
    REFRESH_PAGE = "Try refreshing the page"
    CLEAR_CACHE = "Try clearing your browser cache and cookies"
    USE_DIFFERENT_BROWSER = "Try using a different browser"
    
    # Business logic suggestions
    CHECK_PERMISSIONS = "Check that you have the necessary permissions"
    REVIEW_BUSINESS_RULES = "Review the business rules for this operation"
    CONTACT_ADMIN_FOR_LIMITS = "Contact your administrator to increase limits"
    
    @staticmethod
    def get_verify_id_suggestion(resource_type: str) -> str:
        """Get formatted resource ID verification suggestion"""
        return SuggestionMessages.VERIFY_RESOURCE_ID.format(
            resource_type=resource_type.lower()
        )
    
    @staticmethod
    def get_check_format_suggestion(field: str) -> str:
        """Get formatted field format checking suggestion"""
        return SuggestionMessages.CHECK_FIELD_FORMAT.format(field=field)
    
    @staticmethod
    def get_use_different_value_suggestion(field: str) -> str:
        """Get formatted different value suggestion"""
        return SuggestionMessages.USE_DIFFERENT_VALUE.format(field=field)


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
