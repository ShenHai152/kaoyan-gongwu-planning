"""Authoritative state for the ai domain: AI session events."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AiSession(Base):
    """One report request = one session (GLOSSARY: AiSessionEvent owner)."""

    __tablename__ = "ai_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))
    style: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[str] = mapped_column(String(32))


class AiSessionEvent(Base):
    """Ordered record; enough to rebuild whatever reached the model.

    Recording rule (Model-visible = logged): the prompt and the structured
    input that reached the provider are stored verbatim in `payload`, so the
    request is reconstructable. Only non-personal data is ever written.
    """

    __tablename__ = "ai_session_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_session.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
