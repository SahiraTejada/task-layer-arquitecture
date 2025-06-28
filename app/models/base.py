from sqlalchemy import Column, Integer, DateTime, func
from app.config.database import Base

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    
    # Fecha de creación (se establece automáticamente)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # Fecha de última actualización (se actualiza automáticamente)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Fecha de eliminación lógica (soft delete)
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
