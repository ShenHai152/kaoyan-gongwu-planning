"""FastAPI application assembly."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.ai import models as _ai_models  # noqa: F401  (register tables)
from app.api.kaoyan import get_session
from app.api.kaoyan import router as kaoyan_router
from app.config import load_env
from app.db import Base, get_engine

# Load .env before anything reads configuration (DB url, LLM keys).
load_env()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(get_engine())
    yield


app = FastAPI(title="考研择校 + 考公路径规划", version="0.1.0", lifespan=lifespan)
app.include_router(kaoyan_router)

__all__ = ["app", "get_session"]
