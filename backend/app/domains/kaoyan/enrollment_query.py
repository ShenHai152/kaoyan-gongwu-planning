"""Read enrollment plans for a school and program, oldest year first."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.aliases import resolve_school_alias
from app.domains.kaoyan.models import EnrollmentPlan


def list_enrollment_plans(
    session: Session,
    *,
    school: str,
    program: str | None = None,
    study_mode: str | None = None,
) -> list[EnrollmentPlan]:
    statement = select(EnrollmentPlan).where(
        EnrollmentPlan.school_name == resolve_school_alias(school)
    )
    if program is not None:
        statement = statement.where(EnrollmentPlan.program_name == program)
    if study_mode is not None:
        statement = statement.where(EnrollmentPlan.study_mode == study_mode)
    statement = statement.order_by(EnrollmentPlan.year.asc(), EnrollmentPlan.id.asc())
    return list(session.scalars(statement).all())
