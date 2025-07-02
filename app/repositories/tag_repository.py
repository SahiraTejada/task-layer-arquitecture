from sqlalchemy.orm import Session
# Import SQLAlchemy session for DB operations

from sqlalchemy import and_, func
# Import logical AND operator and SQL functions (like count, now, etc.)

from typing import List, Optional, Dict, Any
# Import type hints

from app.repositories.base import BaseRepository
# Import the generic base repository class

from app.models.tag import Tag
# SQLAlchemy model for Tag

from app.models.task import Task
# SQLAlchemy model for Task

from app.schemas.tag import TagCreate, TagUpdate
# Pydantic schemas for Tag creation and update


# TagRepository inherits from BaseRepository with Tag-specific types
class TagRepository(BaseRepository[Tag, TagCreate, TagUpdate]):

    def __init__(self, db: Session):
        """
        Initialize the TagRepository with a database session.
        """
        super().__init__(Tag, db)  # Call BaseRepository with the Tag model

    def get_by_user(self, user_id: int) -> List[Tag]:
        """Get all tags that belong to a specific user."""
        return self.db.query(Tag).filter(Tag.user_id == user_id, Tag.deleted_at.is_(None)).all()

    def get_by_name(self, user_id: int, name: str) -> Optional[Tag]:
        """Get a tag by name for a specific user."""
        return self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.name == name, Tag.deleted_at.is_(None))
        ).first()

    def exists_by_name(self, user_id: int, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a tag name exists for a user, excluding a specific tag ID (useful during update)."""
        query = self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.name == name, Tag.deleted_at.is_(None))
        )
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)  # Exclude the current tag being updated
        return query.first() is not None  # Return True if found

    def search_by_name(self, user_id: int, term: str) -> List[Tag]:
        """Search tags by partial name match (case-insensitive)."""

        # Start a query on the Tag model
        return self.db.query(Tag).filter(
            and_(
                # Filter tags that belong to the given user
                Tag.user_id == user_id,

                # Filter tags where the name contains the search term (case-insensitive)
                # '%term%' matches substrings anywhere in the name
                Tag.name.ilike(f"%{term}%"),

                # Exclude soft-deleted tags (deleted_at should be NULL)
                Tag.deleted_at.is_(None)
            )
        ).all()  # Execute the query and return all matching tags as a list


    def get_by_color(self, user_id: int, color: str) -> List[Tag]:
        """Get tags by color for a user."""
        return self.db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.color == color, Tag.deleted_at.is_(None))
        ).all()

    def get_with_task_count(self, user_id: int) -> List[Dict[str, Any]]:
        """Return all tags with the count of tasks associated to them."""

        # Build a query to get each tag and how many tasks are associated with it
        # Use outer join so tags with zero tasks are also included
        # Only include tags that belong to the specified user
        # Exclude soft-deleted tags
        # Group by tag ID so the task count is accurate per tag
        results = self.db.query(
            Tag,  # Select the Tag object
            func.count(Task.id).label("task_count")  # Count the number of tasks per tag and label it 'task_count'
        ).outerjoin(Tag.tasks).filter(
            and_(
                Tag.user_id == user_id,         
                Tag.deleted_at.is_(None)   
            )
        ).group_by(Tag.id) .all()  # Execute the query and return all results as a list of tuples (tag, task_count)

        # Format the results as a list of dictionaries with 'tag' and 'task_count' keys
        return [
            {"tag": tag, "task_count": count}
            for tag, count in results  # Iterate through each result tuple: (Tag object, task count)
        ]


    def get_popular_tags(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most-used tags (tags linked to most tasks)."""
        results = self.db.query(
            Tag,
            func.count(Task.id).label("usage_count")  # Count how many tasks are linked to each tag
        ).join(Tag.tasks).filter(
            and_(Tag.user_id == user_id, Tag.deleted_at.is_(None))
        ).group_by(Tag.id).order_by(func.count(Task.id).desc()).limit(limit).all()

        return [
            {"tag": tag, "usage_count": count}
            for tag, count in results
        ]

    def get_unused_tags(self, user_id: int) -> List[Tag]:
        """Get all tags that are not linked to any task."""
        return self.db.query(Tag).outerjoin(Tag.tasks).filter(
            and_(
                Tag.user_id == user_id,
                Task.id.is_(None),  # Only tags with no associated task
                Tag.deleted_at.is_(None)
            )
        ).all()

    def bulk_delete_unused(self, user_id: int) -> int:
        """Soft delete all tags that are not used in any task for a user."""
        unused_tags = self.get_unused_tags(user_id)
        count = 0

        for tag in unused_tags:
            tag.deleted_at = func.now()  # Mark as deleted by setting timestamp
            self.db.add(tag)
            count += 1

        if count > 0:
            self.db.commit()  # Commit all soft deletes

        return count

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """Generate statistics: total, used, unused tags, and top 5 popular tags."""
        # Count total non-deleted tags
        total_tags = self.db.query(Tag).filter(
            Tag.user_id == user_id, Tag.deleted_at.is_(None)
        ).count()

        # Count distinct tags used in at least one task
        used_tags = self.db.query(Tag).join(Tag.tasks).filter(
            Tag.user_id == user_id, Tag.deleted_at.is_(None)
        ).distinct().count()

        # Calculate unused tags
        unused_tags = total_tags - used_tags

        # Get top 5 most used tags
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

