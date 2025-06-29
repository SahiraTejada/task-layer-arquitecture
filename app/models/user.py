from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # 🔹 Relación con tareas
    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 🔹 Relación con tags (nuevo, para conectar con modelo Tag)
    tags = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan"
    )
