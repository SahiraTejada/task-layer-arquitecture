from fastapi import APIRouter
from .endpoints.auth import auth_router
from .endpoints.user import users_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)

