from typing import TypeVar, Type, Callable, Protocol
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.database import get_db


T = TypeVar('T')


class ServiceProtocol(Protocol):
    """Protocol for services that accept a database session."""
    def __init__(self, db: Session) -> None:
        ...


def get_service(service_class: Type[T]) -> Callable[[Session], T]:
    """Generic dependency factory for services that accept a database session."""
    def _get_service(db: Session = Depends(get_db)) -> T:
        # Ensure the service class can be instantiated with a db parameter
        return service_class(db)  # type: ignore[call-arg]
    return _get_service




# Dependencias específicas solo para las más complejas
# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     user_service = Depends(get_service(UserService))
# ):
#     """Dependency to get current authenticated user."""
#     return user_service.get_current_user(token)