
"""
Shared FastAPI dependencies for database sessions and authentication.
Provides get_db() for database access and get_current_user() for auth.
"""
from typing import Annotated
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_async_session
from app.models.models import UserSession, LoginUser
from app.config import settings


# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer()


async def get_db() -> AsyncSession:
    """
    Database session dependency.
    Yields an async SQLAlchemy session for use in route handlers.
    """
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LoginUser:
    """
    Authentication dependency for protected routes.
    Validates JWT token, verifies active session, and returns authenticated user.
    
    Raises:
        HTTPException 401: If token is invalid, expired, or session is not active
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        session_id: str = payload.get("session_id")
        email: str = payload.get("sub")
        
        if session_id is None or email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Verify session exists and is active
    stmt = select(UserSession).where(
        UserSession.session_id == session_id,
        UserSession.status == "active"
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if session has expired
    if session.expires_at and session.expires_at < datetime.utcnow():
        # Mark session as expired
        session.status = "expired"
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch and return user
    stmt = select(LoginUser).where(LoginUser.email_id == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user
