from fastapi import APIRouter

from .conditions import router as conditions_router
from .configurations.router import router as configurations_router
from .demo import router as demo_router
from .events import router as events_router
from .info import router as info_router
from .releases import router as releases_router

router = APIRouter(prefix="/v1")
router.include_router(conditions_router)
router.include_router(configurations_router)
router.include_router(demo_router)
router.include_router(events_router)
router.include_router(info_router)
router.include_router(releases_router)
