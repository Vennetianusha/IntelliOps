from fastapi import APIRouter
from app.api.v1.endpoints import issues

api_router = APIRouter()

# Include Issues CRUD endpoints under /issues
api_router.include_router(issues.router, prefix="/issues", tags=["Issues"])


@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify backend service operational status.
    """
    return {
        "status": "healthy",
        "service": "IntelliOps Backend API",
        "version": "0.1.0",
    }
