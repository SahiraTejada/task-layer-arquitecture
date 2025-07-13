from abc import ABC
from sqlalchemy.orm import Session
from typing import Any, Optional, Callable, TypeVar, List, Dict
import logging
from datetime import datetime, timezone

from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError, 
    DuplicateResourceError,
    DatabaseError
)
from app.utils.validators import Validators

T = TypeVar('T')


class BaseService(ABC):
    """Base service with common validations and utilities using new exception system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # ========== VALIDATION METHODS (Using Centralized Validators) ==========
    
    def validate_required_fields(self, data: dict, required_fields: List[str]) -> None:
        """Validate that required fields are present"""
        Validators.validate_required_fields(data, required_fields)
    
    def validate_email_format(self, email: str, field: str = "email") -> str:
        """Validate and return normalized email"""
        return Validators.validate_email(email, field)
    
    def validate_password_strength(self, password: str, field: str = "password") -> None:
        """Validate password strength"""
        Validators.validate_password(password, field)
    
    def validate_username(self, username: str, field: str = "username") -> str:
        """Validate and return normalized username"""
        return Validators.validate_username(username, field)
    
    def validate_string_length(self, value: str, field: str, min_length: int = 0, 
                             max_length: Optional[int] = None) -> str:
        """Validate string length"""
        return Validators.validate_string_length(value, field, min_length, max_length)
    
    # ========== RESOURCE UTILITY METHODS ==========
    
    def get_resource_or_raise_not_found(
        self, 
        resource_id: Any, 
        get_func: Callable[[Any], Optional[T]], 
        resource_type: str = "Resource"
    ) -> T:
        """Get a resource or raise exception if not found"""
        try:
            resource = get_func(resource_id)
            if not resource:
                raise ResourceNotFoundError(resource_type, str(resource_id))
            return resource
        except (ResourceNotFoundError, ValidationError, DuplicateResourceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(f"Error getting {resource_type} {resource_id}: {str(e)}")
            raise DatabaseError(
                operation=f"get_{resource_type.lower()}",
                details={"resource_id": str(resource_id), "error": str(e)}
            )
    
    def check_resource_not_exist_or_raise_duplicate(
        self, 
        check_func: Callable[[], bool], 
        resource_type: str,
        field: str,
        value: str
    ) -> None:
        """Check that a resource doesn't exist (to avoid duplicates)"""
        try:
            if check_func():
                raise DuplicateResourceError(resource_type, field, value)
        except DuplicateResourceError:
            # Re-raise duplicate resource exceptions
            raise
        except Exception as e:
            self.logger.error(f"Error checking {resource_type} existence: {str(e)}")
            raise DatabaseError(
                operation=f"check_{resource_type.lower()}_exists",
                details={"field": field, "value": value, "error": str(e)}
            )
    
    def validate_pagination_params(self, page: int, per_page: int, max_per_page: int = 100) -> tuple[int, int]:
        """Validate and normalize pagination parameters"""
        # Validate page parameter
        if not isinstance(page, int) or page < 1:
            if isinstance(page, str) and page.isdigit():
                page = int(page)
            else:
                raise ValidationError(
                    field="page",
                    message="Page must be a positive integer",
                    invalid_value=page,
                    constraint="min_value_1",
                    expected_type="integer"
                )
        
        # Validate per_page parameter
        if not isinstance(per_page, int) or per_page < 1:
            if isinstance(per_page, str) and per_page.isdigit():
                per_page = int(per_page)
            else:
                raise ValidationError(
                    field="per_page",
                    message="Per page must be a positive integer",
                    invalid_value=per_page,
                    constraint="min_value_1",
                    expected_type="integer"
                )
        
        # Enforce maximum per_page limit
        if per_page > max_per_page:
            raise ValidationError(
                field="per_page",
                message=f"Per page cannot exceed {max_per_page}",
                invalid_value=per_page,
                constraint=f"max_value_{max_per_page}"
            )
        
        return page, per_page
    
    def validate_id_parameter(self, id_value: Any, field: str = "id") -> int:
        """Validate ID parameter"""
        if not id_value:
            raise ValidationError(
                field=field,
                message=f"{field.title()} is required",
                constraint="required"
            )
        
        try:
            id_int = int(id_value)
            if id_int <= 0:
                raise ValidationError(
                    field=field,
                    message=f"{field.title()} must be a positive integer",
                    invalid_value=id_value,
                    constraint="min_value_1"
                )
            return id_int
        except (ValueError, TypeError):
            raise ValidationError(
                field=field,
                message=f"{field.title()} must be a valid integer",
                invalid_value=id_value,
                expected_type="integer"
            )
    
    # ========== TRANSACTION METHODS ==========
    
    def commit_transaction_or_raise_error(self) -> None:
        """Commit current transaction or raise DatabaseError"""
        try:
            self.db.commit()
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction commit failed: {e}")
            raise DatabaseError(
                operation="commit_transaction",
                details={"error": str(e)}
            )
    
    def safely_rollback_transaction_without_exceptions(self) -> None:
        """Safely rollback current transaction without raising exceptions"""
        try:
            self.db.rollback()
            self.logger.debug("Transaction rolled back")
        except Exception as e:
            self.logger.error(f"Transaction rollback failed: {e}")
    
    def execute_operation_within_transaction(self, operation: Callable[[], T]) -> T:
        """Execute operation in transaction with automatic rollback on error"""
        try:
            result = operation()
            self.commit_transaction_or_raise_error()
            return result
        except Exception as e:
            self.safely_rollback_transaction_without_exceptions()
            if isinstance(e, (ValidationError, ResourceNotFoundError, DuplicateResourceError, DatabaseError)):
                raise
            # Convert unexpected exceptions to DatabaseError
            raise DatabaseError(
                operation="transaction_execution",
                details={"error": str(e)}
            )
    
    # ========== DATA CLEANING AND PREPARATION METHODS ==========
    
    def clean_string_data(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Clean text fields (trim, normalize, etc.)"""
        cleaned_data = data.copy()
        
        for field in fields:
            if field in cleaned_data and isinstance(cleaned_data[field], str):
                value = cleaned_data[field].strip()
                
                # Field-specific cleaning
                if field == "email":
                    value = value.lower()
                elif field in ["username", "slug"]:
                    value = value.lower()
                elif field in ["full_name", "name", "title"]:
                    # Capitalize each word, but preserve original if already properly formatted
                    if value and not any(c.isupper() for c in value):
                        value = value.title()
                
                cleaned_data[field] = value if value else None
        
        return cleaned_data
    
    def prepare_audit_fields(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Prepare audit fields for database operations"""
        prepared_data = data.copy()
        now = datetime.now(timezone.utc)
        
        if not is_update:
            prepared_data["created_at"] = now
        
        prepared_data["updated_at"] = now
        
        return prepared_data
    
    def sanitize_string(self, value: str, max_length: Optional[int] = None, 
                       allow_empty: bool = True) -> Optional[str]:
        """Sanitize a text string"""
        if not value or not isinstance(value, str):
            return None if allow_empty else ""
        
        # Remove extra whitespace and normalize
        sanitized = " ".join(value.split())
        
        # Remove potential XSS characters (basic sanitization)
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()
        
        return sanitized if sanitized else (None if allow_empty else "")
    
    def sanitize_input_data(self, data: Dict[str, Any], string_max_length: int = 1000) -> Dict[str, Any]:
        """Recursively sanitize input data"""
        sanitized_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitize_string(value, string_max_length)
            elif isinstance(value, dict):
                sanitized_data[key] = self.sanitize_input_data(value, string_max_length)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    self.sanitize_string(item, string_max_length) if isinstance(item, str) 
                    else item for item in value
                ]
            else:
                sanitized_data[key] = value
        
        return sanitized_data
    
    # ========== BATCH OPERATIONS ==========
    
    def bulk_validate_and_create(self, items_data: List[Dict[str, Any]], 
                                create_func: Callable[[Dict[str, Any]], T],
                                validate_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> List[T]:
        """Bulk validate and create multiple items with automatic rollback"""
        if not items_data:
            return []
        
        def batch_operation():
            created_items = []
            for i, item_data in enumerate(items_data):
                try:
                    # Optional validation step
                    if validate_func:
                        validated_data = validate_func(item_data)
                    else:
                        validated_data = item_data
                    
                    # Create item
                    created_item = create_func(validated_data)
                    created_items.append(created_item)
                    
                except Exception as e:
                    # Add context about which item failed
                    if isinstance(e, ValidationError):
                        # Add item index to error details
                        e.details = e.details or {}
                        e.details["item_index"] = i
                        e.details["total_items"] = len(items_data)
                    raise
            
            return created_items
        
        return self.execute_operation_within_transaction(batch_operation)
    
    # ========== SEARCH AND FILTER UTILITIES ==========
    
    def validate_search_params(self, search_term: Optional[str] = None, 
                             min_search_length: int = 2) -> Optional[str]:
        """Validate and sanitize search parameters"""
        if not search_term:
            return None
        
        if not isinstance(search_term, str):
            raise ValidationError(
                field="search",
                message="Search term must be a string",
                invalid_value=type(search_term).__name__,
                expected_type="string"
            )
        
        sanitized_search = self.sanitize_string(search_term)
        if not sanitized_search:
            return None
        
        if len(sanitized_search) < min_search_length:
            raise ValidationError(
                field="search",
                message=f"Search term must be at least {min_search_length} characters",
                invalid_value=sanitized_search,
                constraint=f"min_length_{min_search_length}"
            )
        
        return sanitized_search
    
    # ========== UTILITY HELPERS ==========
    
    def format_error_context(self, operation: str, **context) -> Dict[str, Any]:
        """Format error context for consistent logging and debugging"""
        return {
            "operation": operation,
            "service": self.__class__.__name__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **context
        }
    
    def log_operation(self, operation: str, success: bool = True, **context):
        """Log service operations for monitoring"""
        log_data = self.format_error_context(operation, success=success, **context)
        
        if success:
            self.logger.info(f"Operation successful: {operation}", extra=log_data)
        else:
            self.logger.warning(f"Operation failed: {operation}", extra=log_data)
    
    def validate_enum_value(self, value: Any, enum_class, field: str = "value"):
        """Validate that a value is a valid enum member"""
        if not value:
            raise ValidationError(
                field=field,
                message=f"{field.title()} is required",
                constraint="required"
            )
        
        try:
            # Try to get enum member
            if isinstance(value, str):
                return enum_class(value)
            elif isinstance(value, enum_class):
                return value
            else:
                # Try by name
                return enum_class[str(value).upper()]
        except (ValueError, KeyError):
            valid_values = [member.value for member in enum_class]
            raise ValidationError(
                field=field,
                message=f"{field.title()} must be one of: {', '.join(valid_values)}",
                invalid_value=value,
                allowed_values=valid_values,
                constraint="enum_choice"
            )