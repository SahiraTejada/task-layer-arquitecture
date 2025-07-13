from typing import TypeVar, Type, Callable
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.database import get_db


T = TypeVar('T')

def get_service(service_class: Type[T]) -> Callable[[Session], T]:
    """Generic dependency factory for services."""
    def _get_service(db: Session = Depends(get_db)) -> T:
        return service_class(db)
    return _get_service

# Dependencias específicas solo para las más complejas
# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     user_service = Depends(get_service(UserService))
# ):
#     """Dependency to get current authenticated user."""
#     return user_service.get_current_user(token)