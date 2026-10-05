"""Load NationalLine records into the database (idempotent)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import NationalLine
from app.domains.kaoyan.national_line_parsing import NationalLineRecord

_BUSINESS_KEY = ("year", "category_kind", "subject", "candidate_type")


def load_national_lines(session: Session, records: list[NationalLineRecord]) -> int:
    if not records:
        return 0
    existing = {
        tuple(getattr(row, field) for field in _BUSINESS_KEY)
        for row in session.scalars(select(NationalLine)).all()
    }
    seen = set(existing)
    inserted = 0
    for record in records:
        key = tuple(getattr(record, field) for field in _BUSINESS_KEY)
        if key in seen:
            continue
        seen.add(key)
        session.add(NationalLine(**vars(record)))
        inserted += 1
    session.commit()
    return inserted
