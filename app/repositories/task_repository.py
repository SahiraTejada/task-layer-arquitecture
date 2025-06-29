from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.task import Task
from app.models.tag import Tag
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.enum import TaskStatus, PriorityEnum

class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    def __init__(self, db: Session):
        super().__init__(Task, db)

    def get_with_tags(self, task_id: int) -> Optional[Task]:
        """Get a task along with its tags loaded."""
        return self.db.query(Task).options(joinedload(Task.tags)).filter(Task.id == task_id).first()

    def get_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[PriorityEnum] = None,
        search: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Task]:
        """Get tasks of a user with advanced filters and pagination."""
        query = self.db.query(Task).options(joinedload(Task.tags)).filter(Task.user_id == user_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        if priority:
            query = query.filter(Task.priority == priority)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Task.name.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )
        
        if tag_ids:
            query = query.join(Task.tags).filter(Tag.id.in_(tag_ids))
        
        if due_date_from:
            query = query.filter(Task.due_date >= due_date_from)
        if due_date_to:
            query = query.filter(Task.due_date <= due_date_to)
        
        if hasattr(Task, sort_by):
            order_func = desc if sort_order.lower() == "desc" else asc
            query = query.order_by(order_func(getattr(Task, sort_by)))
        
        return query.offset(skip).limit(limit).all()

    def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """Get overdue tasks for a user."""
        return self.db.query(Task).filter(
            and_(
                Task.user_id == user_id,
                Task.due_date < datetime.now(),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        ).all()

    def get_due_today(self, user_id: int) -> List[Task]:
        """Get tasks that are due today for a user."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        return self.db.query(Task).filter(
            and_(
                Task.user_id == user_id,
                Task.due_date >= today,
                Task.due_date < tomorrow,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        ).all()

    def get_by_tag(self, user_id: int, tag_id: int) -> List[Task]:
        """Get tasks of a user filtered by a specific tag."""
        return self.db.query(Task).join(Task.tags).filter(
            and_(
                Task.user_id == user_id, 
                Tag.id == tag_id
            )
        ).all()

    def get_by_priority(self, user_id: int, priority: PriorityEnum) -> List[Task]:
        """Get tasks filtered by priority."""
        return self.db.query(Task).filter(
            and_(
                Task.user_id == user_id,
                Task.priority == priority
            )
        ).all()

    def get_completed_in_period(
        self, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Task]:
        """Get tasks completed in a given period."""
        return self.db.query(Task).filter(
            and_(
                Task.user_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_date,
                Task.completed_at <= end_date
            )
        ).all()

    def add_tags(self, task_id: int, tag_ids: List[int]) -> Optional[Task]:
        """Add tags to a task."""
        task = self.get(task_id)
        if task:
            tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            task.tags.extend(tags)
            self.db.commit()
            self.db.refresh(task)
        return task

    def remove_tags(self, task_id: int, tag_ids: List[int]) -> Optional[Task]:
        """Remove tags from a task."""
        task = self.get(task_id)
        if task:
            tags_to_remove = [tag for tag in task.tags if tag.id in tag_ids]
            for tag in tags_to_remove:
                task.tags.remove(tag)
            self.db.commit()
            self.db.refresh(task)
        return task

    def replace_tags(self, task_id: int, tag_ids: List[int]) -> Optional[Task]:
        """Replace all tags of a task with new ones."""
        task = self.get(task_id)
        if task:
            task.tags.clear()
            if tag_ids:
                tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                task.tags.extend(tags)
            self.db.commit()
            self.db.refresh(task)
        return task

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get task statistics for a user."""
        base_query = self.db.query(Task).filter(Task.user_id == user_id)
        
        total = base_query.count()
        completed = base_query.filter(Task.status == TaskStatus.COMPLETED).count()
        pending = base_query.filter(Task.status == TaskStatus.PENDING).count()
        in_progress = base_query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
        cancelled = base_query.filter(Task.status == TaskStatus.CANCELLED).count()
        
        overdue = base_query.filter(
            and_(
                Task.due_date < datetime.now(),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        ).count()
        
        priority_stats = {}
        for priority in PriorityEnum:
            priority_stats[priority.value] = base_query.filter(Task.priority == priority).count()
        
        completed_tasks_with_time = base_query.filter(
            and_(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at.isnot(None),
                Task.created_at.isnot(None)
            )
        ).all()
        
        avg_completion_time = 0
        if completed_tasks_with_time:
            total_time = sum([
                (task.completed_at - task.created_at).total_seconds() / 3600
                for task in completed_tasks_with_time
            ])
            avg_completion_time = total_time / len(completed_tasks_with_time)
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "priority_distribution": priority_stats,
            "avg_completion_time_hours": round(avg_completion_time, 2)
        }

    def get_productivity_data(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily productivity data (completed tasks) for last N days."""
        start_date = datetime.now() - timedelta(days=days)
        
        results = self.db.query(
            func.date(Task.completed_at).label('date'),
            func.count(Task.id).label('completed_count')
        ).filter(
            and_(
                Task.user_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_date
            )
        ).group_by(func.date(Task.completed_at)).all()
        
        return [
            {
                "date": result.date.isoformat(),
                "completed_tasks": result.completed_count
            }
            for result in results
        ]

    def mark_as_completed(self, task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as completed."""
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self.db.commit()
            self.db.refresh(task)
        
        return task

    def reopen_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Reopen a completed or cancelled task."""
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
        
        if task and task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            task.status = TaskStatus.PENDING
            task.completed_at = None
            self.db.commit()
            self.db.refresh(task)
        
        return task
