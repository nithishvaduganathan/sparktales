"""
File upload routes using AWS S3
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List

from app.models import User, Course, CourseResource
from app.schemas import PresignedUrlRequest, PresignedUrlResponse, ResourceResponse
from app.services.s3 import s3_service
from app.services.rag import rag_service
from app.dependencies import get_current_user, get_current_admin
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/upload", tags=["File Upload"])


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file directly to S3
    """
    # Validate file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 50MB"
        )
    
    # Reset file position
    await file.seek(0)
    
    result = await s3_service.upload_file(file, folder)
    return result


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get a presigned URL for direct upload from frontend
    """
    result = s3_service.generate_presigned_upload_url(
        filename=request.filename,
        content_type=request.content_type,
        folder=request.folder,
    )
    
    return PresignedUrlResponse(
        upload_url=result["upload_url"],
        file_url=result["file_url"],
        expires_in=result["expires_in"],
    )


@router.get("/download-url")
async def get_download_url(
    key: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a presigned URL for downloading a file
    """
    download_url = s3_service.generate_presigned_download_url(key)
    return {"download_url": download_url}


@router.get("/resource/{resource_id}/presigned-url")
async def get_resource_presigned_url(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a presigned URL for viewing a course resource
    """
    resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )
    
    # Extract S3 key from URL
    # URL format: https://bucket.s3.region.amazonaws.com/key
    try:
        key = resource.file_url.split(".amazonaws.com/")[1]
        presigned_url = s3_service.generate_presigned_download_url(key, expires_in=3600)
        return {
            "presigned_url": presigned_url,
            "resource_id": resource_id,
            "file_type": resource.file_type,
            "name": resource.name,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


@router.post("/course/{course_id}/resource", response_model=ResourceResponse)
async def upload_course_resource(
    course_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    session_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Upload a resource file for a course (Admin only)
    PDF files are automatically processed for RAG (text extraction & embedding)
    """
    # Check course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )
    
    # Determine file type
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
    file_type = "pdf" if file_ext == "pdf" else "video" if file_ext in ["mp4", "webm", "mov"] else "other"
    
    # Upload to S3
    folder = f"courses/{course_id}/resources"
    result = await s3_service.upload_file(file, folder)
    
    # Create resource record with session_name
    resource = CourseResource(
        course_id=course_id,
        name=name or file.filename,
        file_url=result["url"],
        file_type=file_type,
        file_size=result["size"],
        session_name=session_name or "Introduction",
        order=len(course.resources),
    )
    
    db.add(resource)
    db.commit()
    db.refresh(resource)
    
    # Process PDF for RAG in background (extract text, create embeddings)
    if file_type == "pdf":
        # We need to process RAG after commit, so schedule it as background task
        async def process_rag():
            from app.database import SessionLocal
            rag_db = SessionLocal()
            try:
                await rag_service.process_pdf_for_rag(
                    course_id=course_id,
                    resource_id=resource.id,
                    file_url=result["url"],
                    db=rag_db
                )
            except Exception as e:
                print(f"RAG processing error for resource {resource.id}: {e}")
            finally:
                rag_db.close()
        
        background_tasks.add_task(process_rag)
    
    return resource


@router.delete("/course/{course_id}/resource/{resource_id}")
async def delete_course_resource(
    course_id: int,
    resource_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a course resource (Admin only)
    """
    resource = db.query(CourseResource).filter(
        CourseResource.id == resource_id,
        CourseResource.course_id == course_id
    ).first()
    
    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )
    
    # Extract S3 key from URL and delete
    # URL format: https://bucket.s3.region.amazonaws.com/key
    try:
        key = resource.file_url.split(".amazonaws.com/")[1]
        s3_service.delete_file(key)
    except Exception:
        pass  # Continue even if S3 delete fails
    
    db.delete(resource)
    db.commit()
    
    return {"message": "Resource deleted"}


@router.post("/course-image/{course_id}")
async def upload_course_image(
    course_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Upload a course thumbnail image (Admin only)
    """
    # Validate it's an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Check course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )
    
    # Upload to S3
    folder = f"courses/{course_id}/images"
    result = await s3_service.upload_file(file, folder)
    
    # Update course image URL
    course.image_url = result["url"]
    db.commit()
    
    return {"image_url": result["url"]}
