from typing import TYPE_CHECKING, Any
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from kts_backend.store.database.sqlalchemy_base import db

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: AsyncSession | None = None
        self._db: declarative_base | None = None
        self.session: AsyncSession | None = None

    async def connect(self, *_: Any, **__: Any) -> None:
        self._db = db
        self._engine = create_async_engine()
        self.session = sessionmaker()

    async def disconnect(self, *_: list, **__: dict) -> None:
        raise NotImplemented
