"""
Tests for the InviteTrackingService.
"""

import pytest
from unittest.mock import MagicMock

from aiogram.types import User

from bot.core.enums import JoinMethod
from bot.services.invite_service import InviteTrackingService

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

async def test_process_join_new_user(uow):
    """
    Test that a brand new user joining via public search
    is registered correctly and no inviters are credited.
    """
    service = InviteTrackingService(uow)
    
    # Mock Telegram User
    tg_user = User(
        id=999,
        is_bot=False,
        first_name="Test User",
        username="testuser"
    )
    
    await service.process_join(
        group_id=1,
        user=tg_user,
        join_method=JoinMethod.PUBLIC.value,
        idempotency_key="test_join_1"
    )
    
    # Assertions
    async with uow:
        # Check user was created
        db_user = await uow.users.get_by_id(999)
        assert db_user is not None
        assert db_user.first_name == "Test User"
        
        # Check member record was created
        member = await uow.members.get_member(1, 999)
        assert member is not None
        assert member.status == "active"
        assert member.join_method == "public"
        
        # Check attribution record
        record = await uow.invite_records.get_active_record(1, 999)
        assert record is not None
        assert record.inviter_id is None
        assert record.is_rejoin is False
