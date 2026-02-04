# AI-Powered LMS Backend

FastAPI backend for the AI-Powered Learning Management System with AWS integrations.

## Features

- 🔐 **AWS Cognito Authentication** - Secure user authentication with JWT tokens
- 📁 **AWS S3 Storage** - File uploads for course resources and images
- 🗄️ **AWS RDS Database** - PostgreSQL database for course data
- 🤖 **AI Chatbot** - OpenAI-powered learning assistant
- 📊 **Progress Tracking** - Track student progress across courses
- 👨‍💼 **Admin Dashboard** - Course and user management

## Prerequisites

- Python 3.10+
- AWS Account with:
  - Cognito User Pool configured
  - S3 Bucket created
  - RDS PostgreSQL instance
- OpenAI API key (optional, for chatbot)

## Installation

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy example env file
   copy .env.example .env   # Windows
   cp .env.example .env     # Linux/Mac
   
   # Edit .env with your AWS credentials
   ```

4. **Initialize database**
   ```bash
   # Run migrations (first time)
   alembic upgrade head
   
   # Or let the app create tables on startup
   python main.py
   ```

## Configuration

Edit `.env` file with your AWS credentials:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# AWS Cognito
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXX
COGNITO_CLIENT_ID=your_client_id
COGNITO_DOMAIN=your-domain.auth.us-east-1.amazoncognito.com

# AWS S3
S3_BUCKET_NAME=your-lms-bucket
S3_REGION=us-east-1

# AWS RDS PostgreSQL
DATABASE_URL=postgresql://user:pass@your-rds.rds.amazonaws.com:5432/lms_db

# Application
APP_SECRET_KEY=your-super-secret-key
FRONTEND_URL=http://localhost:5173

# OpenAI (optional)
OPENAI_API_KEY=sk-your-openai-key
```

## Running the Server

```bash
# Development mode with hot reload
INFO:     127.0.0.1:54860 - "GET /api/courses?published_only=false HTTP/1.1" 200 OK
INFO:     127.0.0.1:54861 - "GET /api/admin/stats HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:52355 - "GET /api/courses?published_only=false HTTP/1.1" 200 OK
INFO:     127.0.0.1:50387 - "GET /api/courses?published_only=false HTTP/1.1" 200 OK
INFO:     127.0.0.1:50388 - "GET /api/admin/stats HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:50390 - "GET /api/courses?published_only=false HTTP/1.1" 200 OK
# Or run directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `GET /api/auth/login` - Redirect to Cognito login
- `GET /api/auth/logout` - Logout and redirect
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update user profile
- `POST /api/auth/verify` - Verify JWT token

### Courses
- `GET /api/courses` - List all courses
- `GET /api/courses/{id}` - Get course details
- `POST /api/courses` - Create course (Admin)
- `PUT /api/courses/{id}` - Update course (Admin)
- `DELETE /api/courses/{id}` - Delete course (Admin)
- `POST /api/courses/{id}/enroll` - Enroll in course

### Progress
- `GET /api/progress` - Get overall progress
- `GET /api/progress/courses` - Get enrolled courses
- `PUT /api/progress/courses/{id}` - Update course progress
- `PUT /api/progress/lessons/{id}` - Update lesson progress

### Chat
- `POST /api/chat` - Send message to AI assistant
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/history` - Clear chat history

### File Upload
- `POST /api/upload/file` - Upload file to S3
- `POST /api/upload/presigned-url` - Get presigned upload URL
- `POST /api/upload/course/{id}/resource` - Upload course resource
- `POST /api/upload/course-image/{id}` - Upload course image

### Admin
- `GET /api/admin/stats` - Get LMS statistics
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}/role` - Update user role
- `GET /api/admin/courses/{id}/students` - Get enrolled students

## AWS Setup Guide

### Cognito User Pool

1. Create a new User Pool in AWS Cognito
2. Configure app client with:
   - Enable "Implicit grant" flow
   - Add callback URL: `http://localhost:5173/callback`
   - Enable scopes: email, openid, profile
3. Create user groups:
   - `Admin_auth` - For administrators
   - `Students_auth` - For students
4. Note down: User Pool ID, Client ID, Domain

### S3 Bucket

1. Create S3 bucket for file storage
2. Configure CORS:
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
       "AllowedOrigins": ["http://localhost:5173"],
       "ExposeHeaders": []
     }
   ]
   ```
3. Enable public access for course resources (or use presigned URLs)

### RDS PostgreSQL

1. Create RDS PostgreSQL instance
2. Configure security group to allow connections from your IP/server
3. Note the endpoint URL, username, and password
4. Create database: `lms_db`

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── alembic.ini          # Database migration config
├── .env.example         # Environment variables template
├── app/
│   ├── __init__.py
│   ├── config.py        # Application settings
│   ├── database.py      # Database connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── dependencies.py  # FastAPI dependencies
│   ├── routes/          # API route handlers
│   │   ├── auth.py      # Authentication routes
│   │   ├── courses.py   # Course CRUD routes
│   │   ├── progress.py  # Progress tracking routes
│   │   ├── upload.py    # File upload routes
│   │   ├── chat.py      # AI chatbot routes
│   │   └── admin.py     # Admin routes
│   └── services/        # External services
│       ├── cognito.py   # AWS Cognito service
│       └── s3.py        # AWS S3 service
└── alembic/             # Database migrations
    └── versions/
```

## Security Notes

- Never commit `.env` file to version control
- Use IAM roles in production instead of access keys
- Enable HTTPS in production
- Configure proper CORS origins for production
- Use strong secret keys

## License

MIT
