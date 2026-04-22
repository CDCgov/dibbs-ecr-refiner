from fastapi import APIRouter

from .activation import router as activation_router
from .base import router as base_router
from .codesets import router as codesets_router
from .custom_codes import router as custom_codes_router
from .exports import router as exports_router
from .locking import router as locking_router
from .sections import router as sections_router
from .testing import router as testing_router

router = APIRouter(prefix="/configurations")

router.include_router(base_router)
router.include_router(codesets_router)
router.include_router(custom_codes_router)
router.include_router(exports_router)
router.include_router(testing_router)
router.include_router(sections_router)
router.include_router(activation_router)
router.include_router(locking_router)
