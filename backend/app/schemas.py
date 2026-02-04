"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============ User Schemas ============

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    id: str  # Cognito sub


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithProgress(UserResponse):
    enrolled_courses: List["CourseResponse"] = []


# ============ Course Schemas ============

class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CourseCreate(CourseBase):
    image_url: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "beginner"
    duration_hours: Optional[float] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration_hours: Optional[float] = None
    is_published: Optional[bool] = None


class CourseResponse(CourseBase):
    id: int
    image_url: Optional[str] = None
    category: Optional[str] = None
    difficulty: str
    duration_hours: Optional[float] = None
    is_published: bool
    created_at: datetime
    progress: Optional[float] = 0  # User's progress in this course

    class Config:
        from_attributes = True


class CourseWithResources(CourseResponse):
    resources: List["ResourceResponse"] = []
    modules: List["ModuleResponse"] = []


# ============ Module Schemas ============

class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0


class ModuleCreate(ModuleBase):
    course_id: int


class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    lessons: List["LessonResponse"] = []

    class Config:
        from_attributes = True


# ============ Lesson Schemas ============

class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: int = 0


class LessonCreate(LessonBase):
    module_id: int


class LessonResponse(LessonBase):
    id: int
    module_id: int

    class Config:
        from_attributes = True


# ============ Resource Schemas ============

class ResourceBase(BaseModel):
    name: str
    file_type: Optional[str] = None
    session_name: Optional[str] = "Introduction"
    order: int = 0


class ResourceCreate(ResourceBase):
    course_id: int
    file_url: str


class ResourceResponse(ResourceBase):
    id: int
    course_id: int
    file_url: str
    file_size: Optional[int] = None
    session_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Progress Schemas ============

class ProgressUpdate(BaseModel):
    progress_percent: float = Field(..., ge=0, le=100)
    is_completed: Optional[bool] = False


class ProgressResponse(BaseModel):
    course_id: int
    progress_percent: float
    is_completed: bool
    last_accessed: datetime

    class Config:
        from_attributes = True


class OverallProgress(BaseModel):
    total_courses: int
    completed_courses: int
    average_progress: float
    courses: List[ProgressResponse] = []


# ============ Chat Schemas ============

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    message: str
    response: str
    created_at: datetime


class CourseRAGChatRequest(BaseModel):
    """Request for course-specific RAG chat"""
    message: str = Field(..., min_length=1)
    chat_history: Optional[List[dict]] = None  # Previous messages for context


class RAGSource(BaseModel):
    """Source information for RAG response"""
    page_number: int
    resource_id: int
    similarity: float


class CourseRAGChatResponse(BaseModel):
    """Response from course-specific RAG chat"""
    message: str
    response: str
    sources: List[RAGSource] = []
    chunks_used: int = 0
    created_at: datetime


class RAGStatsResponse(BaseModel):
    """RAG statistics for a course"""
    course_id: int
    total_chunks: int
    resources_processed: int
    total_pages: int


# ============ Auth Schemas ============

class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    groups: List[str] = []


class CognitoTokens(BaseModel):
    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    expires_in: int


# ============ S3 Schemas ============

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str
    folder: Optional[str] = "uploads"


class PresignedUrlResponse(BaseModel):
    upload_url: str
    file_url: str
    expires_in: int


# Forward reference updates
UserWithProgress.model_rebuild()
CourseWithResources.model_rebuild()
ModuleResponse.model_rebuild()
