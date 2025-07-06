from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.security import get_password_hash, verify_password
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.exceptions import InvalidCredentialsError, UserAlreadyExistsError, UserInactiveError, UserNotFoundError


class UserService:
    """
    Service layer for user-related business logic.
    Handles user operations, authentication, and validation.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with validation and password hashing.
        
        Args:
            user_data: User creation data from Pydantic schema
            
        Returns:
            Created user instance
            
        Raises:
            UserAlreadyExistsError: If email or username already exists
        """
        # Check if user already exists by email
        if self.user_repository.exists_by_email(user_data.email):
            raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")
        
        # Check if user already exists by username
        if self.user_repository.exists_by_username(user_data.username):
            raise UserAlreadyExistsError(f"User with username {user_data.username} already exists")
        
        # Hash the password before storing
        user_dict = user_data.model_dump()
        user_dict['hashed_password'] = get_password_hash(user_data.password)
        
        # Remove plain password from dict
        user_dict.pop('password', None)
        
        # Set default values
        user_dict['is_active'] = True
        user_dict['created_at'] = datetime.now(timezone.utc)
        user_dict['updated_at'] = datetime.now(timezone.utc)
        
        return self.user_repository.create(user_dict)

    def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    def get_user_by_email(self, email: str) -> User:
        """
        Get user by email.
        
        Args:
            email: User email to search for
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        return user

    def get_user_by_username(self, username: str) -> User:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.user_repository.get_by_username(username)
        if not user:
            raise UserNotFoundError(f"User with username {username} not found")
        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user instances
        """
        return self.user_repository.get_multi(skip=skip, limit=limit)

    def get_active_users(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active user instances
        """
        return self.user_repository.get_active_users()

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            user_id: ID of user to update
            user_data: Updated user data
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
            UserAlreadyExistsError: If email/username conflicts with existing user
        """
        # Get existing user
        existing_user = self.get_user_by_id(user_id)
        
        # Convert update data to dict
        update_dict = user_data.model_dump(exclude_unset=True)
        
        # Check for email conflicts
        if 'email' in update_dict:
            if self.user_repository.exists_by_email(update_dict['email'], exclude_id=user_id):
                raise UserAlreadyExistsError(f"User with email {update_dict['email']} already exists")
        
        # Check for username conflicts
        if 'username' in update_dict:
            if self.user_repository.exists_by_username(update_dict['username'], exclude_id=user_id):
                raise UserAlreadyExistsError(f"User with username {update_dict['username']} already exists")
        
        # Hash password if provided
        if 'password' in update_dict:
            update_dict['hashed_password'] = get_password_hash(update_dict['password'])
            update_dict.pop('password')
        
        # Update timestamp
        update_dict['updated_at'] = datetime.now(timezone.utc)
        
        return self.user_repository.update(existing_user, update_dict)

    def delete_user(self, user_id: int) -> User:
        """
        Soft delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            Deleted user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.get_user_by_id(user_id)
        deleted_user = self.user_repository.soft_delete(user_id)
        if not deleted_user:
            raise UserNotFoundError(f"Could not delete user with ID {user_id}")
        return deleted_user

    def activate_user(self, user_id: int) -> User:
        """
        Activate a user account.
        
        Args:
            user_id: ID of user to activate
            
        Returns:
            Activated user instance
        """
        user = self.get_user_by_id(user_id)
        update_data = {'is_active': True, 'updated_at': datetime.now(timezone.utc)}
        return self.user_repository.update(user, update_data)

    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of user to deactivate
            
        Returns:
            Deactivated user instance
        """
        user = self.get_user_by_id(user_id)
        update_data = {'is_active': False, 'updated_at': datetime.now(timezone.utc)}
        return self.user_repository.update(user, update_data)

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user by email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Authenticated user instance
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserInactiveError: If user account is inactive
        """
        try:
            user = self.get_user_by_email(email)
        except UserNotFoundError:
            raise InvalidCredentialsError("Invalid email or password")
        
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        
        if not user.is_active:
            raise UserInactiveError("User account is inactive")
        
        return user

    def change_password(self, user_id: int, old_password: str, new_password: str) -> User:
        """
        Change user password after verifying old password.
        
        Args:
            user_id: ID of user
            old_password: Current password
            new_password: New password
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If old password is incorrect
        """
        user = self.get_user_by_id(user_id)
        
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")
        
        update_data = {
            'hashed_password': get_password_hash(new_password),
            'updated_at': datetime.now(timezone.utc)
        }
        
        return self.user_repository.update(user, update_data)

    def get_users_with_pagination(self, skip: int = 0, limit: int = 10, **filters) -> Tuple[List[User], int]:
        """
        Get users with pagination and optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filters to apply
            
        Returns:
            Tuple of (users list, total count)
        """
        return self.user_repository.get_with_pagination(skip=skip, limit=limit, **filters)

    def search_users(self, query: str, skip: int = 0, limit: int = 10) -> List[User]:
        """
        Search users by username or email.
        
        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching users
        """
        # This would require a more complex query with OR conditions
        # For now, we'll search by username and email separately
        users_by_username = self.user_repository.get_multi(skip=skip, limit=limit, username=query)
        users_by_email = self.user_repository.get_multi(skip=skip, limit=limit, email=query)
        
        # Combine and deduplicate
        all_users = users_by_username + users_by_email
        seen = set()
        unique_users = []
        for user in all_users:
            if user.id not in seen:
                seen.add(user.id)
                unique_users.append(user)
        
        return unique_users[:limit]

    def get_user_count(self, **filters) -> int:
        """
        Get total count of users matching optional filters.
        
        Args:
            **filters: Filters to apply
            
        Returns:
            Total count of matching users
        """
        return self.user_repository.count(**filters)

    def bulk_update_users(self, updates: List[Dict[str, Any]]) -> int:
        """
        Bulk update multiple users.
        
        Args:
            updates: List of update dictionaries, each containing 'id' and fields to update
            
        Returns:
            Number of users updated
        """
        # Add updated_at timestamp to each update
        for update in updates:
            if 'id' in update:
                update['updated_at'] = datetime.now(timezone.utc)
                
                # Hash password if provided
                if 'password' in update:
                    update['hashed_password'] = get_password_hash(update['password'])
                    update.pop('password')
        
        return self.user_repository.bulk_update(updates)

    def user_exists(self, user_id: int) -> bool:
        """
        Check if user exists by ID.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user exists, False otherwise
        """
        return self.user_repository.exists(user_id)

    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if email exists.
        
        Args:
            email: Email to check
            exclude_id: Optional user ID to exclude from check
            
        Returns:
            True if email exists, False otherwise
        """
        return self.user_repository.exists_by_email(email, exclude_id)

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if username exists.
        
        Args:
            username: Username to check
            exclude_id: Optional user ID to exclude from check
            
        Returns:
            True if username exists, False otherwise
        """
        return self.user_repository.exists_by_username(username, exclude_id)