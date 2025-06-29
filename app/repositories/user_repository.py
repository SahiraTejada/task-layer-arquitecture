from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email."""
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username."""
        return self.db.query(User).filter(User.username == username, User.deleted_at.is_(None)).first()

    def exists_by_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a user exists with the given email, excluding a specific user ID."""
        query = self.db.query(User).filter(User.email == email, User.deleted_at.is_(None))
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None

    def exists_by_username(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a user exists with the given username, excluding a specific user ID."""
        query = self.db.query(User).filter(User.username == username, User.deleted_at.is_(None))
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None

    def get_active_users(self) -> List[User]:
        """Retrieve all active users."""
        return self.db.query(User).filter(User.is_active.is_(True), User.deleted_at.is_(None)).all()
