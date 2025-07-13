class ValidationMessages:
    """Standard validation messages - facilitates internationalization"""
    
    # General messages
    REQUIRED_FIELD = "'{field}' is required"
    INVALID_TYPE = "'{field}' must be {expected_type}"
    INVALID_FORMAT = "{field} format is invalid"
    
    # String length messages
    MIN_LENGTH = "'{field}' must be at least {min_length} characters"
    MAX_LENGTH = "'{field}' cannot exceed {max_length} characters"
    EMPTY_VALUE = "'{field}' cannot be empty"
    
    # Specific validations
    EMAIL_REQUIRED = "Email is required"
    EMAIL_INVALID_FORMAT = "Email format is invalid"
    
    USERNAME_REQUIRED = "Username is required"
    USERNAME_INVALID_FORMAT = "Username must be 3-50 alphanumeric characters or underscore"
    
    PASSWORD_REQUIRED = "Password is required"
    PASSWORD_REQUIREMENTS = "Password must contain {requirements}"
    
    # Helper methods to format messages
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """Format message with parameters"""
        return template.format(**kwargs)
    
    @staticmethod
    def get_min_length_message(field: str, min_length: int) -> str:
        return ValidationMessages.format_message(
            ValidationMessages.MIN_LENGTH, 
            field=field, 
            min_length=min_length
        )
    
    @staticmethod
    def get_max_length_message(field: str, max_length: int) -> str:
        return ValidationMessages.format_message(
            ValidationMessages.MAX_LENGTH, 
            field=field, 
            max_length=max_length
        )
    
    @staticmethod
    def get_required_message(field: str) -> str:
        return ValidationMessages.format_message(
            ValidationMessages.REQUIRED_FIELD, 
            field=field
        )


class ErrorMessages:
    """Standard error messages for business logic"""
    
    # Authentication
    INVALID_CREDENTIALS = "Invalid credentials"
    USER_NOT_FOUND = "User not found"
    ACCOUNT_INACTIVE = "Account is inactive"
    ACCESS_DENIED = "Access denied"
    
    # Resources
    RESOURCE_NOT_FOUND = "{resource_type} not found"
    RESOURCE_DUPLICATE = "{resource_type} with {field} '{value}' already exists"
    RESOURCE_LOCKED = "{resource_type} is locked"
    
    # System
    DATABASE_ERROR = "Error processing request"
    EXTERNAL_SERVICE_ERROR = "External service unavailable"
    INTERNAL_ERROR = "Internal server error"
    
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        return template.format(**kwargs)


class SuggestionMessages:
    """Standard suggestions for error resolution"""
    
    # General suggestions
    TRY_AGAIN = "Try again"
    CONTACT_SUPPORT = "Contact support if the problem persists"
    CHECK_PERMISSIONS = "Check your permissions"
    CONTACT_ADMIN = "Contact the administrator"
    
    # Type-specific suggestions
    VERIFY_EMAIL_FORMAT = "Verify that the email format is correct"
    USE_DIFFERENT_EMAIL = "Use a different email"
    USE_DIFFERENT_USERNAME = "Use a different username"
    CHECK_PASSWORD_REQUIREMENTS = "Check password requirements"
    VERIFY_RESOURCE_ID = "Verify that the {resource_type} ID is correct"
    
    @staticmethod
    def get_verify_id_suggestion(resource_type: str) -> str:
        return SuggestionMessages.VERIFY_RESOURCE_ID.format(
            resource_type=resource_type.lower()
        )