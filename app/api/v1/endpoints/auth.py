from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.services.auth_service import AuthService
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
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


@auth_router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user account with email, username, and password validation.",
)
async def create_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Create a new user account.

    - **email**: Valid email address (must be unique)
    - **username**: Username (must be unique)
    - **password**: Password meeting security requirements
    - **full_name**: User's full name (optional)
    """
    try:
        return auth_service.create_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.post(
    "/authenticate",
    response_model=UserResponse,
    summary="Authenticate user",
    description="Authenticate a user with email and password.",
)
async def authenticate_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
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


@auth_router.put(
    "/{user_id}/password",
    response_model=UserResponse,
    summary="Change user password",
    description="Change a user's password after verifying the current password.",
)
async def change_password(
    user_id: int,
    password_data: UserChangePassword,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change user password.

    - **user_id**: The ID of the user
    - **old_password**: Current password
    - **new_password**: New password
    """
    try:
        return auth_service.change_password(user_id, password_data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
