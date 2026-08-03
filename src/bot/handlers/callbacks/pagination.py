"""
Pagination callback handlers.
"""

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.keyboards.factory import PaginationCallback

router = Router(name="pagination_cb_router")

@router.callback_query(PaginationCallback.filter())
async def handle_pagination(
    callback: CallbackQuery,
    callback_data: PaginationCallback,
) -> None:
    """Handle pagination clicks."""
    # This is a stub for now. The actual logic would re-query the page
    # and update the message with the new leaderboard segment.
    await callback.answer("Pagination is not fully implemented yet.")
