"""
Admin routes for managing the LMS
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import User, Course, UserProgress
from app.schemas import UserResponse, CourseResponse
from app.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get overall LMS statistics (Admin only)
    """
    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(Course.is_published == True).count()
    
    # Average progress across all students
    avg_progress = db.query(func.avg(UserProgress.progress_percent)).filter(
        UserProgress.lesson_id == None
    ).scalar() or 0
    
    # Active enrollments
    total_enrollments = db.query(UserProgress).filter(
        UserProgress.lesson_id == None
    ).count()
    
    # Completed courses
    completed_enrollments = db.query(UserProgress).filter(
        UserProgress.lesson_id == None,
        UserProgress.is_completed == True
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "students": total_students,
            "admins": total_admins,
        },
        "courses": {
            "total": total_courses,
            "published": published_courses,
            "draft": total_courses - published_courses,
        },
        "enrollments": {
            "total": total_enrollments,
            "completed": completed_enrollments,
            "average_progress": round(avg_progress, 2),
        },
    }


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get all users (Admin only)
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update a user's role (Admin only)
    """
    if role not in ["student", "admin", "instructor"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be: student, admin, or instructor"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    user.role = role
    db.commit()
    
    return {"message": f"User role updated to {role}"}


@router.get("/courses/all", response_model=List[CourseResponse])
async def get_all_courses_admin(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get all courses including unpublished (Admin only)
    """
    courses = db.query(Course).all()
    return courses


@router.get("/courses/{course_id}/students")
async def get_course_students(
    course_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get all students enrolled in a course (Admin only)
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )
    
    students = []
    for user in course.enrolled_users:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user.id,
            UserProgress.course_id == course_id,
            UserProgress.lesson_id == None
        ).first()
        
        students.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "progress": progress.progress_percent if progress else 0,
            "is_completed": progress.is_completed if progress else False,
        })
    
    return students
