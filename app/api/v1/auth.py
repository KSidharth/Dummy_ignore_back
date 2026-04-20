
"""
Authentication API endpoints (v1).
Implements all auth routes per API contract: login page, login submission, welcome page.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RedirectDto,
    WelcomePageDto,
    LoginPageDto
)
from app.schemas.common import ErrorDto
from app.services.auth_service import AuthService
from app.models.models import LoginUser


router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get(
    "/",
    response_model=LoginPageDto,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorDto, "description": "Internal server error"}
    },
    summary="Serve Login Landing Page",
    description=(
        "Serves the login landing page per FR-001 — first page presented to any "
        "unauthenticated user, containing the EmailID field, Password field, and Login button"
    )
)
async def get_login_page() -> LoginPageDto:
    """
    GET /api/v1/ — Serve login page metadata.
    
    This endpoint returns metadata about the login page for SPA routing.
    The actual HTML is served by the frontend React app.
    
    Returns:
        LoginPageDto with page identifier and title
    """
    return LoginPageDto(
        page="login",
        title="Login"
    )


@router.post(
    "/login",
    response_model=RedirectDto,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": RedirectDto,
            "description": "Login successful, redirect to welcome page"
        },
        400: {
            "model": ErrorDto,
            "description": "Invalid input format (bad email or empty password)"
        },
        401: {
            "model": ErrorDto,
            "description": "Authentication failed (invalid credentials)"
        },
        422: {
            "model": ErrorDto,
            "description": "Validation error"
        },
        500: {
            "model": ErrorDto,
            "description": "Internal server error"
        }
    },
    summary="Submit Login Credentials",
    description=(
        "Submit EmailID and Password credentials per FR-002 and FR-003. "
        "Validates input format, queries the login_user PostgreSQL table, "
        "creates an authenticated session on success, and returns a redirect signal "
        "to the welcome page. On failure returns a generic error message per NFR-003 "
        "without revealing which field was incorrect."
    )
)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> RedirectDto:
    """
    POST /api/v1/login — Authenticate user and create session.
    
    Flow per FR-003:
    1. Validate EmailID format and Password non-empty (Pydantic handles this)
    2. Query login_user table with submitted EmailID
    3. Verify password hash using bcrypt
    4. Log attempt to login_attempt table
    5. Create session in user_session table on success
    6. Generate JWT token containing session_id
    7. Return redirect response with token
    
    Args:
        request: FastAPI request object (for IP and user agent)
        login_data: LoginRequest DTO with EmailID and Password
        db: Async database session dependency
        
    Returns:
        RedirectDto with access token and redirect URL on success
        
    Raises:
        HTTPException 401: If credentials are invalid (generic message per NFR-003)
        HTTPException 500: If database or service error occurs
    """
    # Extract client context for audit logging
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Initialize auth service
    auth_service = AuthService()
    
    # Authenticate user credentials against database per FR-003
    success, user, failure_reason = await auth_service.authenticate_user(
        db=db,
        email=login_data.EmailID,
        password=login_data.Password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not success:
        # Return generic error message per NFR-003 (do not reveal which field failed)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your email and password."
        )
    
    # Create active session per FR-004
    session = await auth_service.create_session(db=db, email=user.email_id)
    
    # Generate JWT access token
    access_token = auth_service.create_access_token(
        session_id=session.session_id,
        email=user.email_id
    )
    
    # Return redirect response per API contract
    return RedirectDto(
        redirect_url="/welcome",
        access_token=access_token,
        token_type="bearer"
    )


@router.get(
    "/welcome",
    response_model=WelcomePageDto,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": WelcomePageDto,
            "description": "Welcome page for authenticated user"
        },
        401: {
            "model": ErrorDto,
            "description": "Unauthenticated (no valid session)"
        },
        500: {
            "model": ErrorDto,
            "description": "Internal server error"
        }
    },
    summary="Serve Welcome Page",
    description=(
        "Serves the welcome page per FR-004 displaying the exact message "
        "'Welcome to Login Website'. Accessible only to users with a valid "
        "authenticated session established after successful login."
    )
)
async def get_welcome_page(
    current_user: Annotated[LoginUser, Depends(get_current_user)]
) -> WelcomePageDto:
    """
    GET /api/v1/welcome — Serve welcome page for authenticated users.
    
    This endpoint is protected by session authentication per API contract.
    Only users with a valid JWT token containing an active session can access.
    
    Args:
        current_user: Authenticated LoginUser from JWT token (dependency)
        
    Returns:
        WelcomePageDto with the exact message per FR-004
    """
    return WelcomePageDto(
        message="Welcome to Login Website",
        email=current_user.email_id
    )
