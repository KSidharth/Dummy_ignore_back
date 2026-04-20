
"""
FastAPI application entry point.
Initializes the app, configures CORS, and registers all API routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_v1_router


# Initialize FastAPI application
app = FastAPI(
    title="Simple Login System API",
    description="Backend API for simple login authentication system with PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware per settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 router
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    return {"status": "healthy", "service": "login-system-backend"}
