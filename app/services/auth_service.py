"""
Authentication service layer.
Handles user credential validation, session management, and login attempt logging.
All business logic for authentication flows per FR-003, FR-004, FR-005.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import LoginUser, UserSession, LoginAttempt
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt (cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Advanced Service class for authentication operations.
    Implements credential validation, session creation, and audit logging.
    """
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a plain-text password using bcrypt."""
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a bcrypt hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @classmethod
    def create_access_token(cls, session_id: UUID, email: str) -> str:
        """Create a JWT access token containing session_id and email."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Build token payload
        payload = {
            "sub": email,
            "session_id": str(session_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        try:
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except JWTError as e:
            logger.error(f"JWT encoding error: {e}")
            raise
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[LoginUser], Optional[str]]:
        """
        Authenticate user credentials against login_user table per FR-003.
        Logs all authentication attempts to login_attempt table per NFR-003.
        """
        user = (await db.execute(select(LoginUser).where(LoginUser.email_id == email))).scalar_one_or_none()
        
        success = False
        failure_reason = None
        
        if not user:
            failure_reason = "user_not_found"
            logger.warning(f"Authentication failed: User {email} not found.")
        elif not self.verify_password(password, user.password):
            failure_reason = "invalid_credentials"
            logger.warning(f"Authentication failed: Invalid password for {email}.")
        else:
            success = True
            logger.info(f"User {email} authenticated successfully.")
            
        # Log the attempt in a unified way
        attempt = LoginAttempt(
            email_id=email if user else None,
            success=success,
            attempt_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason
        )
        db.add(attempt)
        await db.commit()
        
        return (success, user if success else None, failure_reason)
    
    async def create_session(
        self,
        db: AsyncSession,
        email: str
    ) -> UserSession:
        """Create a new active user session per FR-004."""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        session = UserSession(
            email_id=email,
            status="active",
            created_at=now,
            expires_at=expires_at,
            updated_at=now
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created new session {session.session_id} for user {email}")
        return session
    
    async def invalidate_session(
        self,
        db: AsyncSession,
        session_id: UUID
    ) -> bool:
        """Invalidate an active user session (logout)."""
        session = (await db.execute(select(UserSession).where(UserSession.session_id == session_id))).scalar_one_or_none()
        
        if not session:
            logger.warning(f"Session {session_id} not found for invalidation.")
            return False
        
        session.status = "invalidated"
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Invalidated session {session_id}")
        return True