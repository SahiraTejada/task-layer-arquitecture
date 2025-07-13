# app/api/v1/users.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.user_service import UserService
from app.schemas.user import (
    UserUpdate,
    UserResponse,
    UserWithTasksResponse,
    UserFilters,
    UserBulkUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationRequest
from app.utils.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    DatabaseError,
    AppValidationError,
    ServiceError,
)

users_router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(db)


@users_router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID.",
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    try:
        return user_service.get_by_id(user_id)  # Using base service method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
    description="Retrieve a user by their email address.",
)
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user by email address.
    
    - **email**: The email address of the user to retrieve
    """
    try:
        return user_service.get_by_email(email)  # User-specific method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/username/{username}",
    response_model=UserResponse,
    summary="Get user by username",
    description="Retrieve a user by their username.",
)
async def get_user_by_username(
    username: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user by username.
    
    - **username**: The username of the user to retrieve
    """
    try:
        return user_service.get_by_username(username)  # User-specific method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/{user_id}/tasks",
    response_model=UserWithTasksResponse,
    summary="Get user with tasks",
    description="Retrieve a user along with their associated tasks.",
)
async def get_user_with_tasks(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user with their associated tasks.
    
    - **user_id**: The ID of the user to retrieve with tasks
    """
    try:
        return user_service.get_with_tasks(user_id)  # Updated method name
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/",
    response_model=List[UserResponse],
    summary="Get all users",
    description="Retrieve all users with basic pagination.",
)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get all users with pagination.
    
    - **skip**: Number of users to skip (default: 0)
    - **limit**: Maximum number of users to return (default: 100, max: 1000)
    """
    try:
        return user_service.get_all(skip=skip, limit=limit)  # Using base service method
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/paginated/list",
    response_model=PaginatedResponse[UserResponse],
    summary="Get users with advanced pagination",
    description="Retrieve users with advanced pagination and filtering options.",
)
async def get_users_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of users to return per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    email_contains: Optional[str] = Query(None, description="Filter by email containing text"),
    username_contains: Optional[str] = Query(None, description="Filter by username containing text"),
    full_name_contains: Optional[str] = Query(None, description="Filter by full name containing text"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get users with advanced pagination and filtering.
    
    - **page**: Page number (default: 1)
    - **limit**: Maximum number of users to return per page (default: 10, max: 100)
    - **is_active**: Filter by active status
    - **email_contains**: Filter by email containing text
    - **username_contains**: Filter by username containing text
    - **full_name_contains**: Filter by full name containing text
    """
    try:
        # Create pagination request
        pagination = PaginationRequest(page=page, limit=limit)
        
        # Create filters object
        filters = UserFilters(
            is_active=is_active,
            email_contains=email_contains,
            username_contains=username_contains,
            full_name_contains=full_name_contains,
        )
        
        return user_service.get_filtered_paginated(pagination, filters)  # Updated method
        
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information by ID.",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user information.
    
    - **user_id**: The ID of the user to update
    - **user_data**: Updated user information
    """
    try:
        return user_service.update(user_id, user_data)  # Using base service method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Delete user",
    description="Soft delete a user by ID.",
)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Soft delete a user.
    
    - **user_id**: The ID of the user to delete
    """
    try:
        return user_service.delete(user_id)  # Using base service method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.put(
    "/bulk-update",
    response_model=dict,
    summary="Bulk update users",
    description="Update multiple users at once.",
)
async def bulk_update_users(
    bulk_data: UserBulkUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Bulk update multiple users.
    
    - **user_ids**: List of user IDs to update
    - **update_data**: Data to update for all specified users
    """
    try:
        updated_count = user_service.bulk_update_users(bulk_data)  # User-specific method
        return {
            "message": f"Successfully updated {updated_count} users",
            "updated_count": updated_count
        }
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/count/total",
    response_model=dict,
    summary="Get user count",
    description="Get the total count of users with optional filters.",
)
async def get_user_count(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    email_contains: Optional[str] = Query(None, description="Filter by email containing text"),
    username_contains: Optional[str] = Query(None, description="Filter by username containing text"),
    full_name_contains: Optional[str] = Query(None, description="Filter by full name containing text"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get total count of users with optional filters.
    
    - **is_active**: Filter by active status
    - **email_contains**: Filter by email containing text
    - **username_contains**: Filter by username containing text
    - **full_name_contains**: Filter by full name containing text
    """
    try:
        filters = UserFilters(
            is_active=is_active,
            email_contains=email_contains,
            username_contains=username_contains,
            full_name_contains=full_name_contains,
        )
        
        count = user_service.count(**filters.model_dump(exclude_none=True))  # Using base service method
        return {"total_users": count}
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/{user_id}/exists",
    response_model=dict,
    summary="Check if user exists",
    description="Check if a user exists by ID.",
)
async def check_user_exists(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Check if a user exists by ID.
    
    - **user_id**: The ID of the user to check
    """
    try:
        exists = user_service.exists(user_id)  # Using base service method
        return {"exists": exists}
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.get(
    "/check-email/{email}",
    response_model=dict,
    summary="Check if email exists",
    description="Check if an email address is already taken.",
)
async def check_email_exists(
    email: str,
    exclude_id: Optional[int] = Query(None, description="User ID to exclude from check"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Check if an email address is already taken.
    
    - **email**: The email address to check
    - **exclude_id**: User ID to exclude from the check (useful for updates)
    """
    exists = user_service.email_exists(email, exclude_id)  # User-specific method
    return {"exists": exists}


@users_router.get(
    "/check-username/{username}",
    response_model=dict,
    summary="Check if username exists",
    description="Check if a username is already taken.",
)
async def check_username_exists(
    username: str,
    exclude_id: Optional[int] = Query(None, description="User ID to exclude from check"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Check if a username is already taken.
    
    - **username**: The username to check
    - **exclude_id**: User ID to exclude from the check (useful for updates)
    """
    exists = user_service.username_exists(username, exclude_id)  # User-specific method
    return {"exists": exists}


# Additional endpoints leveraging the new BaseService capabilities

@users_router.get(
    "/active/list",
    response_model=List[UserResponse],
    summary="Get active users",
    description="Retrieve all active users.",
)
async def get_active_users(
    user_service: UserService = Depends(get_user_service),
):
    """
    Get all active users.
    """
    try:
        return user_service.get_active_users()  # User-specific method
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.put(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user",
    description="Activate a user account.",
)
async def activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Activate a user account.
    
    - **user_id**: The ID of the user to activate
    """
    try:
        return user_service.activate_user(user_id)  # User-specific method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@users_router.put(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user",
    description="Deactivate a user account.",
)
async def deactivate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Deactivate a user account.
    
    - **user_id**: The ID of the user to deactivate
    """
    try:
        return user_service.deactivate_user(user_id)  # User-specific method
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )