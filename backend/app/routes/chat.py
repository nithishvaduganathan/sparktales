"""
AI Chatbot routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime

from app.database import get_db
from app.models import User, ChatHistory, Course
from app.schemas import ChatMessage, ChatResponse, CourseRAGChatRequest, CourseRAGChatResponse, RAGStatsResponse
from app.dependencies import get_current_user, get_current_user_optional
from app.config import get_settings
from app.services.rag import rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()


async def get_ai_response(message: str, context: Optional[str] = None) -> str:
    """
    Get AI response using OpenAI API
    """
    try:
        from openai import OpenAI
        
        if not settings.openai_api_key:
            return "AI assistant is not configured. Please set up OpenAI API key."
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        system_prompt = """You are a helpful AI learning assistant for an online Learning Management System (LMS). 
        You help students with:
        - Understanding course concepts
        - Answering questions about course materials
        - Providing explanations and examples
        - Offering study tips and learning strategies
        - Helping with programming and technical concepts
        
        Be concise, helpful, and encouraging. If you don't know something, admit it."""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Current course context: {context}"
            })
        
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        
        return response.choices[0].message.content
        
    except ImportError:
        return "OpenAI library not installed. Please install it with: pip install openai"
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"


@router.post("", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    course_context: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI chatbot and get a response
    """
    # Get AI response
    response = await get_ai_response(chat_message.message, course_context)
    
    # Save to chat history if user is authenticated
    if current_user:
        history = ChatHistory(
            user_id=current_user.id,
            message=chat_message.message,
            response=response,
            context=course_context,
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        
        return ChatResponse(
            message=chat_message.message,
            response=response,
            created_at=history.created_at,
        )
    
    from datetime import datetime
    return ChatResponse(
        message=chat_message.message,
        response=response,
        created_at=datetime.now(),
    )


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get chat history for current user
    """
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": h.id,
            "message": h.message,
            "response": h.response,
            "context": h.context,
            "created_at": h.created_at,
        }
        for h in history
    ]


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear chat history for current user
    """
    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).delete()
    db.commit()
    
    return {"message": "Chat history cleared"}


# ============ Course-Specific RAG Chat Endpoints ============

@router.post("/course/{course_id}", response_model=CourseRAGChatResponse)
async def course_rag_chat(
    course_id: int,
    request: CourseRAGChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Send a message to the course-specific RAG chatbot.
    Uses course PDFs as context for AI responses.
    """
    # Check course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if Gemini API is configured
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAG chat is not configured. Please set GEMINI_API_KEY."
        )
    
    # Generate RAG response - use try/except to handle DB errors gracefully
    try:
        result = await rag_service.generate_rag_response(
            query=request.message,
            course_id=course_id,
            course_title=course.title,
            db=db,
            chat_history=request.chat_history
        )
    except Exception as e:
        # Rollback any failed transaction from RAG search
        db.rollback()
        # Return response without RAG context
        result = {
            "response": f"I can help answer your question, but I couldn't search the course materials. Error: {str(e)}",
            "sources": [],
            "chunks_used": 0
        }
    
    # Save to chat history if user is authenticated
    if current_user:
        try:
            history = ChatHistory(
                user_id=current_user.id,
                message=request.message,
                response=result["response"],
                context=f"course:{course_id}",
            )
            db.add(history)
            db.commit()
        except Exception as e:
            # Rollback if saving history fails, but don't fail the response
            db.rollback()
            print(f"Failed to save chat history: {e}")
    
    return CourseRAGChatResponse(
        message=request.message,
        response=result["response"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        created_at=datetime.now(),
    )


@router.get("/course/{course_id}/stats", response_model=RAGStatsResponse)
async def get_course_rag_stats(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get RAG statistics for a course (number of indexed documents, chunks, etc.)
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    stats = rag_service.get_course_rag_stats(course_id, db)
    
    return RAGStatsResponse(
        course_id=course_id,
        total_chunks=stats["total_chunks"],
        resources_processed=stats["resources_processed"],
        total_pages=stats["total_pages"],
    )


@router.post("/course/{course_id}/reindex")
async def reindex_course_documents(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Re-process all course PDFs and recreate vector embeddings.
    Useful when documents have been updated or for troubleshooting.
    """
    from app.models import CourseResource
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get all PDF resources for this course
    resources = db.query(CourseResource).filter(
        CourseResource.course_id == course_id,
        CourseResource.file_type == "pdf"
    ).all()
    
    if not resources:
        return {
            "message": "No PDF resources found for this course",
            "resources_processed": 0,
            "total_chunks": 0
        }
    
    total_chunks = 0
    processed = 0
    
    for resource in resources:
        try:
            chunks = await rag_service.process_pdf_for_rag(
                course_id=course_id,
                resource_id=resource.id,
                file_url=resource.file_url,
                db=db
            )
            total_chunks += chunks
            processed += 1
        except Exception as e:
            print(f"Error processing resource {resource.id}: {e}")
    
    return {
        "message": f"Successfully reindexed {processed} resources",
        "resources_processed": processed,
        "total_chunks": total_chunks
    }

