"""Load normalized 408 records into the database (idempotent)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.cs408_parsing import (
    Cs408ConflictRecord,
    Cs408SubjectChangeRecord,
    Cs408UnitRecord,
    Cs408YearLineRecord,
)
from app.domains.kaoyan.models import (
    Cs408Conflict,
    Cs408SubjectChange,
    Cs408Unit,
    Cs408YearLine,
)

_UNIT_KEY = ("school_name", "college", "direction")
_CONFLICT_KEY = ("school_name", "ordinal")
_CHANGE_KEY = ("school_name", "scope", "effective_year")


def _insert_new(
    session: Session,
    model: type[Any],
    records: Sequence[Any],
    key_fields: tuple[str, ...],
) -> int:
    """Insert records whose business key is not already present; return count."""
    seen = {
        tuple(getattr(row, field) for field in key_fields)
        for row in session.scalars(select(model)).all()
    }
    inserted = 0
    for record in records:
        key = tuple(getattr(record, field) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        session.add(model(**vars(record)))
        inserted += 1
    return inserted


def load_cs408_units(
    session: Session,
    units: list[Cs408UnitRecord],
    lines: list[Cs408YearLineRecord],
) -> int:
    """Insert units and their year lines; existing business keys are skipped.

    Year lines reference their owning unit by foreign key, so the unit is
    inserted (and flushed) first and then resolved by its business key.
    """
    if not units:
        return 0

    inserted = _insert_new(session, Cs408Unit, units, _UNIT_KEY)
    session.flush()

    unit_ids = {
        tuple(getattr(row, field) for field in _UNIT_KEY): row.id
        for row in session.scalars(select(Cs408Unit)).all()
    }
    seen_lines = {
        (row.unit_id, row.year)
        for row in session.scalars(select(Cs408YearLine)).all()
    }
    for line in lines:
        unit_id = unit_ids[tuple(getattr(line, field) for field in _UNIT_KEY)]
        key = (unit_id, line.year)
        if key in seen_lines:
            continue
        seen_lines.add(key)
        session.add(
            Cs408YearLine(
                unit_id=unit_id,
                year=line.year,
                line_raw=line.line_raw,
                line_value=line.line_value,
                source_file=line.source_file,
            )
        )
    session.commit()
    return inserted


def load_cs408_governance(
    session: Session,
    conflicts: list[Cs408ConflictRecord],
    changes: list[Cs408SubjectChangeRecord],
) -> int:
    """Insert conflicts and subject changes; existing business keys are skipped."""
    inserted = _insert_new(session, Cs408Conflict, conflicts, _CONFLICT_KEY)
    inserted += _insert_new(session, Cs408SubjectChange, changes, _CHANGE_KEY)
    session.commit()
    return inserted
