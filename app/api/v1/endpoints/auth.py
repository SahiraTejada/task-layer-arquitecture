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
)
from app.utils.response_docs import ResponseDocs

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


get_auth_service = get_service(AuthService)


@auth_router.post(
    "/register",
    responses={
        201: ResponseDocs.created_201(UserResponse, "User created successfully"),
        400: ResponseDocs.validation_error_400(),
        409: ResponseDocs.conflict_409("User"),
        **ResponseDocs.standard_responses(include_auth=False, resource_name="User"),
    },
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
        return auth_service.register_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@auth_router.post(
    "/login",
    responses={
        200: ResponseDocs.success_200(UserResponse, "User login successfully"),
        401: ResponseDocs.unauthorized_401(),
        **ResponseDocs.standard_responses(include_auth=False, resource_name="User"),
    },
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
    "/change-password",
    responses={
        200: ResponseDocs.success_200(
            SuccessResponseSchema, "Password updated successfully"
        ),
        400: ResponseDocs.validation_error_400(),
        401: ResponseDocs.unauthorized_401(),
        **ResponseDocs.standard_responses(include_auth=False, resource_name="User"),
    },
    summary="Change user password",
    description="Change a user's password after verifying the current password.",
)
async def change_password(
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
        return auth_service.change_password(password_data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
