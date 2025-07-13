from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.services.base import BaseService
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate, 
    UserResponse, 
    UserWithTasksResponse,
    UserFilters,
    UserBulkUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationRequest, SuccessResponseSchema
from app.utils.exceptions import (
    UserAlreadyExistsError, 
    UserNotFoundError,
    AppValidationError,
    ServiceError,
)

logger = logging.getLogger(__name__)


class UserService(BaseService[User, UserCreate, UserUpdate, UserResponse]):
    """
    Service layer for user-related business logic.
    Handles user operations, authentication, and validation using Pydantic schemas.
    """
    
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        super().__init__(
            repository=self.user_repository,
            response_schema=UserResponse,
            entity_name="User"
        )
        self.db = db

    # Additional user-specific methods beyond base CRUD
    
    def get_by_email(self, email: str) -> UserResponse:
        """Get user by email."""
        try:
            self.logger.debug(f"Fetching user with email: {email}")
            
            user = self.user_repository.get_by_email(email)
            if not user:
                raise UserNotFoundError(f"User with email {email} not found")
            
            return UserResponse.model_validate(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise ServiceError(f"Failed to retrieve user: {str(e)}")

    def get_by_username(self, username: str) -> UserResponse:
        """Get user by username."""
        try:
            self.logger.debug(f"Fetching user with username: {username}")
            
            user = self.user_repository.get_by_username(username)
            if not user:
                raise UserNotFoundError(f"User with username {username} not found")
            
            return UserResponse.model_validate(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching user by username {username}: {str(e)}")
            raise ServiceError(f"Failed to retrieve user: {str(e)}")

    def get_with_tasks(self, user_id: int) -> UserWithTasksResponse:
        """Get user with their tasks."""
        try:
            self.logger.debug(f"Fetching user with tasks for ID: {user_id}")
            
            user = self.user_repository.get(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            return UserWithTasksResponse.model_validate(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching user with tasks {user_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve user with tasks: {str(e)}")

    def get_filtered_paginated(
        self, 
        pagination: PaginationRequest, 
        filters: Optional[UserFilters] = None
    ) -> PaginatedResponse[UserResponse]:
        """Get users with pagination and optional filters."""
        try:
            filter_dict = filters.model_dump(exclude_none=True) if filters else {}
            return super().get_paginated(pagination, **filter_dict)
            
        except Exception as e:
            self.logger.error(f"Error fetching filtered paginated users: {str(e)}")
            raise ServiceError(f"Failed to retrieve users: {str(e)}")

    def bulk_update_users(self, bulk_data: UserBulkUpdate) -> int:
        """Bulk update multiple users."""
        try:
            self.logger.info(f"Bulk updating {len(bulk_data.user_ids)} users")
            
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
            
            updated_count = self.user_repository.bulk_update(updates)
            self.logger.info(f"Bulk update completed: {updated_count} users updated")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error in bulk update: {str(e)}")
            raise ServiceError(f"Failed to bulk update users: {str(e)}")

    def activate_user(self, user_id: int) -> UserResponse:
        """Activate a user account."""
        try:
            self.logger.info(f"Activating user: {user_id}")
            
            update_data = UserUpdate(is_active=True)
            return self.update(user_id, update_data)
            
        except Exception as e:
            self.logger.error(f"Error activating user {user_id}: {str(e)}")
            raise

    def deactivate_user(self, user_id: int) -> UserResponse:
        """Deactivate a user account."""
        try:
            self.logger.info(f"Deactivating user: {user_id}")
            
            update_data = UserUpdate(is_active=False)
            return self.update(user_id, update_data)
            
        except Exception as e:
            self.logger.error(f"Error deactivating user {user_id}: {str(e)}")
            raise

    # Utility methods
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email exists."""
        return self.user_repository.exists_by_email(email, exclude_id)

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username exists."""
        return self.user_repository.exists_by_username(username, exclude_id)

    def get_active_users(self) -> List[UserResponse]:
        """Get all active users."""
        try:
            active_users = self.user_repository.get_active_users()
            return [UserResponse.model_validate(user) for user in active_users]
        except Exception as e:
            self.logger.error(f"Error fetching active users: {str(e)}")
            raise ServiceError(f"Failed to retrieve active users: {str(e)}")

    # Override base service methods for user-specific logic

    def _validate_before_create(self, create_data: UserCreate) -> None:
        """Custom validation before user creation."""
        # Check email uniqueness
        if self.email_exists(create_data.email):
            raise UserAlreadyExistsError(f"User with email {create_data.email} already exists")
        
        # Check username uniqueness
        if self.username_exists(create_data.username):
            raise UserAlreadyExistsError(f"User with username {create_data.username} already exists")
        
        # Add any additional user-specific validation here
        self._validate_password_strength(create_data.password)

    def _validate_before_update(self, entity_id: int, update_data: UserUpdate) -> None:
        """Custom validation before user update."""
        # Check email uniqueness (excluding current user)
        if hasattr(update_data, 'email') and update_data.email:
            if self.email_exists(update_data.email, exclude_id=entity_id):
                raise UserAlreadyExistsError(f"User with email {update_data.email} already exists")
        
        # Check username uniqueness (excluding current user)
        if hasattr(update_data, 'username') and update_data.username:
            if self.username_exists(update_data.username, exclude_id=entity_id):
                raise UserAlreadyExistsError(f"User with username {update_data.username} already exists")
        
        # Validate password if being updated
        if hasattr(update_data, 'password') and update_data.password:
            self._validate_password_strength(update_data.password)

    def _validate_before_delete(self, entity_id: int) -> None:
        """Custom validation before user deletion."""
        # Add any business rules for user deletion
        # For example, prevent deletion of admin users, users with active sessions, etc.
        user = self._get_entity_or_raise(entity_id)
        
        # Example: Prevent deletion of admin users
        if hasattr(user, 'is_admin') and user.is_admin:
            raise AppValidationError("Cannot delete admin users")

    def _prepare_create_data(self, create_data: UserCreate) -> Dict[str, Any]:
        """Prepare user data for creation."""
        data = super()._prepare_create_data(create_data)
        
        # Hash the password
        if 'password' in data:
            data['hashed_password'] = get_password_hash(data.pop('password'))
        
        # Set default values
        data.setdefault('is_active', True)
        
        return data

    def _prepare_update_data(self, update_data: UserUpdate) -> Dict[str, Any]:
        """Prepare user data for update."""
        data = super()._prepare_update_data(update_data)
        
        # Hash password if provided
        if 'password' in data:
            data['hashed_password'] = get_password_hash(data.pop('password'))
        
        return data

    def _validate_password_strength(self, password: str) -> None:
        """Validate password strength."""
        if len(password) < 8:
            raise AppValidationError("Password must be at least 8 characters long")
        
        # Add more password validation rules as needed
        # if not re.search(r"[A-Z]", password):
        #     raise AppValidationError("Password must contain at least one uppercase letter")
        # if not re.search(r"[a-z]", password):
        #     raise AppValidationError("Password must contain at least one lowercase letter")
        # if not re.search(r"\d", password):
        #     raise AppValidationError("Password must contain at least one digit")