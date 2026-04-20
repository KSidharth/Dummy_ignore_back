
"""
SQLAlchemy ORM models for all database tables.
Defines the complete schema for login_user, user_session, and login_attempt tables.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Boolean, BigInteger, CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from app.models.base import Base


class LoginUser(Base):
    """
    ORM model for login_user table.
    Stores user credentials (EmailID as PK, Password) for authentication.
    Table name is strictly enforced by FR-005 and BR-002.
    """
    __tablename__ = "login_user"
    
    email_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
        nullable=False,
        doc="EmailID serves as natural primary key; case-sensitive"
    )
    password: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Bcrypt hashed password; hashing handled at application layer"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Row creation timestamp for basic auditability"
    )
    
    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    login_attempts: Mapped[list["LoginAttempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "email_id ~* '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
            name="login_user_email_format"
        ),
        Index("idx_login_user_email_id", "email_id"),
    )


class UserSession(Base):
    """
    ORM model for user_session table.
    Tracks authenticated sessions created upon successful login (FR-004).
    Records session ID, owning EmailID (FK to login_user), status, and timestamps.
    """
    __tablename__ = "user_session"
    
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        doc="Surrogate session identifier; UUID reduces enumeration risk"
    )
    email_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("login_user.email_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        doc="FK to login_user; identifies session owner"
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
        doc="Session lifecycle state: active | expired | invalidated"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Session creation time; used for expiry calculations"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Optional explicit expiry timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last status-change timestamp"
    )
    
    # Relationships
    user: Mapped["LoginUser"] = relationship(back_populates="sessions")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'expired', 'invalidated')",
            name="user_session_status_check"
        ),
        Index("idx_user_session_session_id", "session_id"),
        Index("idx_user_session_email_id", "email_id"),
        Index("idx_user_session_status", "status"),
        Index("idx_user_session_created_at", "created_at"),
        Index("idx_user_session_expires_at", "expires_at"),
    )


class LoginAttempt(Base):
    """
    ORM model for login_attempt table.
    Append-only audit log of all login attempts per FR-003 and NFR-003.
    Records submitted EmailID, success flag, timestamp, and optional security context.
    """
    __tablename__ = "login_attempt"
    
    attempt_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        doc="Auto-incrementing surrogate PK per ER diagram"
    )
    email_id: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("login_user.email_id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        doc="EmailID submitted; nullable to preserve history after user deletion"
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="TRUE = credentials validated; FALSE = authentication failure"
    )
    attempt_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Exact timestamp of attempt; critical for audit per NFR-003"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Client IP address for security auditing"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Browser/client user-agent string for audit context"
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Non-sensitive reason code: invalid_credentials | user_not_found | validation_error"
    )
    
    # Relationships
    user: Mapped[Optional["LoginUser"]] = relationship(back_populates="login_attempts")
    
    __table_args__ = (
        Index("idx_login_attempt_email_id", "email_id"),
        Index("idx_login_attempt_attempt_at", "attempt_at"),
        Index("idx_login_attempt_success", "success"),
        Index("idx_login_attempt_email_success_time", "email_id", "success", "attempt_at"),
    )
