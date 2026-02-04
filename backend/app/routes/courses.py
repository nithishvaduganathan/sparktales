"""
Course CRUD routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import Course, User, UserProgress, user_courses
from app.schemas import (
    CourseCreate, CourseUpdate, CourseResponse, CourseWithResources
)
from app.dependencies import get_current_user, get_current_admin, get_current_user_optional

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=List[CourseResponse])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    published_only: bool = True,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get all courses with optional filtering
    """
    query = db.query(Course)
    
    # Filter by published status (non-admins only see published)
    if published_only and (not current_user or current_user.role != "admin"):
        query = query.filter(Course.is_published == True)
    
    # Filter by category
    if category:
        query = query.filter(Course.category == category)
    
    # Search by title or description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Course.title.ilike(search_term)) | 
            (Course.description.ilike(search_term))
        )
    
    courses = query.offset(skip).limit(limit).all()
    
    # Add user progress if authenticated
    result = []
    for course in courses:
        course_data = CourseResponse.model_validate(course)
        
        if current_user:
            # Get user's progress for this course
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == current_user.id,
                UserProgress.course_id == course.id,
                UserProgress.lesson_id == None  # Overall course progress
            ).first()
            
            if progress:
                course_data.progress = progress.progress_percent
        
        result.append(course_data)
    
    return result


@router.get("/{course_id}", response_model=CourseWithResources)
async def get_course(
    course_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get a specific course with resources and modules
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is published (non-admins)
    if not course.is_published:
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course is not published"
            )
    
    course_data = CourseWithResources.model_validate(course)
    
    # Add user progress if authenticated
    if current_user:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.course_id == course.id,
            UserProgress.lesson_id == None
        ).first()
        
        if progress:
            course_data.progress = progress.progress_percent
    
    return course_data


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new course (Admin only)
    """
    course = Course(
        **course_data.model_dump(),
        instructor_id=current_user.id,
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update a course (Admin only)
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    update_dict = course_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        setattr(course, key, value)
    
    db.commit()
    db.refresh(course)
    
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a course (Admin only)
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    db.delete(course)
    db.commit()
    
    return None


@router.post("/{course_id}/enroll", response_model=dict)
async def enroll_in_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enroll current user in a course
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot enroll in unpublished course"
        )
    
    # Check if already enrolled
    if course in current_user.enrolled_courses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Enroll user
    current_user.enrolled_courses.append(course)
    
    # Create initial progress record
    progress = UserProgress(
        user_id=current_user.id,
        course_id=course_id,
        progress_percent=0,
    )
    db.add(progress)
    
    db.commit()
    
    return {"message": "Successfully enrolled in course", "course_id": course_id}


@router.get("/{course_id}/resources")
async def get_course_resources(
    course_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get all resources for a course
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return course.resources
