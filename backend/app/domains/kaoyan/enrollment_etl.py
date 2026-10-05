"""Load normalized EnrollmentPlan records into the database (idempotent)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.enrollment_parsing import EnrollmentPlanRecord
from app.domains.kaoyan.models import EnrollmentPlan

_BUSINESS_KEY = ("school_name", "program_name", "study_mode", "direction", "year")


def load_enrollment_plans(session: Session, records: list[EnrollmentPlanRecord]) -> int:
    if not records:
        return 0

    existing = {
        tuple(getattr(row, field) for field in _BUSINESS_KEY)
        for row in session.scalars(select(EnrollmentPlan)).all()
    }
    seen = set(existing)
    inserted = 0
    for record in records:
        key = tuple(getattr(record, field) for field in _BUSINESS_KEY)
        if key in seen:
            continue
        seen.add(key)
        session.add(EnrollmentPlan(**vars(record)))
        inserted += 1
    session.commit()
    return inserted
