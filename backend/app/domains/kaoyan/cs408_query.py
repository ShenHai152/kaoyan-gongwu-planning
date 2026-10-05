"""Read 408-track data (units, year lines, subject changes, conflicts).

School names resolve through the same alias map as the wide-caliber tables so
either spelling hits; the 408 records themselves stay independent.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.aliases import resolve_school_alias
from app.domains.kaoyan.models import (
    Cs408Conflict,
    Cs408SubjectChange,
    Cs408Unit,
    Cs408YearLine,
)


def list_cs408_units(
    session: Session,
    *,
    school: str,
    subject_class: str | None = None,
) -> list[Cs408Unit]:
    statement = select(Cs408Unit).where(
        Cs408Unit.school_name == resolve_school_alias(school)
    )
    if subject_class is not None:
        statement = statement.where(Cs408Unit.subject_class == subject_class)
    statement = statement.order_by(Cs408Unit.college.asc(), Cs408Unit.id.asc())
    return list(session.scalars(statement).all())


def list_cs408_year_lines(
    session: Session,
    *,
    school: str,
    year: int | None = None,
) -> list[dict]:
    """Year lines joined with their owning unit's identity for display."""
    statement = (
        select(
            Cs408Unit.school_name,
            Cs408Unit.college,
            Cs408Unit.direction,
            Cs408YearLine.year,
            Cs408YearLine.line_raw,
            Cs408YearLine.line_value,
            Cs408YearLine.source_file,
        )
        .join(Cs408Unit, Cs408YearLine.unit_id == Cs408Unit.id)
        .where(Cs408Unit.school_name == resolve_school_alias(school))
    )
    if year is not None:
        statement = statement.where(Cs408YearLine.year == year)
    statement = statement.order_by(
        Cs408Unit.college.asc(),
        Cs408Unit.direction.asc(),
        Cs408YearLine.year.asc(),
    )
    return [dict(row._mapping) for row in session.execute(statement).all()]


def list_cs408_subject_changes(
    session: Session, *, school: str
) -> list[Cs408SubjectChange]:
    statement = (
        select(Cs408SubjectChange)
        .where(Cs408SubjectChange.school_name == resolve_school_alias(school))
        .order_by(Cs408SubjectChange.id.asc())
    )
    return list(session.scalars(statement).all())


def list_cs408_conflicts(session: Session, *, school: str) -> list[Cs408Conflict]:
    statement = (
        select(Cs408Conflict)
        .where(Cs408Conflict.school_name == resolve_school_alias(school))
        .order_by(Cs408Conflict.ordinal.asc())
    )
    return list(session.scalars(statement).all())
