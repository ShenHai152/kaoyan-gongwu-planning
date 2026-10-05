"""Regression: a request session must return its connection to the pool.

Before the fix, `get_session` created a session but never closed it, so every
request held a connection until garbage collection. With a bounded pool that
exhausts quickly, later requests block and time out.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.db import Base
from app.main import app


def test_repeated_requests_do_not_exhaust_the_pool(monkeypatch):
    # A one-connection pool makes a leaked connection fail fast (0.2s) instead
    # of hanging for SQLAlchemy's 30s default.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=0.2,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr("app.api.kaoyan.get_sessionmaker", lambda: factory)

    client = TestClient(app)
    for _ in range(3):
        response = client.get("/api/kaoyan/provinces")
        assert response.status_code == 200, response.text
