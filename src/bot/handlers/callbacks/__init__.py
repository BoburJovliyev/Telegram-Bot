"""
Callback query handlers router configuration.
"""

from aiogram import Router

from .dashboard import router as dashboard_router
from .export_cb import router as export_router
from .pagination import router as pagination_router

router = Router(name="callbacks_router")
router.include_router(dashboard_router)
router.include_router(export_router)
router.include_router(pagination_router)
