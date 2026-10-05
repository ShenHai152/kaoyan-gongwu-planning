"""Read admission lines for a school and program, newest year last."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.aliases import resolve_school_alias
from app.domains.kaoyan.models import AdmissionLine


def list_admission_lines(
    session: Session,
    *,
    school: str,
    program: str | None = None,
    degree_type: str | None = None,
) -> list[AdmissionLine]:
    statement = select(AdmissionLine).where(
        AdmissionLine.school_name == resolve_school_alias(school)
    )
    if program is not None:
        statement = statement.where(AdmissionLine.program_name == program)
    if degree_type is not None:
        statement = statement.where(AdmissionLine.degree_type == degree_type)
    statement = statement.order_by(AdmissionLine.year.asc(), AdmissionLine.id.asc())
    return list(session.scalars(statement).all())
