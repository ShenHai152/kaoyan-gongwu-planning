"""Load normalized admission-line records into the database (idempotent)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import AdmissionLine
from app.domains.kaoyan.parsing import AdmissionLineRecord

_BUSINESS_KEY = (
    "school_name",
    "program_code",
    "program_name",
    "degree_type",
    "year",
    "department",
)


def _key(record: AdmissionLineRecord) -> tuple:
    return tuple(getattr(record, field) for field in _BUSINESS_KEY)


def load_admission_lines(session: Session, records: list[AdmissionLineRecord]) -> int:
    if not records:
        return 0

    existing = {
        tuple(getattr(row, field) for field in _BUSINESS_KEY)
        for row in session.scalars(select(AdmissionLine)).all()
    }

    seen = set(existing)
    inserted = 0
    for record in records:
        key = _key(record)
        if key in seen:
            continue
        seen.add(key)
        session.add(AdmissionLine(**vars(record)))
        inserted += 1

    session.commit()
    return inserted
