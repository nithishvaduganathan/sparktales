"""
AI-Powered LMS Backend
FastAPI application with AWS Cognito, S3, and RDS integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routes import auth, courses, progress, upload, chat, admin, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Initialize database tables
    print("🚀 Starting AI-Powered LMS Backend...")
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("   Make sure your DATABASE_URL is configured correctly")
    
    yield
    
    # Shutdown
    print("👋 Shutting down AI-Powered LMS Backend...")


# Create FastAPI application
app = FastAPI(
    title="AI-Powered LMS API",
    description="Learning Management System with AWS Cognito, S3, and RDS",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI-Powered LMS API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI-Powered LMS Backend",
        "version": "1.0.0",
    }


@app.get("/api/config")
async def get_frontend_config():
    """
    Get configuration for frontend
    (Only safe-to-expose values)
    """
    return {
        "cognito": {
            "region": settings.aws_region,
            "userPoolId": settings.cognito_user_pool_id,
            "clientId": settings.cognito_client_id,
            "domain": settings.cognito_domain,
        },
        "features": {
            "chat": bool(settings.openai_api_key),
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
