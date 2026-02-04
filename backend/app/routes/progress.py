"""
User progress routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import User, UserProgress, Course, user_courses
from app.schemas import ProgressUpdate, ProgressResponse, OverallProgress, CourseResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("", response_model=OverallProgress)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get overall learning progress for current user
    """
    # Get all progress records for user (course-level only)
    progress_records = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.lesson_id == None  # Only course-level progress
    ).all()
    
    total_courses = len(progress_records)
    completed_courses = sum(1 for p in progress_records if p.is_completed)
    
    avg_progress = 0.0
    if total_courses > 0:
        avg_progress = sum(p.progress_percent for p in progress_records) / total_courses
    
    courses_progress = [
        ProgressResponse(
            course_id=p.course_id,
            progress_percent=p.progress_percent,
            is_completed=p.is_completed,
            last_accessed=p.last_accessed,
        )
        for p in progress_records
    ]
    
    return OverallProgress(
        total_courses=total_courses,
        completed_courses=completed_courses,
        average_progress=round(avg_progress, 2),
        courses=courses_progress,
    )


@router.get("/courses", response_model=List[CourseResponse])
async def get_enrolled_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all courses the user is enrolled in with progress
    """
    enrolled_courses = current_user.enrolled_courses
    
    result = []
    for course in enrolled_courses:
        course_data = CourseResponse.model_validate(course)
        
        # Get progress for this course
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.course_id == course.id,
            UserProgress.lesson_id == None
        ).first()
        
        if progress:
            course_data.progress = progress.progress_percent
        
        result.append(course_data)
    
    return result


@router.get("/courses/{course_id}", response_model=ProgressResponse)
async def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get progress for a specific course
    """
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.course_id == course_id,
        UserProgress.lesson_id == None
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress found for this course"
        )
    
    return progress


@router.put("/courses/{course_id}", response_model=ProgressResponse)
async def update_course_progress(
    course_id: int,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update progress for a specific course
    """
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get or create progress record
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.course_id == course_id,
        UserProgress.lesson_id == None
    ).first()
    
    if not progress:
        # Check if user is enrolled
        if course not in current_user.enrolled_courses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        progress = UserProgress(
            user_id=current_user.id,
            course_id=course_id,
            progress_percent=progress_data.progress_percent,
            is_completed=progress_data.is_completed or progress_data.progress_percent >= 100,
        )
        db.add(progress)
    else:
        progress.progress_percent = progress_data.progress_percent
        progress.is_completed = progress_data.is_completed or progress_data.progress_percent >= 100
    
    db.commit()
    db.refresh(progress)
    
    return progress


@router.put("/lessons/{lesson_id}")
async def update_lesson_progress(
    lesson_id: int,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update progress for a specific lesson
    """
    from app.models import Lesson
    
    # Check if lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    course_id = lesson.module.course_id
    
    # Get or create lesson progress record
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.course_id == course_id,
        UserProgress.lesson_id == lesson_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            course_id=course_id,
            lesson_id=lesson_id,
            progress_percent=progress_data.progress_percent,
            is_completed=progress_data.is_completed,
        )
        db.add(progress)
    else:
        progress.progress_percent = progress_data.progress_percent
        progress.is_completed = progress_data.is_completed
    
    db.commit()
    db.refresh(progress)
    
    # Recalculate overall course progress
    from app.models import CourseModule
    
    # Get total lessons in course
    total_lessons = db.query(Lesson).join(CourseModule).filter(
        CourseModule.course_id == course_id
    ).count()
    
    # Get completed lessons
    completed_lessons = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.course_id == course_id,
        UserProgress.lesson_id != None,
        UserProgress.is_completed == True
    ).count()
    
    # Update course progress
    if total_lessons > 0:
        course_progress_percent = (completed_lessons / total_lessons) * 100
        
        course_progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.course_id == course_id,
            UserProgress.lesson_id == None
        ).first()
        
        if course_progress:
            course_progress.progress_percent = course_progress_percent
            course_progress.is_completed = course_progress_percent >= 100
            db.commit()
    
    return {"message": "Lesson progress updated", "lesson_id": lesson_id}
