from fastapi import APIRouter

from .configurations import router as configurations_router
from .demo import router as demo_router

router = APIRouter(prefix="/v1")
router.include_router(demo_router)
router.include_router(configurations_router)
