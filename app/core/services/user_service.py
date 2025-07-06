from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.core.security import get_password_hash, verify_password
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserWithTasksResponse,
    UserLogin,
    UserChangePassword,
    UserPaginatedResponse,
    UserFilters,
    UserBulkUpdate,
)

from app.utils.exceptions import (
    InvalidCredentialsError, 
    UserAlreadyExistsError, 
    UserInactiveError, 
    UserNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class UserService:
    """
    Service layer for user-related business logic.
    Handles user operations, authentication, and validation using Pydantic schemas.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

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

    def get_user_by_id(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        logger.debug(f"Fetching user with ID: {user_id}")
        
        user = self.user_repository.get(user_id)
        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return UserResponse.model_validate(user)

    def get_user_by_email(self, email: str) -> UserResponse:
        """Get user by email."""
        logger.debug(f"Fetching user with email: {email}")
        
        user = self.user_repository.get_by_email(email)
        if not user:
            logger.warning(f"User with email {email} not found")
            raise UserNotFoundError(f"User with email {email} not found")
        
        return UserResponse.model_validate(user)

    def get_user_by_username(self, username: str) -> UserResponse:
        """Get user by username."""
        logger.debug(f"Fetching user with username: {username}")
        
        user = self.user_repository.get_by_username(username)
        if not user:
            logger.warning(f"User with username {username} not found")
            raise UserNotFoundError(f"User with username {username} not found")
        
        return UserResponse.model_validate(user)

    def get_user_with_tasks(self, user_id: int) -> UserWithTasksResponse:
        """Get user with their tasks."""
        logger.debug(f"Fetching user with tasks for ID: {user_id}")
        
        user = self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return UserWithTasksResponse.model_validate(user)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination."""
        self._validate_pagination_params(skip, limit)
        
        users = self.user_repository.get_multi(skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]

    def get_users_with_pagination(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        filters: Optional[UserFilters] = None
    ) -> UserPaginatedResponse:
        """Get users with pagination and optional filters."""
        self._validate_pagination_params(skip, limit)
        
        filter_dict = filters.model_dump(exclude_none=True) if filters else {}
        
        try:
            users, total = self.user_repository.get_with_pagination(
                skip=skip, 
                limit=limit, 
                **filter_dict
            )
            
            user_responses = [UserResponse.model_validate(user) for user in users]
            
            return UserPaginatedResponse(
                users=user_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_next=skip + limit < total,
                has_previous=skip > 0
            )
        except Exception as e:
            logger.error(f"Error fetching paginated users: {str(e)}")
            raise DatabaseError(f"Failed to fetch users: {str(e)}")


    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user information."""
        logger.info(f"Updating user with ID: {user_id}")
        
        # Get existing user
        existing_user = self._get_user_by_id_or_raise(user_id)
        
        # Convert to dict, excluding None values
        update_dict = user_data.model_dump(exclude_none=True)
        
        # Check for conflicts
        self._check_update_conflicts(user_id, update_dict)
        
        # Prepare update data
        update_dict = self._prepare_user_data_for_update(update_dict)
        
        try:
            # Update user in database
            updated_user = self.user_repository.update(existing_user, update_dict)
            logger.info(f"User {user_id} updated successfully")
            return UserResponse.model_validate(updated_user)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: int) -> UserResponse:
        """Soft delete a user."""
        logger.info(f"Deleting user with ID: {user_id}")
        
        # Check if user exists
        self._get_user_by_id_or_raise(user_id)
        
        try:
            # Soft delete user
            deleted_user = self.user_repository.soft_delete(user_id)
            if not deleted_user:
                raise DatabaseError(f"Could not delete user with ID {user_id}")
            
            logger.info(f"User {user_id} deleted successfully")
            return UserResponse.model_validate(deleted_user)
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete user: {str(e)}")


    def authenticate_user(self, login_data: UserLogin) -> UserResponse:
        """Authenticate user by email and password."""
        logger.info(f"Authenticating user with email: {login_data.email}")
        
        # Get user by email
        user = self.user_repository.get_by_email(login_data.email)
        if not user:
            logger.warning(f"Authentication failed - user not found: {login_data.email}")
            raise InvalidCredentialsError("Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Authentication failed - invalid password: {login_data.email}")
            raise InvalidCredentialsError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication failed - inactive user: {login_data.email}")
            raise UserInactiveError("User account is inactive")
        
        logger.info(f"User authenticated successfully: {login_data.email}")
        
        # Return authentication response
        user_response = UserResponse.model_validate(user)
        
        return user_response


    def change_password(self, user_id:int,  user_data: UserChangePassword) -> UserResponse:
        old_password = user_data.old_password
        new_password = user_data.new_password

        
        """Change user password after verifying old password."""
        logger.info(f"Changing password for user {user_id}")
        
        # Get user
        user = self._get_user_by_id_or_raise(user_id)
        
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            logger.warning(f"Password change failed - incorrect old password for user {user_id}")
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Update password
        update_data = {
            'hashed_password': get_password_hash(new_password),
            'updated_at': datetime.now(timezone.utc)
        }
        
        try:
            updated_user = self.user_repository.update(user, update_data)
            logger.info(f"Password changed successfully for user {user_id}")
            return UserResponse.model_validate(updated_user)
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to change password: {str(e)}")

    def bulk_update_users(self, bulk_data: UserBulkUpdate) -> int:
        """Bulk update multiple users."""
        logger.info(f"Bulk updating {len(bulk_data.user_ids)} users")
        
        # Prepare updates
        updates = []
        update_dict = bulk_data.update_data.model_dump(exclude_none=True)
        
        for user_id in bulk_data.user_ids:
            user_update = {'id': user_id, **update_dict}
            user_update['updated_at'] = datetime.now(timezone.utc)
            
            # Hash password if provided
            if 'password' in user_update:
                user_update['hashed_password'] = get_password_hash(user_update.pop('password'))
            
            updates.append(user_update)
        
        try:
            updated_count = self.user_repository.bulk_update(updates)
            logger.info(f"Bulk update completed: {updated_count} users updated")
            return updated_count
        except Exception as e:
            logger.error(f"Error in bulk update: {str(e)}")
            raise DatabaseError(f"Failed to bulk update users: {str(e)}")

    def get_user_count(self, filters: Optional[UserFilters] = None) -> int:
        """Get total count of users matching optional filters."""
        filter_dict = filters.model_dump(exclude_none=True) if filters else {}
        return self.user_repository.count(**filter_dict)

    # Utility methods
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists by ID."""
        return self.user_repository.exists(user_id)

    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email exists."""
        return self.user_repository.exists_by_email(email, exclude_id)

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username exists."""
        return self.user_repository.exists_by_username(username, exclude_id)

    # Private helper methods
    def _get_user_by_id_or_raise(self, user_id: int) -> User:
        """Get user by ID or raise exception if not found."""
        user = self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user
    
    def _get_user_by_email_or_raise(self, user_email: str) -> User:
        """Get user by ID or raise exception if not found."""
        user = self.user_repository.get_by_email(user_email)
        if not user:
            raise UserNotFoundError(f"User with email {user_email} not found")
        return user

    def _check_user_uniqueness(self, email: str, username: str) -> None:
        """Check if email and username are unique."""
        if self.user_repository.exists_by_email(email):
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        
        if self.user_repository.exists_by_username(username):
            raise UserAlreadyExistsError(f"User with username {username} already exists")

    def _check_update_conflicts(self, user_id: int, update_dict: Dict[str, Any]) -> None:
        """Check for email/username conflicts during update."""
        if 'email' in update_dict:
            if self.user_repository.exists_by_email(update_dict['email'], exclude_id=user_id):
                raise UserAlreadyExistsError(f"User with email {update_dict['email']} already exists")
        
        if 'username' in update_dict:
            if self.user_repository.exists_by_username(update_dict['username'], exclude_id=user_id):
                raise UserAlreadyExistsError(f"User with username {update_dict['username']} already exists")

    def _prepare_user_data_for_creation(self, user_data: UserCreate) -> Dict[str, Any]:
        """Prepare user data dictionary for database creation."""
        user_dict = user_data.model_dump()
        user_dict['hashed_password'] = get_password_hash(user_dict.pop('password'))
        user_dict['is_active'] = True
        user_dict['created_at'] = datetime.now(timezone.utc)
        user_dict['updated_at'] = datetime.now(timezone.utc)
        return user_dict

    def _prepare_user_data_for_update(self, update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare user data dictionary for database update."""
        # Hash password if provided
        if 'password' in update_dict:
            update_dict['hashed_password'] = get_password_hash(update_dict.pop('password'))
        
        # Update timestamp
        update_dict['updated_at'] = datetime.now(timezone.utc)
        
        return update_dict

    def _validate_pagination_params(self, skip: int, limit: int) -> None:
        """Validate pagination parameters."""
        if skip < 0:
            raise ValueError("Skip parameter must be non-negative")
        if limit <= 0:
            raise ValueError("Limit parameter must be positive")
        if limit > 1000:  # Prevent very large requests
            raise ValueError("Limit parameter cannot exceed 1000")