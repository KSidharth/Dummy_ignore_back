
# Login System Backend

FastAPI backend for the simple login authentication system with PostgreSQL database.

## Tech Stack

- **FastAPI** — High-performance Python web framework
- **PostgreSQL** — Relational database (login_user table)
- **psycopg2** — PostgreSQL adapter
- **SQLAlchemy** — Async ORM
- **Pydantic** — Data validation
- **python-jose** — JWT token handling
- **passlib** — Password hashing

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- pip or poetry

## Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp ../.env.example .env
# Edit .env with your database credentials
```

## Database Setup

1. Create PostgreSQL database:
```bash
createdb logindb
```

2. Run database initialization script:
```bash
psql -d logindb -f init_db.sql
```

3. Insert test user (optional):
```sql
INSERT INTO login_user (email_id, password) 
VALUES ('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5M8fGcW7Lm9.S');
-- Password is: password123
```

## Running the Server

Development mode with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── models/
│   │   ├── base.py          # SQLAlchemy base
│   │   ├── database.py      # Database connection
│   │   └── models.py        # ORM models
│   ├── schemas/
│   │   ├── auth.py          # Auth DTOs
│   │   └── common.py        # Common DTOs
│   ├── api/
│   │   ├── deps.py          # Shared dependencies
│   │   └── v1/
│   │       ├── auth.py      # Auth endpoints
│   │       └── router.py    # API router registry
│   └── services/
│       └── auth_service.py  # Authentication logic
├── init_db.sql              # Database schema
├── requirements.txt         # Python dependencies
└── README.md
```

## Required Environment Variables

- `DATABASE_URL` — PostgreSQL connection string (format: postgresql+asyncpg://user:pass@host:port/db)
- `SECRET_KEY` — JWT signing key (generate with: openssl rand -hex 32)
- `ALGORITHM` — JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — Token expiration time (default: 30)
- `BACKEND_CORS_ORIGINS` — Comma-separated allowed origins for CORS

## Authentication Flow

1. User submits EmailID and Password to POST /api/v1/login
2. Backend validates input format (email regex, non-empty password)
3. Queries login_user table with parameterized SQL
4. Verifies password hash using bcrypt
5. Creates session record in user_session table
6. Returns session_id as JWT token
7. Frontend stores token and includes in Authorization header for protected routes

## Security Notes

- All passwords are hashed with bcrypt (cost factor 12)
- JWT tokens signed with HS256
- SQL injection prevented via parameterized queries
- CORS configured with explicit origin whitelist
- Generic error messages prevent enumeration attacks
