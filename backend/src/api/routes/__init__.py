from fastapi import APIRouter
from .auth import router as auth_router
from .projects import router as projects_router

router = APIRouter()

# Include other routers
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(projects_router, tags=["projects"]) 