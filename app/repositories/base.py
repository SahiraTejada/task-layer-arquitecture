from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Tuple, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import BaseModel as GeneralBaseModel

# Type variables for generic usage
ModelType = TypeVar("ModelType", bound=GeneralBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initializes the repository with a model and a database session.
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID (excluding soft-deleted if applicable).
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()

    def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """
        Get multiple records with optional filters and pagination.
        Excludes soft-deleted records.
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.offset(skip).limit(limit).all()

    def get_all(self) -> List[ModelType]:
        """
        Get all records from the table (excluding soft-deleted if applicable).
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get a single record by any field name and value.
        """
        if not hasattr(self.model, field):
            return None
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()

    def get_multiple_by_field(self, field: str, value: Any) -> List[ModelType]:
        """
        Get multiple records that match a specific field and value.
        """
        if not hasattr(self.model, field):
            return []
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def get_multiple_by_ids(self, ids: List[int]) -> List[ModelType]:
        """
        Get multiple records that match a list of IDs.
        """
        query = self.db.query(self.model).filter(self.model.id.in_(ids))
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create a new record from a Pydantic model or dictionary.
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def create_multi(self, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]) -> List[ModelType]:
        """
        Create multiple records at once.
        """
        db_objs = []
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                obj_data = obj_in.model_dump(exclude_unset=True)
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)
        self.db.add_all(db_objs)
        self.db.commit()
        for db_obj in db_objs:
            self.db.refresh(db_obj)
        return db_objs

    def update(self, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Update an existing record using a Pydantic model or dictionary.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> Optional[ModelType]:
        """
        Permanently delete a record by ID.
        """
        obj = self.db.query(self.model).filter(self.model.id == id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def soft_delete(self, id: int) -> Optional[ModelType]:
        """
        Soft-delete a record by setting its `deleted_at` field.
        """
        obj = self.db.query(self.model).filter(self.model.id == id).first()
        if obj and hasattr(obj, "deleted_at"):
            obj.deleted_at = datetime.now(timezone.utc)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        return None

    def delete_multi(self, ids: List[int]) -> int:
        """
        Permanently delete multiple records by a list of IDs.
        """
        deleted_count = self.db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
        self.db.commit()
        return deleted_count

    def exists(self, id: int) -> bool:
        """
        Check if a record exists by ID.
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first() is not None

    def exists_by_field(self, field: str, value: Any) -> bool:
        """
        Check if a record exists for a specific field and value.
        """
        if not hasattr(self.model, field):
            return False
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first() is not None

    def count(self, **filters) -> int:
        """
        Count total records with optional filters (excluding soft-deleted).
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.count()

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Perform bulk updates. Each dict must include an 'id' key.
        """
        if not updates:
            return 0
        updated_count = 0
        for update_data in updates:
            if 'id' not in update_data:
                continue
            obj_id = update_data.pop('id')
            result = self.db.query(self.model).filter(self.model.id == obj_id).update(update_data)
            updated_count += result
        self.db.commit()
        return updated_count

    def get_with_pagination(self, skip: int = 0, limit: int = 10, **filters) -> Tuple[List[ModelType], int]:
        """
        Get records with pagination and optional filters.
        Returns a tuple: (items list, total count).
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
