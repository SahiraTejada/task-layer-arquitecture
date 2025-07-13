from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Tuple, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

from pydantic import BaseModel
from app.models import BaseModel as GeneralBaseModel
from app.schemas.common import PaginatedResponse, PaginationRequest
from app.utils.exceptions import DatabaseError
# Define type variables to be used with generics
ModelType = TypeVar("ModelType", bound=GeneralBaseModel)       # SQLAlchemy model type
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel) # Pydantic schema for creation
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel) # Pydantic schema for update

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    # Generic repository class that works with any model and schemas
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with the given SQLAlchemy model and DB session.
        """
        self.model = model
        self.db = db

    @contextmanager
    def transaction(self):
            """Context manager for database transactions."""
            try:
                yield self.db
                self.db.commit()
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database transaction failed: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Unexpected error during transaction: {str(e)}")
                raise DatabaseError(f"Unexpected database error: {str(e)}")

    def get(self, id: int) -> Optional[ModelType]:
            """Get one record by its primary key id."""
            try:
                query = self.db.query(self.model).filter(self.model.id == id)
                if hasattr(self.model, "deleted_at"):
                    query = query.filter(self.model.deleted_at.is_(None))
                return query.first()
            except SQLAlchemyError as e:
                logger.error(f"Error fetching {self.model.__name__} with ID {id}: {str(e)}")
                raise DatabaseError(f"Failed to fetch record: {str(e)}")
            
        # Execute the query and return the first matching record or None if not found

    def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """
        Get multiple records with optional filters, skipping and limiting results.
        Excludes soft-deleted records.
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        # Apply dynamic filters passed in as a dictionary called 'filters'
        # Loop through each key-value pair in the filters dictionary
        # 'field' is the name of the model field (as a string), and 'value' is the value to filter by
        for field, value in filters.items():
            # Check that the model has this field AND that the filter value is not None
            if hasattr(self.model, field) and value is not None:
                # Add a filter to the query where model.field == value
                # getattr(self.model, field) dynamically gets the column from the model

                """getattr is a built-in Python function used to dynamically get the value of an attribute
                from an object using its name as a string.
                """
                # Dynamically get the field/column from the model using getattr
                # For example: if field = "username", this becomes self.model.username == value
                query = query.filter(getattr(self.model, field) == value)
        # Apply pagination: skip a number of records and limit the number of results returned        
        return query.offset(skip).limit(limit).all()

    def get_all(self) -> List[ModelType]:
        """
        Get all records (excluding soft-deleted if applicable).
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get one record filtered by a specific field and value.
        """
        if not hasattr(self.model, field):
            return None
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()

    def get_multiple_by_field(self, field: str, value: Any) -> List[ModelType]:
        """
        Get multiple records filtered by a specific field and value.
        """
        if not hasattr(self.model, field):
            return []
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def get_multiple_by_ids(self, ids: List[int]) -> List[ModelType]:
        """
        Get multiple records by a list of ids.
        """
        query = self.db.query(self.model).filter(self.model.id.in_(ids))
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.all()

    def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create a new record from a Pydantic schema or dictionary.
            
        Parameters:
        - obj_in: can be either:
            - a Pydantic schema instance (e.g., UserCreate), which provides validated and structured data
            - OR a plain dictionary (e.g., {"username": "sahira"}), useful for internal use or testing
        This makes the function flexible and able to handle both input types.
        
        Returns:
        - A new instance of the SQLAlchemy model, saved in the database
        """

        # Check if the input is a dictionary
        with self.transaction():
            if isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                obj_data = obj_in.model_dump(exclude_unset=True)

            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.flush()  # Flush to get the ID without committing
            self.db.refresh(db_obj)
            return db_obj

    def create_multi(self, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]) -> List[ModelType]:
        """
        Create multiple records at once.
        
        Parameters:
        - objs_in: A list of inputs, where each item can be either:
            - A Pydantic schema instance (e.g., UserCreate)
            - Or a plain dictionary with field-value pairs
        Returns:
        - A list of newly created SQLAlchemy model instances
        """

        # Initialize an empty list to hold the model instances to be created
        with self.transaction():
            db_objs = []
            for obj_in in objs_in:
                if isinstance(obj_in, dict):
                    obj_data = obj_in
                else:
                    obj_data = obj_in.model_dump(exclude_unset=True)
                
                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)
            
            self.db.add_all(db_objs)
            self.db.flush()
            
            for db_obj in db_objs:
                self.db.refresh(db_obj)
            
            return db_objs


    def update(self, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Update an existing record with data from a Pydantic schema or a dictionary.

        Parameters:
        - db_obj: the existing SQLAlchemy model instance to update.
        - obj_in: data to update with, either as a Pydantic schema or a plain dictionary.

        Returns:
        - The updated SQLAlchemy model instance.
        """

        # Check if the input is a dictionary
        with self.transaction():
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            self.db.add(db_obj)
            self.db.flush()
            self.db.refresh(db_obj)
            return db_obj


    def delete(self, id: int) -> Optional[ModelType]:
        """
        Permanently delete a record by id.
        """
        with self.transaction():
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj:
                self.db.delete(obj)
                self.db.flush()
            return obj

    def soft_delete(self, id: int) -> Optional[ModelType]:
        """
        Soft delete by setting the 'deleted_at' timestamp.
        """
        with self.transaction():
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj and hasattr(obj, "deleted_at"):
                obj.deleted_at = datetime.now(timezone.utc)
                self.db.add(obj)
                self.db.flush()
                self.db.refresh(obj)
                return obj
            return None

    def delete_multi(self, ids: List[int]) -> int:
        """
        Permanently delete multiple records by ids.
        Returns count of deleted rows.
        """
        deleted_count = self.db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
        self.db.commit()
        return deleted_count

    def exists(self, id: int) -> bool:
        """
        Check if a record exists by id (excluding soft deleted).
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first() is not None

    def exists_by_field(self, field: str, value: Any) -> bool:
        """
        Check if a record exists for a given field and value (excluding soft deleted).
        """
        if not hasattr(self.model, field):
            return False
        query = self.db.query(self.model).filter(getattr(self.model, field) == value)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first() is not None

    def count(self, **filters) -> int:
        """
        Count total records matching optional filters (excluding soft deleted).
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
        Bulk update multiple records.
        Each dictionary in the list must include an 'id' key and the fields to update.
        Returns:
            The number of rows successfully updated.
        """

        # If the list of updates is empty, return 0 (nothing to update)
        if not updates:
            return 0

        with self.transaction():
            updated_count = 0
            for update_data in updates:
                if 'id' not in update_data:
                    continue

                obj_id = update_data.pop('id')
                result = self.db.query(self.model).filter(self.model.id == obj_id).update(update_data)
                updated_count += result

            return updated_count


    def get_with_pagination(self, skip: int = 0, limit: int = 10, **filters) -> Tuple[List[ModelType], int]:
        """
        Get records with pagination and optional filters.
        Returns a tuple: (list of items, total count).
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
    
    
    def get_paginated_response(self, pagination: PaginationRequest, **filters) -> PaginatedResponse:
        """
        Get paginated response with enhanced pagination metadata.
        
        Args:
            pagination: Pagination request parameters
            **filters: Additional filter parameters
            
        Returns:
            PaginatedResponse with items and pagination metadata
        """
        skip = (pagination.page - 1) * pagination.limit
        items, total = self.get_with_pagination(skip=skip, limit=pagination.limit, **filters)
        
        total_pages = (total + pagination.limit - 1) // pagination.limit
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
        
        return PaginatedResponse(
            items=items,
            page=pagination.page,
            limit=pagination.limit,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
