# app/core/services/base_service.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone

from app.repositories.base import BaseRepository
from app.models import BaseModel as GeneralBaseModel
from app.schemas.common import PaginatedResponse, PaginationRequest
from app.utils.exceptions import (
    AppValidationError,
    ServiceError,
    NotFoundError,
    DatabaseError
)

# Type variables
ModelType = TypeVar("ModelType", bound=GeneralBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseSchemaType = TypeVar("ResponseSchemaType")

logger = logging.getLogger(__name__)




class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType], ABC):
    """
    Base service class that provides common CRUD operations with error handling.
    
    All service classes should inherit from this base class to ensure
    consistent error handling and logging across the application.
    """
    
    def __init__(
        self, 
        repository: BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        entity_name: str
    ):
        """
        Initialize base service.
        
        Args:
            repository: Repository instance for database operations
            response_schema: Pydantic schema for response serialization
            entity_name: Name of the entity (for error messages and logging)
        """
        self.repository = repository
        self.response_schema = response_schema
        self.entity_name = entity_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_by_id(self, entity_id: int) -> ResponseSchemaType:
        """Get entity by ID with error handling."""
        try:
            self.logger.debug(f"Fetching {self.entity_name} with ID: {entity_id}")
            
            entity = self.repository.get(entity_id)
            if not entity:
                raise NotFoundError(f"{self.entity_name} with ID {entity_id} not found")
            
            self.logger.debug(f"{self.entity_name} {entity_id} retrieved successfully")
            return self.response_schema.model_validate(entity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching {self.entity_name} {entity_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve {self.entity_name}: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ResponseSchemaType]:
        """Get all entities with pagination."""
        try:
            self._validate_pagination_params(skip, limit)
            
            self.logger.debug(f"Fetching {self.entity_name}s with skip={skip}, limit={limit}")
            
            entities = self.repository.get_multi(skip=skip, limit=limit)
            
            self.logger.debug(f"Retrieved {len(entities)} {self.entity_name}s")
            return [self.response_schema.model_validate(entity) for entity in entities]
            
        except AppValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching {self.entity_name}s: {str(e)}")
            raise ServiceError(f"Failed to retrieve {self.entity_name}s: {str(e)}")

    def get_paginated(
        self, 
        pagination: PaginationRequest, 
        **filters
    ) -> PaginatedResponse[ResponseSchemaType]:
        """Get entities with enhanced pagination."""
        try:
            self.logger.debug(f"Fetching paginated {self.entity_name}s: page={pagination.page}, limit={pagination.limit}")
            
            # Get paginated response from repository
            paginated_response = self.repository.get_paginated_response(pagination, **filters)
            
            # Convert items to response schema
            response_items = [
                self.response_schema.model_validate(item) 
                for item in paginated_response.items
            ]
            
            # Create new paginated response with converted items
            result = PaginatedResponse[ResponseSchemaType](
                items=response_items,
                page=paginated_response.page,
                limit=paginated_response.limit,
                total=paginated_response.total,
                total_pages=paginated_response.total_pages,
                has_next=paginated_response.has_next,
                has_previous=paginated_response.has_previous
            )
            
            self.logger.debug(f"Retrieved {len(response_items)} {self.entity_name}s (page {pagination.page})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching paginated {self.entity_name}s: {str(e)}")
            raise ServiceError(f"Failed to retrieve {self.entity_name}s: {str(e)}")

    def create(self, create_data: CreateSchemaType) -> ResponseSchemaType:
        """Create new entity with validation."""
        try:
            self.logger.info(f"Creating new {self.entity_name}")
            
            # Perform pre-creation validation
            self._validate_before_create(create_data)
            
            # Prepare data for creation
            prepared_data = self._prepare_create_data(create_data)
            
            # Create entity within transaction
            entity = self.repository.create(prepared_data)
            
            self.logger.info(f"{self.entity_name} created successfully with ID: {entity.id}")
            return self.response_schema.model_validate(entity)
            
        except (AppValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating {self.entity_name}: {str(e)}")
            raise ServiceError(f"Failed to create {self.entity_name}: {str(e)}")

    def update(self, entity_id: int, update_data: UpdateSchemaType) -> ResponseSchemaType:
        """Update existing entity."""
        try:
            self.logger.info(f"Updating {self.entity_name} with ID: {entity_id}")
            
            # Get existing entity
            existing_entity = self._get_entity_or_raise(entity_id)
            
            # Perform pre-update validation
            self._validate_before_update(entity_id, update_data)
            
            # Prepare update data
            prepared_data = self._prepare_update_data(update_data)
            
            # Update entity
            updated_entity = self.repository.update(existing_entity, prepared_data)
            
            self.logger.info(f"{self.entity_name} {entity_id} updated successfully")
            return self.response_schema.model_validate(updated_entity)
            
        except (NotFoundError, AppValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating {self.entity_name} {entity_id}: {str(e)}")
            raise ServiceError(f"Failed to update {self.entity_name}: {str(e)}")

    def delete(self, entity_id: int) -> ResponseSchemaType:
        """Soft delete entity."""
        try:
            self.logger.info(f"Deleting {self.entity_name} with ID: {entity_id}")
            
            # Check if entity exists
            self._get_entity_or_raise(entity_id)
            
            # Perform pre-deletion validation
            self._validate_before_delete(entity_id)
            
            # Soft delete entity
            deleted_entity = self.repository.soft_delete(entity_id)
            if not deleted_entity:
                raise ServiceError(f"Could not delete {self.entity_name} with ID {entity_id}")
            
            self.logger.info(f"{self.entity_name} {entity_id} deleted successfully")
            return self.response_schema.model_validate(deleted_entity)
            
        except (NotFoundError, AppValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting {self.entity_name} {entity_id}: {str(e)}")
            raise ServiceError(f"Failed to delete {self.entity_name}: {str(e)}")

    def exists(self, entity_id: int) -> bool:
        """Check if entity exists."""
        try:
            return self.repository.exists(entity_id)
        except Exception as e:
            self.logger.error(f"Error checking if {self.entity_name} {entity_id} exists: {str(e)}")
            raise ServiceError(f"Failed to check {self.entity_name} existence: {str(e)}")

    def count(self, **filters) -> int:
        """Count entities with optional filters."""
        try:
            return self.repository.count(**filters)
        except Exception as e:
            self.logger.error(f"Error counting {self.entity_name}s: {str(e)}")
            raise ServiceError(f"Failed to count {self.entity_name}s: {str(e)}")

    # Protected helper methods
    def _get_entity_or_raise(self, entity_id: int) -> ModelType:
        """Get entity by ID or raise NotFoundError."""
        entity = self.repository.get(entity_id)
        if not entity:
            raise NotFoundError(f"{self.entity_name} with ID {entity_id} not found")
        return entity

    def _validate_pagination_params(self, skip: int, limit: int) -> None:
        """Validate pagination parameters."""
        if skip < 0:
            raise AppValidationError("Skip parameter must be non-negative")
        if limit <= 0:
            raise AppValidationError("Limit parameter must be positive")
        if limit > 1000:
            raise AppValidationError("Limit parameter cannot exceed 1000")

    def _prepare_create_data(self, create_data: CreateSchemaType) -> Dict[str, Any]:
        """Prepare data for creation. Override in subclasses if needed."""
        if hasattr(create_data, 'model_dump'):
            data = create_data.model_dump(exclude_unset=True)
        else:
            data = dict(create_data) if isinstance(create_data, dict) else create_data
        
        # Add timestamps
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        
        return data

    def _prepare_update_data(self, update_data: UpdateSchemaType) -> Dict[str, Any]:
        """Prepare data for update. Override in subclasses if needed."""
        if hasattr(update_data, 'model_dump'):
            data = update_data.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = dict(update_data) if isinstance(update_data, dict) else update_data
        
        # Add update timestamp
        data['updated_at'] = datetime.now(timezone.utc)
        
        return data

    # Abstract methods for subclasses to implement
    def _validate_before_create(self, create_data: CreateSchemaType) -> None:
        """Override in subclasses for custom creation validation."""
        pass

    def _validate_before_update(self, entity_id: int, update_data: UpdateSchemaType) -> None:
        """Override in subclasses for custom update validation."""
        pass

    def _validate_before_delete(self, entity_id: int) -> None:
        """Override in subclasses for custom deletion validation."""
        pass