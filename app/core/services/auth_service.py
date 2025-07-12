from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.core.security import get_password_hash, verify_password
from app.core.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.common import SuccessResponseSchema
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserChangePassword,
)

from app.utils.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserInactiveError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service layer for user-related business logic.
    Handles user operations, authentication, and validation using Pydantic schemas.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user with validation and password hashing.

        Args:
            user_data: User creation data from Pydantic schema

        Returns:
            Created user response schema

        Raises:
            UserAlreadyExistsError: If email or username already exists
        """
        logger.info(f"Creating user with email: {user_data.email}")

        # Check for existing users
        self._check_user_uniqueness(user_data.email, user_data.username)

        # Prepare user data for database
        user_dict = self._prepare_user_data_for_creation(user_data)

        try:
            # Create user in database
            db_user = self.user_repository.create(user_dict)
            logger.info(f"User created successfully with ID: {db_user.id}")
            return UserResponse.model_validate(db_user)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseError(f"Failed to create user: {str(e)}")

    def authenticate_user(self, login_data: UserLogin) -> UserResponse:
        """Authenticate user by email and password."""
        logger.info(f"Authenticating user with email: {login_data.email}")

        # Get user by email
        user = self.user_repository.get_by_email(login_data.email)
        if not user:
            logger.warning(
                f"Authentication failed - user not found: {login_data.email}"
            )
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(
                f"Authentication failed - invalid password: {login_data.email}"
            )
            raise InvalidCredentialsError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication failed - inactive user: {login_data.email}")
            raise UserInactiveError("User account is inactive")

        logger.info(f"User authenticated successfully: {login_data.email}")

        # Return authentication response
        user_response = UserResponse.model_validate(user)

        return user_response

    def change_password(
        self,  user_data: UserChangePassword
    ) -> SuccessResponseSchema:
        user_id= user_data.id
        old_password = user_data.old_password
        new_password = user_data.new_password

        """Change user password after verifying old password."""
        logger.info(f"Changing password for user {user_id}")

        # Get user
        user = self.user_service._get_user_by_id_or_raise(user_id)

        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            logger.warning(
                f"Password change failed - incorrect old password for user {user_id}"
            )
            raise InvalidCredentialsError("Current password is incorrect")

        # Update password
        update_data = {
            "hashed_password": get_password_hash(new_password),
            "updated_at": datetime.now(timezone.utc),
        }

        try:
            self.user_repository.update(user, update_data)
            logger.info(f"Password changed successfully for user {user_id}")
            return SuccessResponseSchema(
                message="Password changed successfully",
            )
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to change password: {str(e)}")

    def _check_user_uniqueness(self, email: str, username: str) -> None:
        """Check if email and username are unique."""
        if self.user_repository.exists_by_email(email):
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        if self.user_repository.exists_by_username(username):
            raise UserAlreadyExistsError(
                f"User with username {username} already exists"
            )

    def _prepare_user_data_for_creation(self, user_data: UserCreate) -> Dict[str, Any]:
        """Prepare user data dictionary for database creation."""
        user_dict = user_data.model_dump()
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        user_dict["is_active"] = True
        user_dict["created_at"] = datetime.now(timezone.utc)
        user_dict["updated_at"] = datetime.now(timezone.utc)
        return user_dict
