"""Database foundation shared by every domain.

The engine is created lazily so importing models never opens a connection.
Local development and tests may use SQLite; Postgres is used for integration
and production (ADR-0001).
"""

from __future__ import annotations

import os
from functools import cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DEFAULT_DATABASE_URL = "sqlite:///./exam.db"


def database_url() -> str:
    return os.environ.get("EXAM_DATABASE_URL", DEFAULT_DATABASE_URL)


@cache
def _engine_for(url: str) -> Engine:
    engine = create_engine(url, future=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_sqlite_fks(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine(url: str | None = None) -> Engine:
    return _engine_for(url or database_url())


def get_sessionmaker(url: str | None = None) -> sessionmaker:
    return sessionmaker(bind=get_engine(url), expire_on_commit=False)
