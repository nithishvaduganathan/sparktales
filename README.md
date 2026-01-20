# SparkTales LMS

A SaaS-based Learning Management System (LMS) with AI-powered Retrieval-Augmented Generation (RAG) capabilities.

## Features

### Core Features
- **User Authentication**: Secure signup, login with JWT-based authentication
- **Document Management**: Upload, manage, and share PDFs, TXT, and DOCX files
- **AI-Powered Q&A**: Ask questions about uploaded documents using RAG technology
- **Discussion Groups**: Create and join public/private discussion groups
- **Group Messaging**: Real-time group discussions with message history
- **Super Admin Dashboard**: Complete platform control and monitoring

### User Roles
- **Student**: Default role for all registered users
- **Super Admin**: Special role with complete platform control (accessible via predefined email)

### Discussion Groups
- **Public Groups**: Open for all users to join
- **Private Groups**: Invite-only, managed by group admins
- Group creator automatically becomes admin
- Admins can invite members and moderate discussions

### AI RAG System
- Upload documents (PDF, TXT, DOCX)
- Automatic text extraction and processing
- Ask natural language questions about document content
- Context-aware responses based strictly on uploaded content

### Admin Features
- Monitor user activities (registrations, logins, failed attempts)
- View and manage all documents, groups, and users
- Enable/disable user accounts
- View audit logs for all platform activities
- Track AI query usage

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM (async)
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt via passlib
- **Document Processing**: PyPDF2
- **RAG Pipeline**: Custom implementation with text chunking

### Frontend
- **Framework**: React.js with TypeScript
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Styling**: CSS with responsive design

## Project Structure

```
sparktales/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   │   ├── auth.py       # Authentication
│   │   │   ├── documents.py  # Document management
│   │   │   ├── groups.py     # Group management
│   │   │   ├── messages.py   # Group messaging
│   │   │   ├── ai.py         # AI RAG queries
│   │   │   └── admin.py      # Super admin
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Utilities
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Backend tests
│   ├── uploads/              # Document storage
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   ├── contexts/         # React contexts
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── types/            # TypeScript types
│   │   ├── App.tsx           # Main app
│   │   └── index.tsx         # Entry point
│   └── package.json          # Node dependencies
└── README.md
```

## Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Configuration

### Backend Environment Variables

Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-secret-key-here
SUPER_ADMIN_EMAIL=superadmin@sparktales.com
SUPER_ADMIN_PASSWORD=SuperAdmin123!
DATABASE_URL=sqlite+aiosqlite:///./sparktales.db
```

### Frontend Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/logout` - Logout user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/` - List user's documents
- `GET /api/documents/shared` - List shared documents
- `GET /api/documents/{id}` - Get document details
- `PUT /api/documents/{id}` - Update document
- `DELETE /api/documents/{id}` - Delete document

### Groups
- `POST /api/groups/` - Create group
- `GET /api/groups/` - List public groups
- `GET /api/groups/my-groups` - List user's groups
- `GET /api/groups/{id}` - Get group details
- `POST /api/groups/{id}/join` - Join public group
- `POST /api/groups/{id}/leave` - Leave group
- `POST /api/groups/{id}/invite` - Invite to private group
- `DELETE /api/groups/{id}` - Delete group

### Messages
- `POST /api/groups/{id}/messages/` - Send message
- `GET /api/groups/{id}/messages/` - List messages
- `PUT /api/groups/{id}/messages/{msg_id}` - Update message
- `DELETE /api/groups/{id}/messages/{msg_id}` - Delete message

### AI
- `POST /api/ai/query` - Ask AI a question
- `GET /api/ai/history` - Get query history
- `GET /api/ai/query/{id}` - Get specific query

### Admin (Super Admin Only)
- `GET /api/admin/dashboard` - Get dashboard stats
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}/status` - Enable/disable user
- `GET /api/admin/audit-logs` - Get audit logs
- `GET /api/admin/groups` - List all groups
- `DELETE /api/admin/groups/{id}` - Delete any group
- `GET /api/admin/documents` - List all documents
- `GET /api/admin/ai-queries` - List all AI queries

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

## Security Features

- JWT-based authentication with token expiration
- Password hashing using bcrypt
- Role-based access control (RBAC)
- Protected routes on frontend
- Audit logging for all sensitive operations
- Input validation using Pydantic schemas
- CORS configuration for frontend communication

## License

MIT License