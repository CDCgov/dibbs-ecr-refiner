from fastapi import APIRouter

from .demo import router as demo_router
from .ecr import router as ecr_router
from .file_io import router as file_io_router

router = APIRouter(prefix="/v1")
router.include_router(demo_router)
router.include_router(ecr_router)
router.include_router(file_io_router)
