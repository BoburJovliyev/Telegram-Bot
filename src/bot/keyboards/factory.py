"""
Callback data factories for inline keyboards.
"""

from aiogram.filters.callback_data import CallbackData


class DashboardCallback(CallbackData, prefix="dash"):
    """Navigation within the admin dashboard."""
    action: str  # main, settings, stats, export


class ExportCallback(CallbackData, prefix="export"):
    """Triggering file exports."""
    format: str  # csv, excel


class PaginationCallback(CallbackData, prefix="page"):
    """Navigating paginated lists."""
    list_type: str  # leaderboard, history
    page: int
