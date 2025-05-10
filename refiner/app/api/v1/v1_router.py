from fastapi import APIRouter

from .demo import router as demo_router
from .ecr import router as ecr_router

router = APIRouter(prefix="/v1")
router.include_router(demo_router)
router.include_router(ecr_router)
