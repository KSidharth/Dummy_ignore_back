
"""
Common Pydantic schemas used across multiple API endpoints.
"""
from pydantic import BaseModel


class ErrorDto(BaseModel):
    """
    Standard error response schema.
    Used for all 4xx and 5xx error responses with generic messages per NFR-003.
    """
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials. Please check your email and password."
            }
        }


class MessageDto(BaseModel):
    """
    Generic message response schema.
    """
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }
