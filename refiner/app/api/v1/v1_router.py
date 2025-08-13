from fastapi import APIRouter

from .conditions import router as conditions_router
from .demo import router as demo_router

router = APIRouter(prefix="/v1")
router.include_router(demo_router)
router.include_router(conditions_router)
