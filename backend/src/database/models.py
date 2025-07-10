"""
SQLAlchemy Database Models for Railway PostgreSQL

These models correspond to the existing Pydantic models but are designed for PostgreSQL storage.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from infrastructure.postgresql_client import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Google user ID
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="user", cascade="all, delete-orphan")
    ai_files = relationship("AIFileRecord", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    summary = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("projects.id"), nullable=True)
    level = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    parent = relationship("Project", remote_side=[id], back_populates="children")
    children = relationship("Project", back_populates="parent", cascade="all, delete-orphan")
    notes = relationship("Note", secondary="project_notes", back_populates="projects")


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notes")
    projects = relationship("Project", secondary="project_notes", back_populates="notes")
    action_items = relationship("ActionItem", back_populates="source_note")


class ProjectNote(Base):
    __tablename__ = "project_notes"
    
    project_id = Column(String, ForeignKey("projects.id"), primary_key=True)
    note_id = Column(String, ForeignKey("notes.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task = Column(Text, nullable=False)
    doer = Column(String, nullable=True)
    deadline = Column(String, nullable=True)  # Store as string to match existing format
    theme = Column(String, nullable=True)
    context = Column(Text, nullable=True)
    extracted_entities = Column(JSON, default=dict)
    status = Column(String, default="open")
    type = Column(String, default="task")
    projects = Column(JSON, default=list)  # Store as JSON array of project IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source_note_id = Column(String, ForeignKey("notes.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="action_items")
    source_note = relationship("Note", back_populates="action_items")


class AIFileRecord(Base):
    __tablename__ = "ai_files"
    
    file_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    state = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    input_s3_key = Column(String, nullable=False)
    output_s3_key = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    total_records = Column(Integer, nullable=True)
    processed_records = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="ai_files")


class AIConfiguration(Base):
    __tablename__ = "ai_configurations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    use_case = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    model = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    max_tokens = Column(Integer, default=500)
    temperature = Column(String, default="0.7")  # Store as string to match existing
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=False)
    
    # Composite key constraint would be added via Alembic migration
    __table_args__ = {"comment": "AI configuration storage for different use cases"} 