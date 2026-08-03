"""
Main Router configuration.

Collects all module-level routers and combines them into a single
root router that is registered with the Dispatcher.
"""

from aiogram import Router

from bot.handlers.chat_member import router as chat_member_router
from bot.handlers.commands import router as commands_router
from bot.handlers.admin_cmd import router as admin_cmd_router
from bot.handlers.my_chat_member import router as my_chat_member_router
from bot.handlers.callbacks import router as callbacks_router

def setup_routers() -> Router:
    """
    Creates and configures the root router containing all handlers.
    """
    root_router = Router(name="root_router")
    
    # Register sub-routers
    # Note: Order matters if there are overlapping filters.
    # Typically, specific events like my_chat_member go first.
    root_router.include_router(my_chat_member_router)
    root_router.include_router(chat_member_router)
    root_router.include_router(admin_cmd_router)
    root_router.include_router(commands_router)
    root_router.include_router(callbacks_router)
    
    return root_router
