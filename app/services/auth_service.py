from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.services.base import BaseService
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserChangePassword
from app.schemas.common import SuccessResponseSchema
from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)


class AuthService(BaseService):
    """Authentication service using UserService for user operations"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create user using UserService - errors handled automatically"""
        self.logger.info(f"Creating user with email: {user_data.email}")
        
        # Validations using BaseService methods (will raise ValidationError automatically)
        email = self.validate_email_format(user_data.email)
        username = self.validate_username(user_data.username)
        self.validate_password_strength(user_data.password)
        
        
        # Check uniqueness using BaseService method
        self.check_resource_not_exist_or_raise_duplicate(
            lambda: self.user_repository.exists_by_email(email),
            "User",
            "email",
            email
        )
        self.check_resource_not_exist_or_raise_duplicate(
            lambda: self.user_repository.exists_by_username(username),
            "User",
            "username",
            username
        )
        
        # Create user using transaction
        def create_operation():
            user_dict = self._prepare_user_data(user_data, email, username)
            db_user = self.user_repository.create(user_dict)
            self.logger.info(f"User created successfully with ID: {db_user.id}")
            return db_user
        
        db_user = self.execute_operation_within_transaction(create_operation)
        return UserResponse.model_validate(db_user)
    
    def authenticate_user(self, login_data: UserLogin) -> UserResponse:
        """Authenticate user with enhanced validation"""
        self.logger.info(f"Authenticating user with email: {login_data.email}")
        
        # Validate email format first
        email = self.validate_email_format(login_data.email)
        
        # Get user using UserService (which has validation built-in)
        try:
            user = self.user_service.get_user_by_email(email)
            # Convert back to model for password verification
        except Exception as e:
            self.logger.warning(f"User not found during authentication: {email}")
            raise AuthenticationError("Invalid email or password", field="email")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            self.logger.warning(f"Invalid password for user: {email}")
            raise AuthenticationError("Invalid email or password", field="password")
        
        # Check active status
        if not user.is_active:
            self.logger.warning(f"Inactive user attempted login: {email}")
            raise AuthorizationError(
                "Your account has been deactivated",
                suggestions=["Contact administrator to reactivate your account"]
            )
        
        self.logger.info(f"User authenticated successfully: {email}")
        return user
    
    def change_password(self, password_data: UserChangePassword) -> SuccessResponseSchema:
        """Change user password with validation"""
        user_id = password_data.id
        new_password = password_data.new_password
        old_password = password_data.old_password
        self.logger.info(f"Changing password for user {user_id}")
        
        # Validate user ID
        valid_user_id = self.validate_id_parameter(user_id, "user_id")
        
        # Validate new password strength
        self.validate_password_strength(new_password, "new_password")
        
        # Get user using UserService (which has validation built-in)
        self.user_service.get_user_by_id(valid_user_id)
        # Get the actual model for password verification
        user = self.user_repository.get(valid_user_id)
        
        # Verify current password
        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect", field="current_password")
        
        # Check if new password is different from current
        if verify_password(new_password, user.hashed_password):
            raise ValidationError(
                field="new_password",
                message="New password must be different from current password",
                constraint="different_from_current"
            )
        
        # Update password using transaction
        def update_operation():
            update_data = {
                "hashed_password": get_password_hash(new_password)
            }
            update_data = self.prepare_audit_fields(update_data, is_update=True)
            
            self.user_repository.update(user, update_data)
            self.logger.info(f"Password changed successfully for user {valid_user_id}")
            return SuccessResponseSchema(message="Password updated successfully")
        
        return self.execute_operation_within_transaction(update_operation)
    
    
    def _prepare_user_data(self, user_data: UserCreate, email: str = None, username: str = None) -> Dict[str, Any]:
        """Prepare user data for creation with normalized values"""
        user_dict = user_data.model_dump()
        
        # Use normalized values if provided
        if email:
            user_dict["email"] = email
        if username:
            user_dict["username"] = username
        
        # Hash password
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        user_dict["is_active"] = True
        
        # Clean data using BaseService method
        user_dict = self.clean_string_data(user_dict, ["email", "username", "full_name"])
        
        # Add audit fields
        user_dict = self.prepare_audit_fields(user_dict)
        
        return user_dict