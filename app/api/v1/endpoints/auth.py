from fastapi import APIRouter, Depends, HTTPException, status
from app.api.__deps import get_service
from app.services.auth_service import AuthService
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
    UserNotFoundError,
    DatabaseError,
    AppValidationError,
    ServiceError,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


get_auth_service = get_service(AuthService)


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "User already exists"},
        500: {"description": "Internal server error"}
    },
    summary="Create a new user",
    description="Create a new user account with email, username, and password validation.",
)
async def create_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Create a new user account.

    - **email**: Valid email address (must be unique)
    - **username**: Username (must be unique)
    - **password**: Password meeting security requirements
    """
    try:
        return auth_service.register_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except AppValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.post(
    "/login",
    response_model=UserResponse,
    responses={
        200: {"description": "User authenticated successfully"},
        401: {"description": "Invalid credentials"},
        403: {"description": "User account is inactive"},
        500: {"description": "Internal server error"}
    },
    summary="Authenticate user",
    description="Authenticate a user with email and password.",
)
async def authenticate_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Authenticate a user with email and password.

    - **email**: User's email address
    - **password**: User's password
    """
    try:
        return auth_service.authenticate_user(login_data)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except UserInactiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.put(
    "/change-password",
    response_model=SuccessResponseSchema,
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Bad request - validation error or incorrect current password"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    },
    summary="Change user password",
    description="Change a user's password after verifying the current password.",
)
async def change_password(
    password_data: UserChangePassword,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponseSchema:
    """
    Change user password.

    - **user_id**: The ID of the user
    - **old_password**: Current password
    - **new_password**: New password
    """
    try:
        return auth_service.change_password(password_data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AppValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.put(
    "/reset-password",
    response_model=SuccessResponseSchema,
    responses={
        200: {"description": "Password reset successfully"},
        400: {"description": "Validation error"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    },
    summary="Reset user password",
    description="Reset a user's password (admin function or after email verification).",
)
async def reset_password(
    email: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponseSchema:
    """
    Reset user password (admin function).

    - **email**: User's email address
    - **new_password**: New password to set
    """
    try:
        return auth_service.reset_password(email, new_password)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AppValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (DatabaseError, ServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.put(
    "/users/{user_id}/activate",
    response_model=UserResponse,
    responses={
        200: {"description": "User activated successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    },
    summary="Activate user account",
    description="Activate a user account (admin function).",
)
async def activate_user_account(
    user_id: int,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Activate a user account (admin function).

    - **user_id**: ID of user to activate
    """
    try:
        return auth_service.activate_user_account(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.put(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
    responses={
        200: {"description": "User deactivated successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    },
    summary="Deactivate user account",
    description="Deactivate a user account (admin function).",
)
async def deactivate_user_account(
    user_id: int,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Deactivate a user account (admin function).

    - **user_id**: ID of user to deactivate
    """
    try:
        return auth_service.deactivate_user_account(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.get(
    "/users/{user_id}/profile",
    response_model=UserResponse,
    responses={
        200: {"description": "User profile retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    },
    summary="Get user profile",
    description="Get user profile information.",
)
async def get_user_profile(
    user_id: int,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get user profile (convenience method).

    - **user_id**: ID of user to retrieve
    """
    try:
        return auth_service.get_user_profile(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )