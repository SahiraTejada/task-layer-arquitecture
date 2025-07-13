from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime, timezone, timedelta


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
    
    
    def get_recently_created_users(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users created within the last N days"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return self.db.query(User).filter(
            User.created_at >= cutoff_date,
            User.deleted_at.is_(None)
        ).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        
    def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by username, email, or full name"""
        search_pattern = f"%{search_term.strip()}%"
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            (User.username.ilike(search_pattern) |
             User.email.ilike(search_pattern))
        ).offset(skip).limit(limit).all()
