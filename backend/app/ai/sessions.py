"""Record AI session events so any report is reconstructable (recording rule)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.models import AiSession, AiSessionEvent


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def start_session(session: Session, *, kind: str, provider: str, style: str) -> AiSession:
    record = AiSession(kind=kind, provider=provider, style=style, created_at=_now())
    session.add(record)
    session.flush()
    return record


def append_event(
    session: Session, *, session_id: int, event_type: str, payload: dict
) -> AiSessionEvent:
    next_ordinal = (
        session.scalar(
            select(AiSessionEvent.ordinal)
            .where(AiSessionEvent.session_id == session_id)
            .order_by(AiSessionEvent.ordinal.desc())
            .limit(1)
        )
        or 0
    ) + 1
    event = AiSessionEvent(
        session_id=session_id,
        ordinal=next_ordinal,
        event_type=event_type,
        payload=json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )
    session.add(event)
    session.flush()
    return event


def list_events(session: Session, session_id: int) -> list[AiSessionEvent]:
    statement = (
        select(AiSessionEvent)
        .where(AiSessionEvent.session_id == session_id)
        .order_by(AiSessionEvent.ordinal.asc())
    )
    return list(session.scalars(statement).all())
