from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any

from app.repositories.base import BaseRepository
from app.models.tag import Tag
from app.models.task import Task
from app.schemas.tag import TagCreate, TagUpdate


class TagRepository(BaseRepository[Tag, TagCreate, TagUpdate]):
    def __init__(self, db: Session):
        super().__init__(Tag, db)

    def get_by_user(self, user_id: int) -> List[Tag]:
        """Get all tags that belong to a specific user."""
        return self.db.query(Tag).filter(Tag.user_id == user_id, Tag.deleted_at.is_(None)).all()

    def get_by_name(self, user_id: int, name: str) -> Optional[Tag]:
        """Get a tag by name for a specific user."""
        return self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.name == name, Tag.deleted_at.is_(None))
        ).first()

    def exists_by_name(self, user_id: int, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a tag name exists for a user, excluding a specific tag ID."""
        query = self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.name == name, Tag.deleted_at.is_(None))
        )
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)
        return query.first() is not None

    def search_by_name(self, user_id: int, term: str) -> List[Tag]:
        """Search tags by partial name match (case-insensitive)."""
        return self.db.query(Tag).filter(
            and_(
                Tag.user_id == user_id,
                Tag.name.ilike(f"%{term}%"),
                Tag.deleted_at.is_(None)
            )
        ).all()

    def get_by_color(self, user_id: int, color: str) -> List[Tag]:
        """Get tags by color for a user."""
        return self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.color == color, Tag.deleted_at.is_(None))
        ).all()

    def get_with_task_count(self, user_id: int) -> List[Dict[str, Any]]:
        """Return all tags with associated task count for a user."""
        results = self.db.query(
            Tag,
            func.count(Task.id).label("task_count")
        ).outerjoin(Tag.tasks).filter(
            and_(Tag.user_id == user_id, Tag.deleted_at.is_(None))
        ).group_by(Tag.id).all()

        return [
            {"tag": tag, "task_count": count}
            for tag, count in results
        ]

    def get_popular_tags(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most-used tags for a user."""
        results = self.db.query(
            Tag,
            func.count(Task.id).label("usage_count")
        ).join(Tag.tasks).filter(
            and_(Tag.user_id == user_id, Tag.deleted_at.is_(None))
        ).group_by(Tag.id).order_by(func.count(Task.id).desc()).limit(limit).all()

        return [
            {"tag": tag, "usage_count": count}
            for tag, count in results
        ]

    def get_unused_tags(self, user_id: int) -> List[Tag]:
        """Get tags that are not associated with any task."""
        return self.db.query(Tag).outerjoin(Tag.tasks).filter(
            and_(
                Tag.user_id == user_id,
                Task.id.is_(None),
                Tag.deleted_at.is_(None)
            )
        ).all()

    def bulk_delete_unused(self, user_id: int) -> int:
        """Soft delete all unused tags of a user."""
        unused_tags = self.get_unused_tags(user_id)
        count = 0

        for tag in unused_tags:
            tag.deleted_at = func.now()
            self.db.add(tag)
            count += 1

        if count > 0:
            self.db.commit()

        return count

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """Generate usage statistics for a user's tags."""
        total_tags = self.db.query(Tag).filter(
            Tag.user_id == user_id, Tag.deleted_at.is_(None)
        ).count()

        used_tags = self.db.query(Tag).join(Tag.tasks).filter(
            Tag.user_id == user_id, Tag.deleted_at.is_(None)
        ).distinct().count()

        unused_tags = total_tags - used_tags

        popular = self.get_popular_tags(user_id, limit=5)

        return {
            "total_tags": total_tags,
            "used_tags": used_tags,
            "unused_tags": unused_tags,
            "usage_rate": round((used_tags / total_tags) * 100, 2) if total_tags else 0,
            "most_popular": [
                {
                    "name": p["tag"].name,
                    "color": p["tag"].color,
                    "usage_count": p["usage_count"]
                }
                for p in popular
            ]
        }
