"""Read national lines for a year through a subject or category."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import NationalLine


def list_national_lines(
    session: Session,
    *,
    year: int | None = None,
    subject: str | None = None,
    category_kind: str | None = None,
) -> list[NationalLine]:
    statement = select(NationalLine)
    if year is not None:
        statement = statement.where(NationalLine.year == year)
    if subject is not None:
        statement = statement.where(NationalLine.subject == subject)
    if category_kind is not None:
        statement = statement.where(NationalLine.category_kind == category_kind)
    statement = statement.order_by(
        NationalLine.year.asc(),
        NationalLine.subject.asc(),
        NationalLine.candidate_type.asc(),
    )
    return list(session.scalars(statement).all())
