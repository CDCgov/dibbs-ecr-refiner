from fastapi import APIRouter

from .demo import router as demo_router

router = APIRouter(prefix="/v1")
router.include_router(demo_router)
