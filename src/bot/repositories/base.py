"""
Generic Base Repository.

Provides a standard set of CRUD operations for all SQLAlchemy models.
Designed for use with SQLAlchemy 2.0+ `select()` constructs.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.base import Base

# Type variable bound to our SQLAlchemy Declarative Base
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base class for all data repositories.
    
    Provides standard async CRUD operations. Specific repositories
    inherit from this and add domain-specific queries.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """
        Initialize the repository.
        
        Args:
            model: The SQLAlchemy model class.
            session: The active AsyncSession.
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> ModelType | None:
        """Retrieve a single record by its primary key."""
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        """Retrieve multiple records with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create and add a new record to the session.
        Note: You must commit the session for changes to persist.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: Any, **kwargs: Any) -> ModelType | None:
        """
        Update an existing record by ID.
        Returns the updated instance, or None if not found.
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> bool:
        """
        Delete a record by ID.
        Returns True if a record was deleted, False otherwise.
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
