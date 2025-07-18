from sqlalchemy.orm import Session
import logging

from app.core.security import verify_password
from app.services.user_service import UserService
from app.schemas.common import SuccessResponseSchema
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserChangePassword,
    UserUpdate,
)
from app.utils.exceptions import (
    InvalidCredentialsError,
    UserInactiveError,
    AppValidationError,
    ServiceError,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service that handles user registration, login, and password management.
    
    This service focuses on authentication logic and delegates user management
    to UserService, maintaining separation of concerns.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user account.
        
        Args:
            user_data: User registration data
            
        Returns:
            UserResponse: Created user data
            
        Raises:
            UserAlreadyExistsError: Email or username already exists
            AppValidationError: Invalid user data
        """
        try:
            self.logger.info(f"Registering new user with email: {user_data.email}")
            
            # UserService.create() handles all validation, uniqueness checks, and password hashing
            user_response = self.user_service.create(user_data)
            
            self.logger.info(f"User registered successfully: {user_data.email}")
            return user_response
            
        except Exception as e:
            self.logger.error(f"Error registering user {user_data.email}: {str(e)}")
            raise

    def authenticate_user(self, login_data: UserLogin) -> UserResponse:
        """
        Authenticate user with email and password.
        
        Args:
            login_data: User login credentials
            
        Returns:
            UserResponse: Authenticated user data
            
        Raises:
            InvalidCredentialsError: Invalid email or password
            UserInactiveError: User account is inactive
        """
        try:
            self.logger.info(f"Authenticating user with email: {login_data.email}")
            

            email = login_data.email
            password = login_data.password
            user = self.user_service.repository.get_by_email(email)
            if not user:
                raise InvalidCredentialsError("Invalid email or password")
            
            if not verify_password(password, user.hashed_password):
                self.logger.warning(f"Authentication failed - invalid password: {login_data.email}")
                raise InvalidCredentialsError("Invalid email or password")
            
            if not user.is_active:
                self.logger.warning(f"Authentication failed - inactive user: {login_data.email}")
                raise UserInactiveError("User account is inactive")
            
  
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Authentication failed - inactive user: {login_data.email}")
                raise UserInactiveError("User account is inactive")
            
            self.logger.info(f"User authenticated successfully: {login_data.email}")
            return UserResponse.model_validate(user)
            
        except (InvalidCredentialsError, UserInactiveError):
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {str(e)}")
            raise ServiceError(f"Authentication failed: {str(e)}")

    def change_password(self, password_data: UserChangePassword) -> SuccessResponseSchema:
        """
        Change user password after verifying current password.
        
        Args:
            password_data: Password change data including user ID, old and new passwords
            
        Returns:
            SuccessResponseSchema: Success confirmation
            
        Raises:
            InvalidCredentialsError: Current password is incorrect
            AppValidationError: Password validation errors
        """
        try:
            self.logger.info(f"Changing password for user {password_data.user_id}")
            
            # Validate password change data
            self._validate_password_change(password_data)
            
            # Get user using UserService (handles NotFoundError automatically)
            user = self.user_service.repository.get(password_data.user_id)
            
            
            # Verify current password
            if not verify_password(password_data.old_password, user.hashed_password):
                self.logger.warning(f"Password change failed - incorrect old password for user {password_data.user_id}")
                raise InvalidCredentialsError("Current password is incorrect")
            
            update_data = UserUpdate(password=password_data.new_password,user_id=password_data.user_id)
            
            # UserService.update() handles password hashing, validation, and error handling
            self.user_service.update(password_data.user_id, update_data)
            
            self.logger.info(f"Password changed successfully for user {password_data.user_id}")
            return SuccessResponseSchema(
                message="Password changed successfully"
            )
            
        except (InvalidCredentialsError, AppValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error changing password for user {password_data.user_id}: {str(e)}")
            raise ServiceError(f"Failed to change password: {str(e)}")

    # def reset_password(self, email: str, new_password: str) -> SuccessResponseSchema:
    #     """
    #     Reset user password (admin function or after email verification).
        
    #     Args:
    #         email: User email address
    #         new_password: New password to set
            
    #     Returns:
    #         SuccessResponseSchema: Success confirmation
    #     """
    #     try:
    #         self.logger.info(f"Resetting password for user with email: {email}")
            
    #         # Get user by email
    #         user_response = self.user_service.get_by_email(email)
            
    #         # Update password using UserService
    #         from app.schemas.user import UserUpdate
    #         update_data = UserUpdate(password=new_password)
            
    #         self.user_service.update(user_response.id, update_data)
            
    #         self.logger.info(f"Password reset successfully for user: {email}")
    #         return SuccessResponseSchema(
    #             message="Password reset successfully"
    #         )
            
    #     except Exception as e:
    #         self.logger.error(f"Error resetting password for email {email}: {str(e)}")
    #         raise ServiceError(f"Failed to reset password: {str(e)}")

    # def deactivate_user_account(self, user_id: int) -> UserResponse:
    #     """
    #     Deactivate user account (admin function).
        
    #     Args:
    #         user_id: ID of user to deactivate
            
    #     Returns:
    #         UserResponse: Updated user data
    #     """
    #     try:
    #         self.logger.info(f"Deactivating user account: {user_id}")
            
    #         # Use UserService deactivate method
    #         user_response = self.user_service.deactivate_user(user_id)
            
    #         self.logger.info(f"User account deactivated successfully: {user_id}")
    #         return user_response
            
    #     except Exception as e:
    #         self.logger.error(f"Error deactivating user {user_id}: {str(e)}")
    #         raise

    # def activate_user_account(self, user_id: int) -> UserResponse:
    #     """
    #     Activate user account (admin function).
        
    #     Args:
    #         user_id: ID of user to activate
            
    #     Returns:
    #         UserResponse: Updated user data
    #     """
    #     try:
    #         self.logger.info(f"Activating user account: {user_id}")
            
    #         # Use UserService activate method
    #         user_response = self.user_service.activate_user(user_id)
            
    #         self.logger.info(f"User account activated successfully: {user_id}")
    #         return user_response
            
    #     except Exception as e:
    #         self.logger.error(f"Error activating user {user_id}: {str(e)}")
    #         raise

    # Convenience methods for profile management
    def get_user_profile(self, user_id: int) -> UserResponse:
        """Get user profile (convenience method)."""
        return self.user_service.get_by_id(user_id)

    def update_user_profile(self, user_id: int, update_data) -> UserResponse:
        """Update user profile (convenience method)."""
        return self.user_service.update(user_id, update_data)

    # Private helper methods
    def _validate_password_change(self, password_data: UserChangePassword) -> None:
        """Validate password change data."""
        if not password_data.old_password:
            raise AppValidationError("Current password is required")
        
        if not password_data.new_password:
            raise AppValidationError("New password is required")
        
        if password_data.old_password == password_data.new_password:
            raise AppValidationError("New password must be different from current password")
        
        # Password strength validation is handled by UserService
        if len(password_data.new_password) < 8:
            raise AppValidationError("New password must be at least 8 characters long")
