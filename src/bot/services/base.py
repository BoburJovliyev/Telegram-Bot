"""
Base Service.
"""

import structlog

from bot.repositories.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


class BaseService:
    """
    Base class for all business logic services.
    
    Services are instantiated per-request (per-update) and receive
    the UnitOfWork as a dependency to ensure database operations
    can be coordinated transactionally.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """
        Initialize the service.
        
        Args:
            uow: The Unit of Work containing repository accessors.
        """
        self.uow = uow
        self.logger = logger.bind(service=self.__class__.__name__)
