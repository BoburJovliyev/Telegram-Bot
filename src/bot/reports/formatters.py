"""
Text Formatters.

Creates beautifully formatted HTML strings for Telegram messages
using pre-calculated statistics.
"""

from bot.models.daily_stats import DailyStats


class ReportFormatter:
    """Formats statistics into Telegram-ready HTML messages."""

    @staticmethod
    def format_daily_stats(stats: DailyStats) -> str:
        """
        Format a DailyStats record into a readable message.
        """
        # Determine growth emoji
        if stats.net_growth > 0:
            growth_icon = "📈"
        elif stats.net_growth < 0:
            growth_icon = "📉"
        else:
            growth_icon = "➖"

        # Format the text using Telegram HTML
        return (
            f"📊 <b>Daily Report: {stats.stats_date.strftime('%B %d, %Y')}</b>\n\n"
            f"👥 <b>Active Members (EOD):</b> {stats.active_members_eod:,}\n"
            f"{growth_icon} <b>Net Growth:</b> {stats.net_growth:+,}\n\n"
            f"📥 <b>Total Joins:</b> {stats.joins_count:,}\n"
            f"┣ 🔗 Via Links: {stats.invite_link_joins:,}\n"
            f"┣ 👤 Public Joins: {stats.public_joins:,}\n"
            f"┣ 👑 Admin Added: {stats.admin_added_joins:,}\n"
            f"┗ 🔄 Rejoins: {stats.rejoin_count:,}\n\n"
            f"📤 <b>Total Leaves/Kicks:</b> {stats.leaves_count:,}\n"
            f"🛡 <b>Retention Rate:</b> {stats.retention_rate}%\n\n"
            f"🏆 <b>Unique Inviters Today:</b> {stats.unique_inviters:,}"
        )
