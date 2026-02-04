"""
SQLAlchemy models for the LMS database (AWS RDS)
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# Association table for user-course enrollment
user_courses = Table(
    'user_courses',
    Base.metadata,
    Column('user_id', String(255), ForeignKey('users.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('progress', Float, default=0.0),
    Column('enrolled_at', DateTime(timezone=True), server_default=func.now()),
    Column('completed_at', DateTime(timezone=True), nullable=True),
)


class User(Base):
    """User model - synced with Cognito"""
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)  # Cognito sub (UUID)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="student")  # student, admin, instructor
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    enrolled_courses = relationship("Course", secondary=user_courses, back_populates="enrolled_users")
    progress_records = relationship("UserProgress", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)  # S3 URL
    category = Column(String(100), nullable=True)
    difficulty = Column(String(50), default="beginner")  # beginner, intermediate, advanced
    duration_hours = Column(Float, nullable=True)
    instructor_id = Column(String(255), ForeignKey('users.id'), nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])
    enrolled_users = relationship("User", secondary=user_courses, back_populates="enrolled_courses")
    resources = relationship("CourseResource", back_populates="course", cascade="all, delete-orphan")
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(id={self.id}, title={self.title})>"


class CourseModule(Base):
    """Course module/section model"""
    __tablename__ = "course_modules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CourseModule(id={self.id}, title={self.title})>"


class Lesson(Base):
    """Lesson model within a module"""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey('course_modules.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)  # S3 URL
    duration_minutes = Column(Integer, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    module = relationship("CourseModule", back_populates="lessons")
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title={self.title})>"


class CourseResource(Base):
    """Course resources (PDFs, files) - stored in S3"""
    __tablename__ = "course_resources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)  # S3 URL
    file_type = Column(String(50), nullable=True)  # pdf, video, image, etc.
    file_size = Column(Integer, nullable=True)  # in bytes
    session_name = Column(String(255), nullable=True, default="Introduction")  # Session/Module name
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="resources")
    
    def __repr__(self):
        return f"<CourseResource(id={self.id}, name={self.name})>"


class UserProgress(Base):
    """User progress tracking for courses/lessons"""
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress_records")
    
    def __repr__(self):
        return f"<UserProgress(user_id={self.user_id}, course_id={self.course_id})>"


class ChatHistory(Base):
    """Chat history for AI assistant"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # Course context if applicable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id})>"


class DocumentChunk(Base):
    """Document chunks for RAG - stores text chunks with embeddings for vector search"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    resource_id = Column(Integer, ForeignKey('course_resources.id', ondelete='CASCADE'), nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON array of floats
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course")
    resource = relationship("CourseResource")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, course_id={self.course_id}, page={self.page_number})>"
