# ===================================================================
# app/core/services/user_service.py - UPDATED WITH BASESERVICE AND NEW EXCEPTION SYSTEM
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.core.security import get_password_hash
from app.services.base import BaseService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import (
    UserUpdate, 
    UserResponse, 
    UserWithTasksResponse,
    UserPaginatedResponse,
    UserFilters,
    UserBulkUpdate,
)
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DuplicateResourceError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """
    Enhanced user service using BaseService with comprehensive validation and error handling.
    Handles user operations, authentication, and validation using new exception system.
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repository = UserRepository(db)

    def get_user_by_id(self, user_id: int) -> UserResponse:
        """Get user by ID with validation"""
        logger.debug(f"Fetching user with ID: {user_id}")
        
        # Validate ID parameter using BaseService
        valid_user_id = self.validate_id_parameter(user_id, "user_id")
        
        # Use BaseService method for consistent error handling
        user = self.get_resource_or_raise(
            valid_user_id,
            self.user_repository.get,
            "User"
        )
        
        return UserResponse.model_validate(user)

    def get_user_by_email(self, email: str) -> UserResponse:
        """Get user by email with validation"""
        logger.debug(f"Fetching user with email: {email}")
        
        # Validate email format using BaseService
        valid_email = self.validate_email_format(email)
        
        # Use BaseService method for consistent error handling
        user = self.get_resource_or_raise(
            valid_email,
            self.user_repository.get_by_email,
            "User"
        )
        
        return UserResponse.model_validate(user)

    def get_user_by_username(self, username: str) -> UserResponse:
        """Get user by username with validation"""
        logger.debug(f"Fetching user with username: {username}")
        
        # Validate username format using BaseService
        valid_username = self.validate_username(username)
        
        # Use BaseService method for consistent error handling
        user = self.get_resource_or_raise(
            valid_username,
            self.user_repository.get_by_username,
            "User"
        )
        
        return UserResponse.model_validate(user)

    def get_user_with_tasks(self, user_id: int) -> UserWithTasksResponse:
        """Get user with their tasks"""
        logger.debug(f"Fetching user with tasks for ID: {user_id}")
        
        # Validate ID and get user
        valid_user_id = self.validate_id_parameter(user_id, "user_id")
        user = self.get_resource_or_raise(
            valid_user_id,
            self.user_repository.get,
            "User"
        )
        
        return UserWithTasksResponse.model_validate(user)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination validation"""
        # Use BaseService pagination validation
        valid_skip, valid_limit = self._convert_to_pagination_params(skip, limit)
        valid_page, valid_per_page = self.validate_pagination_params(valid_skip, valid_limit)
        
        # Convert back to skip/limit format
        calculated_skip = (valid_page - 1) * valid_per_page
        
        try:
            users = self.user_repository.get_multi(skip=calculated_skip, limit=valid_per_page)
            return [UserResponse.model_validate(user) for user in users]
        except Exception as e:
            logger.error(f"Error fetching all users: {str(e)}")
            raise DatabaseError(
                operation="get_all_users",
                details={"skip": calculated_skip, "limit": valid_per_page, "error": str(e)}
            )

    def get_users_with_pagination(
        self, 
        page: int = 1, 
        per_page: int = 10, 
        filters: Optional[UserFilters] = None
    ) -> UserPaginatedResponse:
        """Get users with pagination and optional filters using BaseService validation"""
        # Use BaseService pagination validation
        valid_page, valid_per_page = self.validate_pagination_params(page, per_page)
        
        # Validate and sanitize filters
        filter_dict = {}
        if filters:
            filter_dict = self._validate_and_sanitize_filters(filters)
        
        try:
            # Calculate skip for repository
            skip = (valid_page - 1) * valid_per_page
            
            users, total = self.user_repository.get_with_pagination(
                skip=skip, 
                limit=valid_per_page, 
                **filter_dict
            )
            
            user_responses = [UserResponse.model_validate(user) for user in users]
            
            # Calculate pagination metadata
            total_pages = (total + valid_per_page - 1) // valid_per_page
            has_next = valid_page < total_pages
            has_previous = valid_page > 1
            
            return UserPaginatedResponse(
                users=user_responses,
                total=total,
                page=valid_page,
                per_page=valid_per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_previous=has_previous
            )
        except Exception as e:
            logger.error(f"Error fetching paginated users: {str(e)}")
            raise DatabaseError(
                operation="get_users_with_pagination",
                details={
                    "page": valid_page, 
                    "per_page": valid_per_page, 
                    "filters": filter_dict,
                    "error": str(e)
                }
            )

    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user information with comprehensive validation"""
        logger.info(f"Updating user with ID: {user_id}")
        
        # Validate ID parameter
        valid_user_id = self.validate_id_parameter(user_id, "user_id")
        
        # Get existing user
        existing_user = self.get_resource_or_raise(
            valid_user_id,
            self.user_repository.get,
            "User"
        )
        
        # Convert to dict, excluding None values
        update_dict = user_data.model_dump(exclude_none=True)
        if not update_dict:
            raise ValidationError(
                field="update_data",
                message="No fields provided for update",
                constraint="not_empty"
            )
        
        # Validate and sanitize update data
        validated_update_dict = self._validate_update_data(update_dict, valid_user_id)
        
        # Check for conflicts using BaseService
        self._check_update_conflicts(valid_user_id, validated_update_dict)
        
        # Prepare update data
        final_update_dict = self._prepare_user_data_for_update(validated_update_dict)
        
        # Update user using transaction
        def update_operation():
            updated_user = self.user_repository.update(existing_user, final_update_dict)
            logger.info(f"User {valid_user_id} updated successfully")
            return updated_user
        
        updated_user = self.execute_in_transaction(update_operation)
        return UserResponse.model_validate(updated_user)

    def delete_user(self, user_id: int) -> UserResponse:
        """Soft delete a user with validation"""
        logger.info(f"Deleting user with ID: {user_id}")
        
        # Validate ID parameter
        valid_user_id = self.validate_id_parameter(user_id, "user_id")
        
        # Check if user exists
        existing_user = self.get_resource_or_raise(
            valid_user_id,
            self.user_repository.get,
            "User"
        )
        
        # Check if user is already deleted (soft delete)
        if hasattr(existing_user, 'deleted_at') and existing_user.deleted_at:
            raise ValidationError(
                field="user_status",
                message="User is already deleted",
                constraint="already_deleted"
            )
        
        # Soft delete user using transaction
        def delete_operation():
            deleted_user = self.user_repository.soft_delete(valid_user_id)
            if not deleted_user:
                raise DatabaseError(
                    operation="soft_delete_user",
                    details={"user_id": valid_user_id}
                )
            logger.info(f"User {valid_user_id} deleted successfully")
            return deleted_user
        
        deleted_user = self.execute_in_transaction(delete_operation)
        return UserResponse.model_validate(deleted_user)

    def bulk_update_users(self, bulk_data: UserBulkUpdate) -> int:
        """Bulk update multiple users with validation"""
        logger.info(f"Bulk updating {len(bulk_data.user_ids)} users")
        
        # Validate bulk data
        if not bulk_data.user_ids:
            raise ValidationError(
                field="user_ids",
                message="User IDs list cannot be empty",
                constraint="not_empty"
            )
        
        if len(bulk_data.user_ids) > 1000:  # Prevent very large bulk operations
            raise ValidationError(
                field="user_ids",
                message="Cannot update more than 1000 users at once",
                invalid_value=len(bulk_data.user_ids),
                constraint="max_length_1000"
            )
        
        # Validate each user ID
        valid_user_ids = []
        for user_id in bulk_data.user_ids:
            valid_id = self.validate_id_parameter(user_id, "user_id")
            valid_user_ids.append(valid_id)
        
        # Remove duplicates while preserving order
        valid_user_ids = list(dict.fromkeys(valid_user_ids))
        
        # Validate update data
        update_dict = bulk_data.update_data.model_dump(exclude_none=True)
        if not update_dict:
            raise ValidationError(
                field="update_data",
                message="No fields provided for bulk update",
                constraint="not_empty"
            )
        
        # Validate update fields
        validated_update_dict = self._validate_update_data(update_dict)
        
        # Prepare updates
        def bulk_update_operation():
            updates = []
            final_update_dict = self._prepare_user_data_for_update(validated_update_dict)
            
            for user_id in valid_user_ids:
                user_update = {'id': user_id, **final_update_dict}
                updates.append(user_update)
            
            updated_count = self.user_repository.bulk_update(updates)
            logger.info(f"Bulk update completed: {updated_count} users updated")
            return updated_count
        
        return self.execute_in_transaction(bulk_update_operation)

    def get_user_count(self, filters: Optional[UserFilters] = None) -> int:
        """Get total count of users matching optional filters"""
        filter_dict = {}
        if filters:
            filter_dict = self._validate_and_sanitize_filters(filters)
        
        try:
            return self.user_repository.count(**filter_dict)
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            raise DatabaseError(
                operation="count_users",
                details={"filters": filter_dict, "error": str(e)}
            )

    def search_users(self, search_term: str, page: int = 1, per_page: int = 10) -> UserPaginatedResponse:
        """Search users by email, username, or full name"""
        # Validate search parameters using BaseService
        valid_search = self.validate_search_params(search_term, min_search_length=2)
        if not valid_search:
            raise ValidationError(
                field="search",
                message="Search term is required and must be at least 2 characters",
                constraint="required_min_length"
            )
        
        # Validate pagination
        valid_page, valid_per_page = self.validate_pagination_params(page, per_page)
        
        try:
            # Calculate skip
            skip = (valid_page - 1) * valid_per_page
            
            # Perform search (assuming repository has search method)
            users, total = self.user_repository.search_users(
                search_term=valid_search,
                skip=skip,
                limit=valid_per_page
            )
            
            user_responses = [UserResponse.model_validate(user) for user in users]
            
            # Calculate pagination metadata
            total_pages = (total + valid_per_page - 1) // valid_per_page
            has_next = valid_page < total_pages
            has_previous = valid_page > 1
            
            return UserPaginatedResponse(
                users=user_responses,
                total=total,
                page=valid_page,
                per_page=valid_per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_previous=has_previous,
                search_term=valid_search
            )
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise DatabaseError(
                operation="search_users",
                details={
                    "search_term": valid_search,
                    "page": valid_page,
                    "per_page": valid_per_page,
                    "error": str(e)
                }
            )

    # Utility methods with BaseService integration
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists by ID with validation"""
        try:
            valid_user_id = self.validate_id_parameter(user_id, "user_id")
            return self.user_repository.exists(valid_user_id)
        except ValidationError:
            return False

    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email exists with validation"""
        try:
            valid_email = self.validate_email_format(email)
            valid_exclude_id = None
            if exclude_id:
                valid_exclude_id = self.validate_id_parameter(exclude_id, "exclude_id")
            return self.user_repository.exists_by_email(valid_email, valid_exclude_id)
        except ValidationError:
            return False

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username exists with validation"""
        try:
            valid_username = self.validate_username(username)
            valid_exclude_id = None
            if exclude_id:
                valid_exclude_id = self.validate_id_parameter(exclude_id, "exclude_id")
            return self.user_repository.exists_by_username(valid_username, valid_exclude_id)
        except ValidationError:
            return False

    # Private helper methods
    def _convert_to_pagination_params(self, skip: int, limit: int) -> tuple[int, int]:
        """Convert skip/limit to page/per_page for BaseService validation"""
        # Convert skip/limit to page/per_page
        page = (skip // limit) + 1 if limit > 0 else 1
        per_page = limit if limit > 0 else 10
        return page, per_page

    def _validate_and_sanitize_filters(self, filters: UserFilters) -> Dict[str, Any]:
        """Validate and sanitize filter parameters"""
        filter_dict = filters.model_dump(exclude_none=True)
        sanitized_filters = {}
        
        for key, value in filter_dict.items():
            if key == "email" and value:
                try:
                    sanitized_filters[key] = self.validate_email_format(value, key)
                except ValidationError:
                    # Skip invalid email filters
                    continue
            elif key == "username" and value:
                try:
                    sanitized_filters[key] = self.validate_username(value, key)
                except ValidationError:
                    # Skip invalid username filters
                    continue
            elif key == "is_active" and isinstance(value, bool):
                sanitized_filters[key] = value
            elif isinstance(value, str):
                # Sanitize string values
                sanitized_value = self.sanitize_string(value, max_length=100)
                if sanitized_value:
                    sanitized_filters[key] = sanitized_value
            else:
                sanitized_filters[key] = value
        
        return sanitized_filters

    def _validate_update_data(self, update_dict: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Validate update data fields"""
        validated_dict = {}
        
        for key, value in update_dict.items():
            if key == "email" and value:
                validated_dict[key] = self.validate_email_format(value, key)
            elif key == "username" and value:
                validated_dict[key] = self.validate_username(value, key)
            elif key == "password" and value:
                self.validate_password_strength(value, key)
                validated_dict[key] = value  # Will be hashed later
            elif key == "full_name" and value:
                validated_dict[key] = self.validate_string_length(value, key, min_length=2, max_length=100)
            elif key == "is_active" and isinstance(value, bool):
                validated_dict[key] = value
            elif isinstance(value, str):
                # Sanitize other string fields
                sanitized_value = self.sanitize_string(value, max_length=255)
                if sanitized_value is not None:
                    validated_dict[key] = sanitized_value
            else:
                validated_dict[key] = value
        
        return validated_dict

    def _check_update_conflicts(self, user_id: int, update_dict: Dict[str, Any]) -> None:
        """Check for email/username conflicts during update using BaseService"""
        if 'email' in update_dict:
            self.check_resource_not_exists(
                lambda: self.user_repository.exists_by_email(update_dict['email'], exclude_id=user_id),
                "User",
                "email",
                update_dict['email']
            )
        
        if 'username' in update_dict:
            self.check_resource_not_exists(
                lambda: self.user_repository.exists_by_username(update_dict['username'], exclude_id=user_id),
                "User", 
                "username",
                update_dict['username']
            )

    def _prepare_user_data_for_update(self, update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare user data dictionary for database update"""
        # Hash password if provided
        if 'password' in update_dict:
            update_dict['hashed_password'] = get_password_hash(update_dict.pop('password'))
        
        # Add audit fields using BaseService method
        return self.prepare_audit_fields(update_dict, is_update=True)