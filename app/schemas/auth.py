
"""
Authentication-related Pydantic schemas (DTOs).
Defines request/response models for login, welcome page, and session management.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Login request body schema per API contract POST /api/v1/login.
    Validates EmailID format and ensures Password is non-empty.
    """
    EmailID: EmailStr = Field(
        ...,
        description="User's email address; must be valid email format per NFR-003"
    )
    Password: str = Field(
        ...,
        min_length=1,
        description="User's password; must not be empty per NFR-003"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "EmailID": "test@example.com",
                "Password": "password123"
            }
        }


class LoginResponse(BaseModel):
    """
    Login success response schema.
    Returns session token (JWT) and user email on successful authentication.
    """
    access_token: str = Field(
        ...,
        description="JWT access token containing session_id"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type for Authorization header"
    )
    email: str = Field(
        ...,
        description="Authenticated user's email address"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "email": "test@example.com"
            }
        }


class RedirectDto(BaseModel):
    """
    Redirect response schema per API contract for 302 responses.
    Signals frontend to redirect to welcome page after successful login.
    """
    redirect_url: str = Field(
        ...,
        description="URL to redirect user to after successful authentication"
    )
    access_token: str = Field(
        ...,
        description="JWT access token to include in subsequent requests"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type for Authorization header"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "redirect_url": "/welcome",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class WelcomePageDto(BaseModel):
    """
    Welcome page response schema per API contract GET /api/v1/welcome.
    Returns the exact message per FR-004: 'Welcome to Login Website'.
    """
    message: str = Field(
        default="Welcome to Login Website",
        description="Welcome message displayed to authenticated users"
    )
    email: str = Field(
        ...,
        description="Email of the authenticated user"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Welcome to Login Website",
                "email": "test@example.com"
            }
        }


class LoginPageDto(BaseModel):
    """
    Login page metadata response schema per API contract GET /api/v1/.
    Returns information about the login page (used for SPA routing).
    """
    page: str = Field(
        default="login",
        description="Page identifier"
    )
    title: str = Field(
        default="Login",
        description="Page title"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": "login",
                "title": "Login"
            }
        }


class SessionInfo(BaseModel):
    """
    Session information schema for authenticated user context.
    """
    session_id: UUID
    email_id: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "email_id": "test@example.com",
                "status": "active",
                "created_at": "2024-01-20T10:30:00Z",
                "expires_at": "2024-01-20T11:00:00Z"
            }
        }
