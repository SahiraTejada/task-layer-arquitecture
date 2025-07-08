from fastapi import APIRouter
from .auth import auth_router
from .user import users_router


api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(auth_router)
