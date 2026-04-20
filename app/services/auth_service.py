
"""
Authentication service layer.
Handles user credential validation, session management, and login attempt logging.
All business logic for authentication flows per FR-003, FR-004, FR-005.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import LoginUser, UserSession, LoginAttempt
from app.config import settings


# Password hashing context using bcrypt (cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Service class for authentication operations.
    Implements credential validation, session creation, and audit logging.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain-text password using bcrypt.
        
        Args:
            password: Plain-text password string
            
        Returns:
            Bcrypt hashed password string
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a bcrypt hash.
        
        Args:
            plain_password: Plain-text password to verify
            hashed_password: Bcrypt hash from database
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(session_id: UUID, email: str) -> str:
        """
        Create a JWT access token containing session_id and email.
        
        Args:
            session_id: UUID of the active user session
            email: User's email address
            
        Returns:
            Encoded JWT token string
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": email,
            "session_id": str(session_id),
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
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
        
        Args:
            db: Async database session
            email: EmailID submitted by user
            password: Plain-text password submitted by user
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            Tuple of (success: bool, user: LoginUser | None, failure_reason: str | None)
        """
        # Query login_user table for matching email
        stmt = select(LoginUser).where(LoginUser.email_id == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Determine authentication outcome
        if user is None:
            # User not found in database
            failure_reason = "user_not_found"
            success = False
            
            # Log failed attempt with NULL email_id (user doesn't exist)
            attempt = LoginAttempt(
                email_id=None,
                success=False,
                attempt_at=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            db.add(attempt)
            await db.commit()
            
            return (False, None, failure_reason)
        
        # Verify password hash
        if not self.verify_password(password, user.password):
            # Password mismatch
            failure_reason = "invalid_credentials"
            success = False
            
            # Log failed attempt
            attempt = LoginAttempt(
                email_id=email,
                success=False,
                attempt_at=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            db.add(attempt)
            await db.commit()
            
            return (False, None, failure_reason)
        
        # Authentication successful
        # Log successful attempt
        attempt = LoginAttempt(
            email_id=email,
            success=True,
            attempt_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=None
        )
        db.add(attempt)
        await db.commit()
        
        return (True, user, None)
    
    async def create_session(
        self,
        db: AsyncSession,
        email: str
    ) -> UserSession:
        """
        Create a new active user session per FR-004.
        
        Args:
            db: Async database session
            email: EmailID of authenticated user
            
        Returns:
            Created UserSession ORM instance
        """
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        session = UserSession(
            email_id=email,
            status="active",
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            updated_at=datetime.utcnow()
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    async def invalidate_session(
        self,
        db: AsyncSession,
        session_id: UUID
    ) -> bool:
        """
        Invalidate an active user session (logout).
        
        Args:
            db: Async database session
            session_id: UUID of session to invalidate
            
        Returns:
            True if session was invalidated, False if not found
        """
        stmt = select(UserSession).where(UserSession.session_id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session is None:
            return False
        
        session.status = "invalidated"
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        return True
