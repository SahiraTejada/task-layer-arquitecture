import re
from typing import List, Optional, Any, Dict, Union
from app.core.exceptions import ValidationError, ValidationErrorCollector
from app.core.messages import ValidationMessages


class Validators:
    """IMPROVEMENT 4: Validators with strong typing and centralized messages"""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_]{3,50}$'
    
    @staticmethod
    def validate_email(email: Optional[str], field: str = "email") -> str:
        """
        Validate email and return it normalized.
        
        Args:
            email: Email to validate (can be None)
            field: Field name for errors
            
        Returns:
            str: Normalized email (lowercase, stripped)
            
        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError(
                field=field,
                message=ValidationMessages.EMAIL_REQUIRED,
                expected_type="string",
                constraint="required"
            )
        
        email = email.strip().lower()
        if not re.match(Validators.EMAIL_PATTERN, email):
            raise ValidationError(
                field=field,
                message=ValidationMessages.EMAIL_INVALID_FORMAT,
                invalid_value=email,
                constraint="email_format",
                expected_type="email"
            )
        return email
    
    @staticmethod
    def validate_password(password: Optional[str], field: str = "password") -> None:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            field: Field name for errors
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not password:
            raise ValidationError(
                field=field,
                message=ValidationMessages.PASSWORD_REQUIRED,
                constraint="required"
            )
        
        issues = []
        if len(password) < 8: 
            issues.append("at least 8 characters")
        # if not any(c.isupper() for c in password): 
        #     issues.append("one uppercase letter")
        # if not any(c.islower() for c in password): 
        #     issues.append("one lowercase letter") 
        # if not any(c.isdigit() for c in password): 
        #     issues.append("one number")
        # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): 
        #     issues.append("one special character")
        
        if issues:
            message = ValidationMessages.format_message(
                ValidationMessages.PASSWORD_REQUIREMENTS,
                requirements=", ".join(issues)
            )
            raise ValidationError(
                field=field,
                message=message,
                constraint="password_strength"
            )
    
    @staticmethod
    def validate_username(username: Optional[str], field: str = "username") -> str:
        """
        Validate username and return it normalized.
        
        Args:
            username: Username to validate
            field: Field name for errors
            
        Returns:
            str: Normalized username (lowercase, stripped)
            
        Raises:
            ValidationError: If username is invalid
        """
        if not username:
            raise ValidationError(
                field=field,
                message=ValidationMessages.USERNAME_REQUIRED,
                constraint="required"
            )
        
        username = username.strip().lower()
        if not re.match(Validators.USERNAME_PATTERN, username):
            raise ValidationError(
                field=field,
                message=ValidationMessages.USERNAME_INVALID_FORMAT,
                invalid_value=username,
                constraint="username_format",
                expected_type="alphanumeric_underscore"
            )
        return username
    
    @staticmethod
    def validate_string_length(
        value: Any, 
        field: str, 
        min_length: int = 0, 
        max_length: Optional[int] = None,
        allow_empty: bool = False
    ) -> str:
        """
        Validate string length.
        
        Args:
            value: Value to validate
            field: Field name
            min_length: Minimum length
            max_length: Maximum length (optional)
            allow_empty: Allow empty strings
            
        Returns:
            str: Validated and clean string
            
        Raises:
            ValidationError: If length is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                field=field,
                message=ValidationMessages.format_message(
                    ValidationMessages.INVALID_TYPE,
                    field=field,
                    expected_type="string"
                ),
                invalid_value=type(value).__name__,
                expected_type="string"
            )
        
        value = value.strip()
        length = len(value)
        
        if not allow_empty and length == 0:
            raise ValidationError(
                field=field,
                message=ValidationMessages.format_message(
                    ValidationMessages.EMPTY_VALUE,
                    field=field
                ),
                constraint="not_empty"
            )
        
        if length < min_length:
            raise ValidationError(
                field=field,
                message=ValidationMessages.get_min_length_message(field, min_length),
                invalid_value=length,
                constraint=f"min_length_{min_length}"
            )
        
        if max_length and length > max_length:
            raise ValidationError(
                field=field,
                message=ValidationMessages.get_max_length_message(field, max_length),
                invalid_value=length,
                constraint=f"max_length_{max_length}"
            )
        
        return value
    
    @staticmethod
    def validate_user_data_bulk(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        IMPROVEMENT 2: Validate user data with improved handling of multiple errors.
        
        Args:
            data: User data to validate
            
        Returns:
            dict: Validated and normalized data
            
        Raises:
            ValidationError: With all accumulated errors
        """
        collector = ValidationErrorCollector()
        validated_data = {}
        
        # Email
        try:
            validated_data['email'] = Validators.validate_email(data.get('email'))
        except ValidationError as e:
            # IMPROVEMENT 2: Use add_validation_error to handle multiple errors correctly
            collector.add_validation_error(e)
        
        # Username
        try:
            validated_data['username'] = Validators.validate_username(data.get('username'))
        except ValidationError as e:
            collector.add_validation_error(e)
        
        # Password
        try:
            Validators.validate_password(data.get('password'))
        except ValidationError as e:
            collector.add_validation_error(e)
        
        # Full name (optional)
        if data.get('full_name'):
            try:
                validated_data['full_name'] = Validators.validate_string_length(
                    data['full_name'], 'full_name', 2, 100
                )
            except ValidationError as e:
                collector.add_validation_error(e)
        
        # Raise if there are accumulated errors
        collector.raise_if_errors()
        
        return validated_data