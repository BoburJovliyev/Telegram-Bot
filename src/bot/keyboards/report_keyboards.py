"""
Keyboards for reports.
"""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_report_periods_keyboard() -> InlineKeyboardMarkup:
    """Returns an inline keyboard to select a report period."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Kunlik (1 kun)", callback_data="report_daily")
    builder.button(text="Haftalik (7 kun)", callback_data="report_weekly")
    builder.button(text="Oylik (30 kun)", callback_data="report_monthly")
    builder.button(text="Yillik (365 kun)", callback_data="report_yearly")
    
    # 2 buttons per row
    builder.adjust(2)
    return builder.as_markup()
