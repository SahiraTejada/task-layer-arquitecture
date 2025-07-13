from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.services.auth_service import AuthService
from app.schemas.common import SuccessResponseSchema
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserChangePassword,
)
from app.schemas.error import ErrorResponseSchema, ValidationErrorResponseSchema


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with complete validations.",
    responses={
        201: {
            "description": "User created successfully",
            "model": UserResponse
        },
        409: {
            "description": "Email or username already exists",
            "model": ErrorResponseSchema
        },
        422: {
            "description": "Invalid input data",
            "model": ValidationErrorResponseSchema
        },
    }
)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user in the system.

    **Validations:**
    - Email must have valid format and be unique
    - Username must be unique and between 3-50 characters
    - Password must have at least 8 characters with uppercase, lowercase, number, and special character
    - Full name is optional but gets sanitized if provided

    **Required fields:**
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Password meeting security requirements
    - **full_name**: Full name (optional)
    """
    return auth_service.create_user(user_data)


@auth_router.post(
    "/login",
    response_model=UserResponse,
    summary="User login",
    description="Authenticate user with email and password.",
    responses={
        200: {
            "description": "Authentication successful",
            "model": UserResponse
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "User inactive",
            "model": ErrorResponseSchema
        },
    }
)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user with email and password.

    **Validations:**
    - Email must have valid format
    - User must exist and be active
    - Password must match stored password

    **Required fields:**
    - **email**: User email
    - **password**: User password
    """
    return auth_service.authenticate_user(login_data)


@auth_router.put(
    "/users/{user_id}/change-password",
    response_model=SuccessResponseSchema,
    summary="Change password",
    description="Change user password by verifying current password.",
    responses={
        200: {
            "description": "Password changed successfully",
            "model": SuccessResponseSchema
        },
        401: {
            "description": "Current password incorrect",
            "model": ErrorResponseSchema
        },
        404: {
            "description": "User not found",
            "model": ErrorResponseSchema
        },
        422: {
            "description": "New password doesn't meet requirements",
            "model": ValidationErrorResponseSchema
        },
    }
)
async def change_password(
    user_id: int,
    password_data: UserChangePassword,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change user password.

    **Validations:**
    - User must exist
    - Current password must be correct
    - New password must meet security requirements

    **Required fields:**
    - **current_password**: Current password
    - **new_password**: New password
    """
    return auth_service.change_password(user_id, password_data)