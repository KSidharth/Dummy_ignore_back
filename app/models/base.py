
"""
SQLAlchemy declarative base for all ORM models.
All database models inherit from Base.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
