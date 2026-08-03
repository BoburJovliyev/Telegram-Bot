"""
Inline keyboard builders.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.factory import DashboardCallback, ExportCallback, PaginationCallback


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Main admin dashboard navigation."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📊 Group Stats", 
        callback_data=DashboardCallback(action="stats")
    )
    builder.button(
        text="📥 Export Data", 
        callback_data=DashboardCallback(action="export")
    )
    builder.button(
        text="⚙️ Settings", 
        callback_data=DashboardCallback(action="settings")
    )
    
    # Adjust layout: two buttons on first row, one on second
    builder.adjust(2, 1)
    
    return builder.as_markup()


def get_export_options_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting export format."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📄 CSV File", 
        callback_data=ExportCallback(format="csv")
    )
    builder.button(
        text="📊 Excel (.xlsx)", 
        callback_data=ExportCallback(format="excel")
    )
    builder.button(
        text="🔙 Back to Dashboard", 
        callback_data=DashboardCallback(action="main")
    )
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_pagination_keyboard(
    list_type: str, 
    current_page: int, 
    total_pages: int
) -> InlineKeyboardMarkup:
    """Generic pagination keyboard generator."""
    builder = InlineKeyboardBuilder()
    
    # Only add Prev if not on first page
    if current_page > 1:
        builder.button(
            text="⬅️ Prev", 
            callback_data=PaginationCallback(list_type=list_type, page=current_page - 1)
        )
    else:
        builder.button(text=" ", callback_data="ignore")
        
    builder.button(
        text=f"{current_page} / {total_pages}", 
        callback_data="ignore"
    )
    
    # Only add Next if not on last page
    if current_page < total_pages:
        builder.button(
            text="Next ➡️", 
            callback_data=PaginationCallback(list_type=list_type, page=current_page + 1)
        )
    else:
        builder.button(text=" ", callback_data="ignore")
        
    builder.adjust(3)
    return builder.as_markup()
